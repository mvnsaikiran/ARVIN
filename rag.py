"""
RAG pipeline: embed query → retrieve policy chunks → call Claude → stream answer.
"""

import os
import anthropic
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

VECTORSTORE_DIR = "vectorstore"
TOP_K = 6  # chunks to retrieve
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant. \
Your role is to help employees understand company HR policies accurately and clearly.

Guidelines:
- Answer ONLY from the policy context provided below. Do not invent information.
- Always mention which policy you are referencing (e.g., "As per the Domestic Travel Policy...").
- If the answer is not found in the context, say: "This is not covered in the policies I have access to. Please contact your Business HR for assistance."
- Be professional, concise, and empathetic in tone.
- For POSH or grievance issues, always include the relevant helpline/contact if present in the context.
- Never give legal advice or speculate beyond what the policy states.
- Format responses clearly using bullet points or numbered steps when listing conditions or steps.
"""

_ef = None
_collection = None
_client = None


def _get_ef():
    global _ef
    if _ef is None:
        _ef = embedding_functions.ONNXMiniLM_L6_V2()
    return _ef


def _get_collection():
    global _collection, _client
    if _collection is None:
        _client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
        _collection = _client.get_collection(
            "arvind_policies", embedding_function=_get_ef()
        )
    return _collection


def retrieve(query: str) -> list[dict]:
    """Return top-K relevant policy chunks for the query."""
    collection = _get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "policy_name": meta["policy_name"],
            "page": meta["page"],
            "filename": meta["filename"],
            "score": round(1 - dist, 3),  # cosine similarity
        })
    return chunks


def build_context_block(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the prompt."""
    parts = []
    seen = set()
    for c in chunks:
        key = (c["policy_name"], c["page"])
        if key in seen:
            continue
        seen.add(key)
        parts.append(
            f"[Source: {c['policy_name']} | Page {c['page']}]\n{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


def stream_answer(query: str, chat_history: list[dict]):
    """
    Retrieve context, build prompt, stream Claude response.
    Yields text chunks as they arrive.
    Also yields a special dict at the end: {"sources": [...]} for citation display.
    """
    chunks = retrieve(query)
    context = build_context_block(chunks)

    # Build messages list for Claude
    messages = []
    for turn in chat_history:
        messages.append({"role": turn["role"], "content": turn["content"]})

    # Inject context into the user query
    user_message = (
        f"POLICY CONTEXT:\n{context}\n\n"
        f"EMPLOYEE QUESTION:\n{query}"
    )
    messages.append({"role": "user", "content": user_message})

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        yield "**Error:** `ANTHROPIC_API_KEY` not set. Please add it to your `.env` file."
        return

    client = anthropic.Anthropic(api_key=api_key)
    with client.messages.stream(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text

    # Yield source citations as final metadata chunk
    unique_sources = {}
    for c in chunks:
        key = c["policy_name"]
        if key not in unique_sources:
            unique_sources[key] = c["page"]
    yield {"sources": [{"policy": k, "page": v} for k, v in unique_sources.items()]}
