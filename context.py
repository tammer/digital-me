import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import HTTPRedirectHandler, Request, build_opener
import json
from groq import Groq

from htmlstripper import _strip_html
from summarize_article import summarize_article

REDIRECT_CODES = (301, 302, 303, 307, 308)


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


GROQ_MODEL = "llama-3.3-70b-versatile"


def relate_article_to_context(article_text: str, context: dict, *, model: str = GROQ_MODEL) -> str:
    """Use a Groq model to determine if any aspects of the article relate to the context.
    context is a dict of name -> text (e.g. from get_context()).
    Returns the model's analysis as a string.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")

    context_blob = "\n\n".join(f"## {name}\n{text}" for name, text in context.items())
    prompt = f"""You are given:
1) An article (below under ARTICLE).
2) Context: several named text sources (below under CONTEXT).

Your task: What links can you find between the article and the context. Make share the links are solid. it is ok to conclude there are no links.
be succinct and to the point.
decide which is the best link andd why.
Then write a one or two sentence intro to the article noting the best link.
Finally, on a scale of 1 to 10, how likely is it that the article is relevant to the context?

---
CONTEXT:
{context_blob}

---
ARTICLE:
{article_text}
"""

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You analyze whether an article relates to given context. Be precise and concise."},
            {"role": "user", "content": prompt},
        ],
        model=model,
        temperature=0.2,
        max_tokens=1024,
    )
    return completion.choices[0].message.content or ""
