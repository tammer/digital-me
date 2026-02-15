from substack_api import Newsletter
from htmlstripper import _strip_html
from summarize_article import summarize_article

def get_posts(newsletter_url: str, cut_off: str | None = None) -> list[dict]:
    """cut_off must be of the form "yyyy-mm-dd". Posts with post_date[:10] < cut_off are excluded. If cut_off is None, all posts are included."""
    newsletter = Newsletter(newsletter_url)
    posts = newsletter.get_posts(limit=10)
    rv = []

    for post in posts:
        post_date = post.get_metadata().get("post_date")
        if cut_off is not None and (not post_date or len(post_date) < 10 or post_date[:10] < cut_off):
            continue
        post_date = post_date[:10]
        content = _strip_html(post.get_content())
        rv.append({
            "id": post.get_metadata().get("id"),
            "title": post.get_metadata().get("title"),
            "url": post.get_metadata().get("canonical_url"),
            "post_date": post_date,
            "content": content,
            "summary": summarize_article(post.get_metadata().get("id"), content),
        })
    return rv