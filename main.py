from context import get_article, get_context, relate_article_to_context

context = get_context()
article_url = "https://substack.com/inbox/post/186080081"

article_content = get_article(article_url)
analysis = relate_article_to_context(article_content, context)
print(analysis)

