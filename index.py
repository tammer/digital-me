from flask import Flask, render_template_string, request, jsonify
from build_list import build_list
from substack import get_posts

app = Flask(__name__)

ALLOWED_ORIGINS = {"http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"}

@app.after_request
def cors_headers(response):
    origin = request.headers.get("Origin")
    print(origin)
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
    return response


@app.route("/api/posts/", methods=["POST"])
def api_posts():
    # Caller POSTs newsletter_url and optionally limit (form data).
    newsletter_url = request.form.get("newsletter_url") or "https://illai.substack.com/"
    return get_posts(newsletter_url)
    


if __name__ == "__main__":
    app.run(debug=True,port=5001)