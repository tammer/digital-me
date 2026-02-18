
from substack import get_recommendations
import json

print(json.dumps(get_recommendations("https://illai.substack.com/"), indent=4, ensure_ascii=False))

