"""
Python RAG backend — FastAPI on port 8001.
Receives requests from the Node.js server (server.ts) and responds with
Claude-generated answers grounded in ChromaDB policy chunks.

Endpoints:
  POST /api/claude/generate  — main chat (called from geminiProxy.ts)
  POST /api/ingest           — re-index all policies in ./policies/
  GET  /api/health           — health check
"""

import os
import sys
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ARVIN Python RAG Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request models ────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    contents: list[Any]       # Gemini-format content array from the frontend
    config: dict[str, Any] = {}

class IngestRequest(BaseModel):
    pass

# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_query_and_history(contents: list[Any]) -> tuple[str, list[dict]]:
    """
    Convert Gemini-format contents into (last_user_query, chat_history).
    Gemini format: [{role: "user", parts: [{text: "..."}]}, ...]
    """
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
            # Map Gemini roles to Anthropic roles
            anthropic_role = "assistant" if role == "model" else "user"
            messages.append({"role": anthropic_role, "content": text.strip()})

    if not messages:
        raise ValueError("No text content found in request.")

    # Last message is the current question; the rest is history
    last = messages[-1]["content"]
    history = messages[:-1]
    return last, history


def get_system_instruction(config: dict) -> str | None:
    """Extract system instruction from Gemini config if present."""
    si = config.get("systemInstruction")
    if isinstance(si, str):
        return si
    if isinstance(si, dict):
        parts = si.get("parts", [])
        texts = [p.get("text", "") for p in parts if isinstance(p, dict)]
        return " ".join(texts).strip() or None
    return None


# ── Lazy-load RAG module ──────────────────────────────────────────────────────

_rag_loaded = False

def ensure_rag():
    global _rag_loaded
    if not _rag_loaded:
        import rag  # noqa: F401 — triggers model + collection load
        _rag_loaded = True


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "backend": "claude-rag"}


@app.post("/api/ingest")
def ingest():
    """Re-run ingest.py to rebuild the ChromaDB vectorstore."""
    try:
        result = subprocess.run(
            [sys.executable, "ingest.py"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        return {"success": True, "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/claude/generate")
def claude_generate(req: GenerateRequest):
    """
    Main chat endpoint. Extracts the query from Gemini-format contents,
    runs RAG retrieval against ChromaDB, and calls Claude for the answer.
    Returns {"text": "..."} to match the existing frontend contract.
    """
    try:
        ensure_rag()
        from rag import stream_answer, retrieve, build_context_block
        import anthropic

        query, history = extract_query_and_history(req.contents)

        # Build RAG context
        chunks = retrieve(query)
        context = build_context_block(chunks)

        # System prompt — use frontend's instruction if present, else default
        frontend_system = get_system_instruction(req.config)
        system_prompt = frontend_system or (
            "You are ARVIN, Arvind Limited's official HR Policy Assistant. "
            "Answer ONLY from the policy context provided. Always cite which policy "
            "you are referencing. If the answer is not in the context, say so and "
            "suggest contacting Business HR. Be professional and concise."
        )

        # Build messages for Claude
        messages = list(history)
        user_message = f"POLICY CONTEXT:\n{context}\n\nEMPLOYEE QUESTION:\n{query}"
        messages.append({"role": "user", "content": user_message})

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set.")

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )

        text = message.content[0].text if message.content else ""
        return {"text": text}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
