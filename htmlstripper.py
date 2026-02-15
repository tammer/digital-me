from html.parser import HTMLParser

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
