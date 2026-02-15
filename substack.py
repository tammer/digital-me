from substack_api import Newsletter
from htmlstripper import _strip_html
from summarize_article import summarize_article

def get_posts(newsletter_url: str, limit: int = 10) -> list[dict]:
    newsletter = Newsletter(newsletter_url)
    posts = newsletter.get_posts(limit=limit)
    rv = []

    for post in posts:
        content = _strip_html(post.get_content())
        rv.append({
            "id": post.get_metadata().get("id"),
            "title": post.get_metadata().get("title"),
            "url": post.get_metadata().get("canonical_url"),
            "post_date": post.get_metadata().get("post_date"),
            "content": content,
            "summary": summarize_article(post.get_metadata().get("id"), content),
        })
    return rv