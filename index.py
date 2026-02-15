from flask import Flask, render_template_string, request, jsonify
from build_list import build_list
from substack import get_posts

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Newsletter digest</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      line-height: 1.5;
      max-width: 720px;
      margin: 0 auto;
      padding: 2rem 1rem;
      color: #1a1a1a;
      background: #fafafa;
    }
    h1.page-title {
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 1.5rem;
      color: #333;
    }
    article {
      background: #fff;
      border-radius: 8px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    article h1 {
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0 0 0.25rem 0;
      line-height: 1.3;
    }
    article h1 a {
      color: #0066cc;
      text-decoration: none;
    }
    article h1 a:hover {
      text-decoration: underline;
    }
    .post-date {
      font-size: 0.8125rem;
      color: #666;
      margin-bottom: 0.75rem;
    }
    .post-date a {
      color: #666;
      text-decoration: none;
    }
    .post-date a:hover {
      text-decoration: underline;
    }
    .short-summary {
      font-size: 1rem;
      margin-bottom: 0.5rem;
      color: #333;
    }
    .full-summary {
      font-size: 0.9375rem;
      color: #555;
      margin: 0;
    }
  </style>
</head>
<body>
  <h1 class="page-title">Newsletter digest</h1>
  {% for item in items %}
  <article>
    <h1><a href="{{ item.url }}" target="_blank" rel="noopener">{{ item.title }}</a></h1>
    <p class="post-date">{{ item.post_date }} · <a href="{{ item.url }}" target="_blank" rel="noopener">{{ item.url }}</a></p>
    <p class="short-summary">{{ item.summary.get('short', '') }}</p>
    <p class="full-summary">{{ item.summary.get('full', '') }}</p>
  </article>
  {% endfor %}
</body>
</html>
"""


@app.route("/")
def index():
    items = build_list()
    for item in items:
        item["summary"] = item.get("summary") or {}
    return render_template_string(HTML_TEMPLATE, items=items)



@app.route("/api/posts/", methods=["POST"])
def api_posts():
    # Caller POSTs newsletter_url and optionally limit (form data).
    newsletter_url = request.form.get("newsletter_url") or "https://illai.substack.com/"
    try:
        limit = int(request.form.get("limit") or 10)
    except (TypeError, ValueError):
        limit = 10
    return get_posts(newsletter_url, limit)
    


if __name__ == "__main__":
    app.run(debug=True,port=5001)