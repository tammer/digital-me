from context import get_article, get_context, relate_article_to_context

article_url = input("Article URL: ").strip()
if not article_url:
    print("No URL provided.")
    exit(1)
context = get_context()
article_content = get_article(article_url)
analysis = relate_article_to_context(article_content, context)
print(analysis)

