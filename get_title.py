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


def get_title(url: str, redirect_limit: int = 10) -> str:
    """Fetch the URL and return the content of the <title> element, or "" if none."""
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
    match = re.search(r"<title[^>]*>([\s\S]*?)</title>", raw, re.I)
    if match:
        title = match.group(1).strip()
        return html.unescape(title)
    return ""
