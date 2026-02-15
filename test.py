from substack import get_posts
import json 

posts = get_posts("https://illai.substack.com/")
print(json.dumps(posts, indent=4))