import re
import html
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import HTTPRedirectHandler, Request, build_opener

REDIRECT_CODES = (301, 302, 303, 307, 308)


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
    """Fetch the URL and return a dict with 'title' and 'subtitle' from the page."""
    # if url is missing the protocol, add https://
    if not url.startswith("http"):
        url = "https://" + url
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
                return get_title(next_url, redirect_limit - 1)
        raise
    raw = resp.read().decode(errors="replace")
    title_match = re.search(r"<title[^>]*>([\s\S]*?)</title>", raw, re.I)
    title = html.unescape(title_match.group(1).strip()) if title_match else ""
    subtitle = _get_subtitle(raw)
    return {"title": title, "subtitle": subtitle}
