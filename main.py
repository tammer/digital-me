import json

from context import get_context, get_article

context = get_context()

article = "https://substack.com/inbox/post/186080081"

article_content = get_article(article)

print(article_content)