"""
Local LLM via Ollama — zero API cost, runs entirely on your machine.

Setup (one-time):
  1. Download Ollama from https://ollama.com
  2. Run: ollama pull llama3.1
  3. Ollama runs as a local server on http://localhost:11434
"""

import requests

OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.1"   # change to llama3.2, mistral, etc. as needed
TIMEOUT      = 120


def ask(system_prompt: str, user_message: str) -> str:
    """Send a prompt to the local Ollama model and return the response text."""
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "options": {
            "temperature": 0.1,   # low temp = factual, consistent answers
            "num_predict": 1024,
        },
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        return (
            "**Ollama is not running.** Please start it with `ollama serve` "
            "and ensure the model is pulled: `ollama pull llama3.1`"
        )
    except Exception as e:
        return f"**LLM error:** {e}"
