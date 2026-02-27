import os
import hashlib
from urllib.parse import urlparse, unquote

import jwt
from jwt import PyJWKClient
from dotenv import load_dotenv
from flask import Flask, render_template_string, request, jsonify
from substack_api import Newsletter
from supabase import create_client

from build_list import build_list
from substack import get_posts, get_posts_list, get_recommendations
from get_title import get_title
from context import get_article, summarize_article

load_dotenv()

app = Flask(__name__)
_supabase_client = None
_jwks_client = None


def _get_jwks_client() -> PyJWKClient:
    """Return cached JWKS client for Supabase Auth (ES256 public keys)."""
    global _jwks_client
    if _jwks_client is None:
        url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        if not url:
            raise RuntimeError("SUPABASE_URL must be set")
        _jwks_client = PyJWKClient(f"{url}/auth/v1/.well-known/jwks.json")
    return _jwks_client


def _get_supabase():
    """Return Supabase client (cached). Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in env."""
    global _supabase_client
    if _supabase_client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        _supabase_client = create_client(url, key)
    return _supabase_client


def _get_user_id_from_request() -> str | None:
    """Extract and verify Bearer JWT (ES256 via JWKS); return sub (user_id) or None."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    try:
        jwks = _get_jwks_client()
        signing_key = jwks.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
            options={"verify_aud": True},
        )
        return payload.get("sub")
    except Exception:
        return None


# app.config["JSON_AS_ASCII"] = False  # output Unicode (e.g. ®) instead of \u00ae
ALLOWED_ORIGINS = {"http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5174"}

@app.after_request
def cors_headers(response):
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/posts/", methods=["POST"])
def api_posts():
    # Caller POSTs newsletter_url and optionally limit (form data).
    newsletter_url = request.form.get("newsletter_url") or "https://illai.substack.com/"
    return get_posts(newsletter_url)


@app.route("/api/recommendations/", methods=["POST"])
def api_recommendations():
    newsletter_url = request.form.get("newsletter_url") or "https://illai.substack.com/"
    return get_recommendations(newsletter_url)


def _normalize_newsletter_url(url: str) -> str | None:
    """Return newsletter root URL (scheme + netloc) or None if invalid scheme."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


@app.route("/newsletters/subscribe-by-url", methods=["POST", "OPTIONS"])
def subscribe_by_url():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"success": False, "message": "url is required"}), 400
    normalized = _normalize_newsletter_url(url)
    if normalized is None:
        return jsonify({"success": False, "message": "Invalid URL"}), 400
    try:
        newsletter = Newsletter(normalized)
        newsletter.get_posts(limit=1)
    except Exception:
        return jsonify({"success": False, "message": "Not a valid Substack newsletter"}), 400
    try:
        info = get_title(normalized)
        title = info.get("title") or ""
        subtitle = info.get("subtitle")
    except Exception:
        title = ""
        subtitle = None
    user_id = _get_user_id_from_request()
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    try:
        supabase = _get_supabase()
    except RuntimeError:
        return jsonify({"success": False, "message": "Failed to save subscription. Please try again."}), 500
    try:
        existing = (
            supabase.table("newsletter_urls")
            .select("id")
            .eq("user_id", user_id)
            .eq("url", normalized)
            .execute()
        )
    except Exception:
        return jsonify({"success": False, "message": "Failed to save subscription. Please try again."}), 500
    if existing.data:
        message = "You're already subscribed to this newsletter."
    else:
        try:
            supabase.table("newsletter_urls").insert({"user_id": user_id, "url": normalized}).execute()
        except Exception:
            return jsonify({"success": False, "message": "Failed to save subscription. Please try again."}), 500
        message = f"Added: {title}" if title else "Added."
    payload = {"success": True, "message": message, "title": title}
    if subtitle is not None:
        payload["subtitle"] = subtitle
    return jsonify(payload)


@app.route("/newsletters", methods=["GET"])
def get_newsletters():
    """Return the authenticated user's newsletters: { newsletters: [ { title, author, url [, id] } ] }."""
    user_id = _get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        supabase = _get_supabase()
    except RuntimeError:
        return jsonify({"error": "Service unavailable"}), 500
    try:
        rows = (
            supabase.table("newsletter_urls")
            .select("id, url")
            .eq("user_id", user_id)
            .execute()
        )
    except Exception:
        return jsonify({"error": "Failed to load newsletters"}), 500
    newsletters = []
    for row in (rows.data or []):
        url = row.get("url") or ""
        item = {"url": url, "title": "", "author": ""}
        if row.get("id") is not None:
            item["id"] = row["id"]
        try:
            info = get_title(url)
            item["title"] = info.get("title") or ""
            item["author"] = info.get("author") or ""
        except Exception:
            pass
        newsletters.append(item)
    return jsonify({"newsletters": newsletters})


@app.route("/posts", methods=["GET"])
def get_posts_route():
    """Return posts for a newsletter: { posts: [ { title, date, read [, id, url] } ] }. Requires Bearer auth."""
    user_id = _get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    newsletter_url = (request.args.get("newsletter_url") or "").strip()
    if not newsletter_url:
        return jsonify({"error": "newsletter_url is required"}), 400
    newsletter_url = unquote(newsletter_url)
    normalized = _normalize_newsletter_url(newsletter_url)
    if normalized is None:
        return jsonify({"error": "Invalid newsletter URL"}), 400
    read_post_ids = set()
    try:
        supabase = _get_supabase()
        rows = (
            supabase.table("read_posts")
            .select("post_id")
            .eq("user_id", user_id)
            .execute()
        )
        for row in (rows.data or []):
            pid = row.get("post_id")
            if pid is not None:
                read_post_ids.add(pid)
    except Exception:
        pass
    try:
        raw_posts = get_posts_list(normalized)
    except Exception:
        return jsonify({"error": "Failed to fetch posts"}), 500
    posts = []
    for p in raw_posts:
        post_id = p.get("id")
        item = {
            "title": p.get("title") or "",
            "date": p.get("post_date") or "",
            "read": post_id in read_post_ids if post_id is not None else False,
        }
        if post_id is not None:
            item["id"] = post_id
        if p.get("url") is not None:
            item["url"] = p["url"]
        posts.append(item)
    return jsonify({"posts": posts})


@app.route("/posts/summary", methods=["POST"])
def get_post_summary():
    """Return summary for a single post URL.

    Requires query param post_url and Bearer auth.
    Response: { id, url, article_title, post_date, short_summary, full_summary }
    """
    user_id = _get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    raw_url = (request.args.get("post_url") or body.get("post_url") or "").strip()
    if not raw_url:
        return jsonify({"error": "post_url is required"}), 400
    post_url = unquote(raw_url)
    if not post_url.startswith(("http://", "https://")):
        post_url = "https://" + post_url
    try:
        article_text = get_article(post_url)
    except Exception:
        return jsonify({"error": "Failed to fetch article"}), 500
    cache_id = hashlib.sha1(post_url.encode("utf-8")).hexdigest()[:16]
    try:
        summary = summarize_article(cache_id, article_text)
    except Exception:
        return jsonify({"error": "Failed to summarize article"}), 500
    if isinstance(summary, dict):
        short_summary = (
            summary.get("short_summary")
            or summary.get("short")
            or summary.get("shortSummary")
            or ""
        )
        full_summary = (
            summary.get("full_summary")
            or summary.get("full")
            or summary.get("fullSummary")
            or ""
        )
    else:
        short_summary = ""
        full_summary = str(summary)
    try:
        title_info = get_title(post_url)
        article_title = title_info.get("title") or ""
    except Exception:
        article_title = ""
    post_date = ""
    return jsonify(
        {
            "id": cache_id,
            "url": post_url,
            "article_title": article_title,
            "post_date": post_date,
            "short_summary": short_summary,
            "full_summary": full_summary,
        }
    )


@app.route("/api/get_title/", methods=["POST"])
def api_get_title():
    url = request.form.get("url")
    if not url or not url.strip():
        return jsonify({"error": "url is required"}), 400
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return jsonify({"error": "url must be http or https"}), 400
    try:
        result = get_title(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Failed to fetch or parse URL", "detail": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True,port=5001)