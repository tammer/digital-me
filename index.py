from flask import Flask, render_template_string, request, jsonify
from build_list import build_list
from substack import get_posts, get_recommendations
from get_title import get_title

app = Flask(__name__)
# app.config["JSON_AS_ASCII"] = False  # output Unicode (e.g. ®) instead of \u00ae

ALLOWED_ORIGINS = {"http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"}

@app.after_request
def cors_headers(response):
    origin = request.headers.get("Origin")
    print(origin)
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
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