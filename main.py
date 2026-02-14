import sys

from context import get_article, get_context, relate_article_to_context

if len(sys.argv) < 2:
    print("Usage: python main.py <article_url>", file=sys.stderr)
    sys.exit(1)

article_url = sys.argv[1]
context = get_context()
article_content = get_article(article_url)
analysis = relate_article_to_context(article_content, context)
print(analysis)

