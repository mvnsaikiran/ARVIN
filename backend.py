"""
Python RAG backend — FastAPI on port 8001.
Retrieval: ChromaDB (semantic search over 8 Arvind HR policies)
LLM: Gemini (via GEMINI_API_KEY) — same model as the frontend uses

Endpoints:
  POST /api/claude/generate  — RAG-enriched Gemini response (called from geminiProxy.ts)
  POST /api/ingest           — re-index all policies in ./policies/
  GET  /api/health           — health check
"""

import os
import sys
import subprocess
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = FastAPI(title="ARVIN RAG Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Gemini client ─────────────────────────────────────────────────────────────

def get_gemini_client():
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set.")
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-2.0-flash")

# ── Request model ─────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    contents: list[Any]
    config: dict[str, Any] = {}

# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_query_and_history(contents: list[Any]) -> tuple[str, list[dict]]:
    """Extract last user query + prior turns from Gemini-format contents."""
    messages = []
    for item in contents:
        if not isinstance(item, dict):
            continue
        role = item.get("role", "user")
        parts = item.get("parts", [])
        text = ""
        for part in parts:
            if isinstance(part, dict):
                text += part.get("text", "")
            elif isinstance(part, str):
                text += part
        if text.strip():
            messages.append({"role": role, "text": text.strip()})

    if not messages:
        raise ValueError("No text content found in request.")

    last_query = messages[-1]["text"]
    return last_query, messages[:-1]


def inject_rag_context(contents: list[Any], context: str) -> list[Any]:
    """Prepend ChromaDB context into the last user turn."""
    if not contents:
        return contents
    enriched = list(contents)
    last = dict(enriched[-1]) if isinstance(enriched[-1], dict) else {}
    parts = list(last.get("parts", []))
    if parts and isinstance(parts[-1], dict) and "text" in parts[-1]:
        original_text = parts[-1]["text"]
        parts[-1] = {
            "text": (
                f"[POLICY CONTEXT FROM KNOWLEDGE BASE]\n{context}\n"
                f"[END POLICY CONTEXT]\n\n{original_text}"
            )
        }
    last["parts"] = parts
    enriched[-1] = last
    return enriched

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
    2. Retrieve relevant policy chunks from ChromaDB
    3. Inject context into the request
    4. Call Gemini and return {text: ...}
    """
    try:
        ensure_rag()
        from rag import retrieve, build_context_block

        query, _ = extract_query_and_history(req.contents)

        # ChromaDB semantic retrieval
        chunks = retrieve(query)
        context = build_context_block(chunks)

        # Inject context into the Gemini request
        enriched_contents = inject_rag_context(req.contents, context)

        # Call Gemini
        model = get_gemini_client()
        response = model.generate_content(enriched_contents)
        text = response.text if response.text else ""

        return {"text": text}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
