from build_list import build_list
import json



list = build_list()
print(json.dumps(list, indent=4))
