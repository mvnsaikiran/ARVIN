"""
LLM via Groq API — free tier, llama-3.3-70b-versatile.
Set GROQ_API_KEY in your .env file or as an environment variable.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
TIMEOUT    = 60


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
    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            json=payload,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"**LLM error:** {e}"
