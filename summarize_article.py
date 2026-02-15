import os
import json
from pathlib import Path

from groq import Groq

GROQ_MODEL = "llama-3.3-70b-versatile"

_CACHE_DIR = Path(__file__).parent / "cache"


def summarize_article(id: str, article_text: str, model: str = GROQ_MODEL) -> str:
    _CACHE_DIR.mkdir(exist_ok=True)
    cache_path = _CACHE_DIR / f"{id}.txt"
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    print(f"Using AI for {id}")
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    client = Groq(api_key=api_key)
    system_prompt = """You summarize an article in two ways: short and full.
    The short summary should be 50 words or less.
    The full summary should around 200 words.
    return a json object with the short and full summaries.
    return pure json, no markdown or other formatting.
    """
    completion = client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": article_text}],
        model=model,
    )
    result = json.loads(completion.choices[0].message.content or "{}")
    cache_path.write_text(json.dumps(result))
    return result
