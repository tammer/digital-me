from substack_api import Newsletter
from context import get_article, summarize_article
from datetime import datetime, timedelta

def build_list(cut_off=None):
    if cut_off is None:
        cut_off = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    # open file newsletters.txt and read each line as a newsletter URL
    with open("newsletters.txt", "r") as file:
        newsletters = [line.strip() for line in file.readlines()]
    list = _build_list(newsletters, cut_off)
    list.sort(key=lambda x: x["post_date"], reverse=True)
    return list

def _build_list(newsletters, cut_off):
    # returns a list of dicts where each dict contains the title, url, and post_date
    list = []
    for newsletter_url in newsletters:
        newsletter = Newsletter(newsletter_url)
        recent_posts = newsletter.get_posts(limit=7)
        for post in recent_posts:
            metadata = post.get_metadata()
            post_date = metadata.get("post_date")[:10]
            if post_date < cut_off:
                continue
            summary = summarize_article(metadata.get("id"), post.url)
            list.append({
                "id": metadata.get("id"),
                "title": metadata.get("title"),
                "url": post.url,
                "post_date": post_date,
                "summary": summary
            })
    return list
