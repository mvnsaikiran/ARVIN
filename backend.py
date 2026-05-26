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

_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(_HERE, ".env"), override=True)

app = FastAPI(title="ARVIN RAG Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Gemini REST config ────────────────────────────────────────────────────────

_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]
GEMINI_TIMEOUT = 60

ARVIN_SYSTEM_PROMPT = (
    "You are ARVIN, Arvind Limited's official HR Policy Assistant. "
    "Your role is to help employees understand company HR policies accurately and clearly.\n\n"
    "Guidelines:\n"
    "- Read the employee's question carefully and identify exactly what they are asking.\n"
    "- Answer ONLY from the policy context provided. Do not invent information.\n"
    "- Focus your answer on the section(s) that DIRECTLY address the specific question — "
    "do not lead with tangentially related sections.\n"
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
    """Call Gemini via REST, trying models in order until one succeeds."""
    import time
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
    last_err = None
    for model in _GEMINI_MODELS:
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        for attempt in range(3):
            try:
                resp = requests.post(
                    endpoint,
                    params={"key": api_key},
                    json=payload,
                    timeout=GEMINI_TIMEOUT,
                )
                if resp.status_code in (429, 503):
                    time.sleep(2 ** attempt)
                    last_err = f"{model} {resp.status_code}"
                    continue
                resp.raise_for_status()
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            except requests.exceptions.Timeout:
                last_err = f"{model} timeout"
                break
            except Exception as e:
                last_err = str(e)
                break
    raise HTTPException(status_code=502, detail=f"All Gemini models failed: {last_err}")

# ── Request model ─────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    contents: list[Any]
    config: dict[str, Any] = {}

class ChatRequest(BaseModel):
    query: str
    employeeId: str = "anonymous"
    memory_context: str = ""

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
        import hybrid_rag
        hybrid_rag._retriever._ensure_loaded()
        count = hybrid_rag._retriever._chroma.count()
        print(f"[RAG] ChromaDB collection count: {count}", flush=True)
        _rag_ready = True

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "backend": "chromadb-gemini"}


class DebugRequest(BaseModel):
    query: str

@app.post("/api/debug/retrieve")
def debug_retrieve(req: DebugRequest):
    """Show exactly which chunks + policies are retrieved for a query.
    Use this to verify the RAG pipeline is working before involving Gemini."""
    try:
        ensure_rag()
        from rag import retrieve, rerank_chunks_for_query
        from hybrid_rag import _detect_policy

        query = req.query.strip()
        detected = _detect_policy(query)
        chunks = retrieve(query)
        chunks = rerank_chunks_for_query(chunks, query)

        summary = []
        for i, c in enumerate(chunks):
            summary.append({
                "rank": i + 1,
                "policy": c["policy_name"],
                "page": c["page"],
                "score": c["score"],
                "snippet": c["text"][:120].replace("\n", " "),
            })

        policy_counts: dict[str, int] = {}
        for c in chunks:
            policy_counts[c["policy_name"]] = policy_counts.get(c["policy_name"], 0) + 1

        return {
            "query": query,
            "detected_policy": detected,
            "policy_counts": policy_counts,
            "chunks": summary,
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}


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
        from rag import retrieve, build_context_block, is_low_confidence, _OUT_OF_SCOPE_MSG, rerank_chunks_for_query

        query = extract_query(req.contents)
        history = req.contents[:-1]

        # Hybrid retrieval
        chunks = retrieve(query)

        # Guardrail: out-of-scope queries return fallback without touching Gemini
        if is_low_confidence(query, chunks):
            return {"text": _OUT_OF_SCOPE_MSG}

        chunks = rerank_chunks_for_query(chunks, query)
        context = build_context_block(chunks)
        user_message = build_user_message(query, context, history)

        # Generate answer via Gemini 2.5 Flash REST
        answer = call_gemini(ARVIN_SYSTEM_PROMPT, user_message)
        return {"text": answer}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def chat(req: ChatRequest):
    """
    Primary chat endpoint called by the frontend (productionRagService.ts).
    Returns AIResponse format: {text, type, suggestedQuestions, data}.

    Flow:
      1. Hybrid BM25 + semantic retrieval (hybrid_rag)
      2. Out-of-scope guardrail
      3. Gemini 2.5 Flash generates a grounded answer
      4. Returns structured AIResponse the frontend UI can render
    """
    try:
        ensure_rag()
        from rag import retrieve, build_context_block, is_low_confidence, _OUT_OF_SCOPE_MSG, rerank_chunks_for_query

        query = req.query.strip()
        if not query:
            return {
                "text": "Please ask a question.",
                "type": "error",
                "suggestedQuestions": [],
            }

        # Hybrid retrieval
        chunks = retrieve(query)

        # Out-of-scope guardrail
        if is_low_confidence(query, chunks):
            return {
                "text": _OUT_OF_SCOPE_MSG,
                "type": "general",
                "suggestedQuestions": [
                    "What is covered under the travel reimbursement policy?",
                    "How do I file a POSH complaint?",
                    "What are my health insurance benefits?",
                ],
                "data": {"confidenceScore": 0, "source": "Out-of-scope guardrail"},
            }

        chunks = rerank_chunks_for_query(chunks, query)
        context = build_context_block(chunks)

        # Build user message with optional memory context and policy hint
        from hybrid_rag import _detect_policy
        detected = _detect_policy(query)
        policy_hint = f"[This query is specifically about: {detected}]\n\n" if detected else ""
        memory_prefix = f"CONVERSATION HISTORY:\n{req.memory_context}\n\n" if req.memory_context.strip() else ""
        user_message = f"{memory_prefix}{policy_hint}POLICY CONTEXT:\n{context}\n\nEMPLOYEE QUESTION:\n{query}"

        # Generate answer via Gemini 2.5 Flash
        answer = call_gemini(ARVIN_SYSTEM_PROMPT, user_message)

        # Build citations from retrieved chunks
        seen: dict[str, Any] = {}
        for c in chunks:
            key = c["policy_name"]
            if key not in seen:
                seen[key] = {
                    "policyName": c["policy_name"],
                    "sourceDocumentName": c.get("source_file", c["policy_name"]),
                    "pageNumber": c.get("page", 1),
                    "clauseReference": c.get("section", ""),
                    "source": "Python Hybrid RAG (BM25 + Semantic)",
                }

        citations = list(seen.values())
        top = citations[0] if citations else {}

        return {
            "text": answer,
            "type": "policy_details",
            "suggestedQuestions": [],
            "data": {
                "confidenceScore": 0.97,
                "source": "Python Hybrid RAG (BM25 + Semantic)",
                "policyName": top.get("policyName", ""),
                "sourceDocumentName": top.get("sourceDocumentName", ""),
                "pageNumber": top.get("pageNumber", 1),
                "clauseReference": top.get("clauseReference", ""),
                "citations": citations,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "text": f"Error: {e}",
            "type": "error",
            "suggestedQuestions": [],
            "data": {"source": "error", "confidenceScore": 0},
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
