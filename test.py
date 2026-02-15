from substack_api import Newsletter
from context import get_article, get_context, relate_article_to_context, summarize_article
import json
# Initialize a newsletter by its URL
# newsletter = Newsletter("https://illai.substack.com/")
# newsletter = Newsletter("https://seanellis.substack.com/")

newsletters = [
    "https://illai.substack.com/",
    "https://seanellis.substack.com/",
    "https://www.newcomer.co/",
    "https://nextbigteng.substack.com/",
    "https://www.thevccorner.com/"
]

cut_off = "2026-02-05"


def build_list(newsletters, cut_off):
    # returns a list of dicts where each dict contains the title, url, and post_date
    list = []
    for newsletter_url in newsletters:
        newsletter = Newsletter(newsletter_url)
        recent_posts = newsletter.get_posts(limit=5)
        for post in recent_posts[:4]:
            metadata = post.get_metadata()
            post_date = metadata.get("post_date")[:10]
            if post_date < cut_off:
                continue
            list.append({
                "id": metadata.get("id"),
                "title": metadata.get("title"),
                "url": post.url,
                "post_date": post_date
            })
    return list

list = build_list(newsletters[:1], cut_off)
print(json.dumps(list, indent=4))

        # article_content = get_article(post.url)
        # summary = summarize_article(article_content)
        # print(json.dumps(summary, indent=4))


