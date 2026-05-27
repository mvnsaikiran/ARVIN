"""
ARVIN Backend v2 — clean, per-policy RAG, local Ollama LLM.
FastAPI on port 8001.

Endpoints:
  POST /api/chat          — main chat endpoint (called by frontend)
  POST /api/ingest        — rebuild vectorstore for all ingested policies
  GET  /api/health        — health check
  POST /api/debug/retrieve — inspect what chunks are retrieved for a query
"""

import os
import sys
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="ARVIN HR Policy Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
_HERE = os.path.dirname(os.path.abspath(__file__))
_DIST = os.path.join(_HERE, "dist")
if os.path.isdir(_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")


# ── Request models ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    employeeId: str = "anonymous"
    memory_context: str = ""
    chat_history: list[dict] = []


class DebugRequest(BaseModel):
    query: str


class IngestRequest(BaseModel):
    policy: str = "all"   # "all" or specific policy name like "whistleblower"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "backend": "arvin-v2-ollama"}


@app.get("/")
def root():
    index = os.path.join(_DIST, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "ARVIN backend running. Build the frontend to serve the UI."}


@app.post("/api/chat")
def chat(req: ChatRequest):
    """Main chat endpoint — routes query to the right policy retriever."""
    try:
        from router import route

        query = req.query.strip()
        if not query:
            return {
                "text": "Please ask a question.",
                "type": "error",
                "suggestedQuestions": [],
            }

        history = req.chat_history or []
        if req.memory_context.strip():
            history = [{"role": "system", "content": req.memory_context}] + history

        result = route(query, history)

        citations = [
            {
                "policyName":         s["policy"],
                "pageNumber":         s["page"],
                "sourceDocumentName": s["policy"],
            }
            for s in result.get("sources", [])
        ]
        top = citations[0] if citations else {}

        return {
            "text": result["text"],
            "type": "policy_details" if result.get("matched") else "general",
            "suggestedQuestions": [],
            "data": {
                "confidenceScore":    0.95 if result.get("matched") else 0,
                "source":             "ARVIN Hybrid RAG (local)",
                "policyName":         result.get("policy") or "",
                "sourceDocumentName": top.get("sourceDocumentName", ""),
                "pageNumber":         top.get("pageNumber", 1),
                "citations":          citations,
            },
        }

    except RuntimeError as e:
        # Vectorstore not built yet
        return {
            "text": (
                f"**Setup required:** {e}\n\n"
                "Run ingestion first: `python -m policies.whistleblower.ingest`"
            ),
            "type": "error",
            "suggestedQuestions": [],
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/debug/retrieve")
def debug_retrieve(req: DebugRequest):
    """Show exactly which chunks are retrieved for a query — use for tuning."""
    try:
        from router import detect_policy, POLICY_REGISTRY
        from policies.whistleblower.retriever import _retriever as wb_ret

        query    = req.query.strip()
        detected = detect_policy(query)

        # For now only whistleblower is loaded
        wb_ret._load()
        chunks = wb_ret.retrieve(query)

        return {
            "query":           query,
            "detected_policy": detected,
            "chunks": [
                {
                    "rank":    i + 1,
                    "policy":  c["policy_name"],
                    "page":    c["page"],
                    "score":   c["score"],
                    "snippet": c["text"][:150].replace("\n", " "),
                }
                for i, c in enumerate(chunks)
            ],
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}


@app.post("/api/ingest")
def ingest(req: IngestRequest):
    """Rebuild vectorstore for the specified policy (or all)."""
    scripts = {
        "whistleblower": "policies.whistleblower.ingest",
        # add more as they're built
    }
    to_run = list(scripts.values()) if req.policy == "all" else [scripts.get(req.policy)]
    if not to_run or to_run[0] is None:
        raise HTTPException(status_code=400, detail=f"Unknown policy: {req.policy}")

    outputs = []
    for module in to_run:
        result = subprocess.run(
            [sys.executable, "-m", module],
            capture_output=True, text=True, timeout=300,
            cwd=_HERE,
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
        outputs.append(result.stdout)

    return {"success": True, "output": "\n".join(outputs)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
