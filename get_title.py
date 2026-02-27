import hashlib
import html
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import HTTPRedirectHandler, Request, build_opener

REDIRECT_CODES = (301, 302, 303, 307, 308)
TITLE_CACHE_DIR = Path(__file__).parent / "title_cache"
CACHE_MAX_AGE_SECONDS = 24 * 60 * 60  # 24 hours


class NoRedirectHandler(HTTPRedirectHandler):
    """Handler that does not follow redirects; the caller will recurse."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _get_subtitle(html_str: str) -> str | None:
    """Return the text of <p class="publication-tagline with-cover ..."> if present, else None."""
    # Match <p> with class containing both publication-tagline and with-cover (order may vary)
    match = re.search(
        r'<p\s[^>]*class="[^"]*(?:publication-tagline[^"]*with-cover|with-cover[^"]*publication-tagline)[^"]*"[^>]*>([\s\S]*?)</p>',
        html_str,
        re.I,
    )
    if match:
        return html.unescape(match.group(1).strip()) or None
    return None


def get_title(url: str, redirect_limit: int = 10) -> dict:
    """Fetch the URL and return a dict with 'title', 'author' (if present), and 'subtitle' from the page.
    Results are cached on disk; cache is refreshed if older than 24 hours.
    """
    # if url is missing the protocol, add https://
    if not url.startswith("http"):
        url = "https://" + url

    cache_key = hashlib.sha256(url.encode()).hexdigest()
    cache_path = TITLE_CACHE_DIR / f"{cache_key}.json"

    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age < CACHE_MAX_AGE_SECONDS:
            return json.loads(cache_path.read_text())

    result = _fetch_title(url, redirect_limit)
    TITLE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(result))
    return result


def _fetch_title(url: str, redirect_limit: int) -> dict:
    if redirect_limit <= 0:
        raise ValueError("Too many redirects")
    opener = build_opener(NoRedirectHandler())
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; get_title/1.0)"})
    try:
        resp = opener.open(req)
    except HTTPError as e:
        if e.code in REDIRECT_CODES:
            location = e.headers.get("Location")
            if location:
                next_url = urljoin(url, location)
                return _fetch_title(next_url, redirect_limit - 1)
        raise
    raw = resp.read().decode(errors="replace")
    title_match = re.search(r"<title[^>]*>([\s\S]*?)</title>", raw, re.I)
    raw_title = html.unescape(title_match.group(1).strip()) if title_match else ""
    parts = [p.strip() for p in raw_title.split("|")]
    title = parts[0] if parts else ""
    author = parts[1] if len(parts) >= 3 else None
    subtitle = _get_subtitle(raw)
    return {"title": title, "author": author, "subtitle": subtitle}
