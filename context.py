from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import HTTPRedirectHandler, Request, build_opener

REDIRECT_CODES = (301, 302, 303, 307, 308)

# Tags to strip entirely (including their content)
STRIP_WITH_CONTENT = frozenset(
    {"script", "style", "head", "noscript", "iframe", "object", "svg", "template"}
)
# Void/self-closing tags to strip (no content)
STRIP_VOID = frozenset({"meta", "link", "embed", "base", "img", "input"})


class _HTMLStripper(HTMLParser):
    """Strip script, style, meta, and other non-content tags; output plain text."""

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self._result = []
        self._block_tags = frozenset(
            {"p", "div", "li", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6", "br", "hr"}
        )

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in STRIP_WITH_CONTENT:
            self._skip_depth += 1
        elif tag in self._block_tags and self._skip_depth == 0 and self._result and self._result[-1] not in (" ", "\n"):
            self._result.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in STRIP_WITH_CONTENT:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in self._block_tags and self._skip_depth == 0:
            self._result.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._result.append(data)

    def get_text(self):
        text = "".join(self._result)
        # collapse runs of whitespace and strip
        return "\n".join(line.strip() for line in text.splitlines() if line.strip()).strip()


def _strip_html(html: str) -> str:
    """Remove script, style, meta, and other junk; return plain text."""
    stripper = _HTMLStripper()
    stripper.feed(html)
    return stripper.get_text()


class NoRedirectHandler(HTTPRedirectHandler):
    """Handler that does not follow redirects; the caller will recurse."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def get_article(url, redirect_limit=10):
    """Fetch the contents at url. If the server responds with a redirect, follow it recursively."""
    if redirect_limit <= 0:
        raise ValueError("Too many redirects")
    opener = build_opener(NoRedirectHandler())
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; get_article/1.0)"})
    try:
        resp = opener.open(req)
    except HTTPError as e:
        if e.code in REDIRECT_CODES:
            location = e.headers.get("Location")
            if location:
                next_url = urljoin(url, location)
                return get_article(next_url, redirect_limit - 1)
        raise
    raw = resp.read().decode(errors="replace")
    if "<" in raw and ">" in raw:
        return _strip_html(raw)
    return raw


def get_context():
    me_dir = Path(__file__).parent / "me"
    content_by_name = {}
    for path in me_dir.iterdir():
        if path.is_file():
            key = path.stem  # root name (filename without extension)
            content_by_name[key] = path.read_text()
    return content_by_name
