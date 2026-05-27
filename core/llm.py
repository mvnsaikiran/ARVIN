"""
LLM via Groq API — free tier, llama-3.3-70b-versatile.
Set GROQ_API_KEY in your .env file or as an environment variable.
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
TIMEOUT    = 60
_MAX_RETRIES = 4


def ask(system_prompt: str, user_message: str) -> str:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return "**Error:** GROQ_API_KEY not set. Add it to your .env file or set it as an environment variable."

    payload = {
        "model":       GROQ_MODEL,
        "temperature": 0.1,
        "max_tokens":  1024,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }

    delay = 5
    for attempt in range(_MAX_RETRIES):
        try:
            resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=TIMEOUT)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("retry-after", delay))
                wait = max(retry_after, delay)
                print(f"  [rate limit] waiting {wait}s before retry {attempt+1}/{_MAX_RETRIES}...")
                time.sleep(wait)
                delay *= 2
                continue
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.HTTPError:
            raise
        except Exception as e:
            return f"**LLM error:** {e}"

    return "**LLM error:** Groq rate limit exceeded after retries. Wait a minute and try again."
