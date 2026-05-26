"""
Python RAG backend — FastAPI on port 8001.
Retrieval: hybrid BM25 + ChromaDB semantic (hybrid_rag.py)
LLM: Gemini 2.5 Flash via REST API (gRPC SDK blocked in this environment)

Endpoints:
  POST /api/claude/generate  — RAG-enriched Gemini response (called from geminiProxy.ts)
  POST /api/ingest           — re-index all policies in ./policies/
  GET  /api/health           — health check
"""

import os
import sys
import subprocess
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ARVIN RAG Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Gemini REST config ────────────────────────────────────────────────────────

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)
GEMINI_TIMEOUT = 30

ARVIN_SYSTEM_PROMPT = (
    "You are ARVIN, Arvind Limited's official HR Policy Assistant. "
    "Your role is to help employees understand company HR policies accurately and clearly.\n\n"
    "Guidelines:\n"
    "- Answer ONLY from the policy context provided. Do not invent information.\n"
    "- Always mention which policy you are referencing "
    "(e.g., 'As per the Domestic Travel Policy...').\n"
    "- If the context does not contain enough information, respond with exactly: "
    "'I'm sorry, this specific detail is not covered in the policies I have access to. "
    "Please contact your Business HR for assistance.'\n"
    "- Never guess, infer, or fill in details not present in the context.\n"
    "- Be professional, concise, and empathetic in tone.\n"
    "- For POSH or grievance issues, always include the relevant helpline/contact "
    "if present in the context.\n"
    "- Format responses clearly using bullet points or numbered steps where appropriate."
)


def call_gemini(system_prompt: str, user_message: str) -> str:
    """Call Gemini 2.5 Flash via REST and return the answer text."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set.")

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_message}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        },
    }
    try:
        resp = requests.post(
            GEMINI_ENDPOINT,
            params={"key": api_key},
            json=payload,
            timeout=GEMINI_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Gemini API timed out.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {e}")

# ── Request model ─────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    contents: list[Any]
    config: dict[str, Any] = {}

# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_query(contents: list[Any]) -> str:
    """Extract the last user query text from Gemini-format contents."""
    for item in reversed(contents):
        if not isinstance(item, dict):
            continue
        if item.get("role", "user") != "user":
            continue
        for part in item.get("parts", []):
            text = part.get("text", "") if isinstance(part, dict) else str(part)
            if text.strip():
                return text.strip()
    raise ValueError("No user text found in request contents.")


def build_user_message(query: str, context: str, history: list[Any]) -> str:
    """Build the full user message with policy context and optional chat history."""
    history_text = ""
    turns = []
    for item in history:
        if not isinstance(item, dict):
            continue
        role = item.get("role", "")
        for part in item.get("parts", []):
            text = part.get("text", "") if isinstance(part, dict) else str(part)
            if text.strip():
                turns.append(f"{role.upper()}: {text.strip()}")
    if turns:
        history_text = "CONVERSATION HISTORY:\n" + "\n".join(turns) + "\n\n"

    return (
        f"{history_text}"
        f"POLICY CONTEXT:\n{context}\n\n"
        f"EMPLOYEE QUESTION:\n{query}"
    )

# ── Lazy RAG loader ───────────────────────────────────────────────────────────

_rag_ready = False

def ensure_rag():
    global _rag_ready
    if not _rag_ready:
        import rag  # triggers ChromaDB + ONNX model load
        _rag_ready = True

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "backend": "chromadb-gemini"}


@app.post("/api/ingest")
def ingest():
    """Rebuild the ChromaDB vectorstore from policies/."""
    try:
        result = subprocess.run(
            [sys.executable, "ingest.py"],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        return {"success": True, "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/claude/generate")
def rag_generate(req: GenerateRequest):
    """
    1. Extract query from Gemini-format contents
    2. Retrieve relevant policy chunks via hybrid BM25 + semantic (hybrid_rag)
    3. Guardrail: short-circuit if retrieval confidence is too low
    4. Build context block and call Gemini 2.5 Flash via REST for the answer
    """
    try:
        ensure_rag()
        from rag import retrieve, build_context_block, is_low_confidence, _OUT_OF_SCOPE_MSG

        query = extract_query(req.contents)
        history = req.contents[:-1]

        # Hybrid retrieval
        chunks = retrieve(query)

        # Guardrail: out-of-scope queries return fallback without touching Gemini
        if is_low_confidence(query, chunks):
            return {"text": _OUT_OF_SCOPE_MSG}

        context = build_context_block(chunks)
        user_message = build_user_message(query, context, history)

        # Generate answer via Gemini 2.5 Flash REST
        answer = call_gemini(ARVIN_SYSTEM_PROMPT, user_message)
        return {"text": answer}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
