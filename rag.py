"""
RAG pipeline: hybrid BM25 + semantic retrieval → call Claude → stream answer.
Uses hybrid_rag.HybridRetriever for better numeric and keyword-specific lookups.
"""

import os
import anthropic
from dotenv import load_dotenv
import hybrid_rag

load_dotenv()

TOP_K = 10
MODEL = "claude-sonnet-4-6"

# Thresholds for the two-gate out-of-scope check (see is_low_confidence).
# Content tokens shorter than MIN_TOKEN_LEN are excluded from scoring to prevent
# single digits/symbols ("2", "+") from inflating BM25.
# A query with no policy-keyword hit passes only when ≥2 multi-char content tokens
# individually score >0 in BM25 AND their combined BM25 score ≥ BM25_NOISE_FLOOR.
MIN_TOKEN_LEN   = 2
BM25_NOISE_FLOOR = 5.5   # combined BM25 floor for no-policy-detected queries
BM25_MATCH_MIN   = 2     # min distinct tokens that must score >0 independently

# Message returned when retrieval confidence is too low or query is out of scope.
_OUT_OF_SCOPE_MSG = (
    "I'm sorry, I wasn't able to find relevant information in Arvind's HR policy documents "
    "for your question.\n\n"
    "This could mean:\n"
    "- The topic is not covered by the policies I have access to, or\n"
    "- Your question may be outside the scope of HR policies (e.g. general knowledge questions).\n\n"
    "**What you can do:**\n"
    "- Rephrase your question using policy-specific terms (e.g. *travel reimbursement*, *POSH complaint*, *grievance process*)\n"
    "- Contact your **Business HR representative** directly\n"
    "- Reach the **Ethics Helpline** at `1800 200 8301` or `arvind@ethicshelpline.in`"
)

SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant. \
Your role is to help employees understand company HR policies accurately and clearly.

Guidelines:
- Read the employee's question carefully and identify exactly what they are asking.
- Answer ONLY from the policy context provided below. Do not invent information.
- Focus your answer on the section(s) that DIRECTLY address the specific question — do not lead with tangentially related sections.
- Always mention which policy you are referencing (e.g., "As per the Domestic Travel Policy...").
- If the policy context does not contain enough information to answer the question, respond with exactly: "I'm sorry, this specific detail is not covered in the policies I have access to. Please contact your Business HR for assistance."
- Never guess, infer, or fill in details not present in the context.
- Be professional, concise, and empathetic in tone.
- For POSH or grievance issues, always include the relevant helpline/contact if present in the context.
- Never give legal advice or speculate beyond what the policy states.
- Format responses clearly using bullet points or numbered steps when listing conditions or steps.
"""

def retrieve(query: str) -> list[dict]:
    """Return top-K relevant policy chunks via hybrid BM25 + semantic retrieval."""
    return hybrid_rag.retrieve(query, n_results=TOP_K)


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


def _max_bm25_content_score(query: str) -> float:
    """Return the max BM25 score across all chunks for the query's content tokens."""
    from hybrid_rag import _retriever, _tokenise, _BM25_STOPWORDS
    _retriever._ensure_loaded()
    content_tokens = [t for t in _tokenise(query) if t not in _BM25_STOPWORDS]
    if not content_tokens:
        return 0.0
    scores = _retriever._bm25.get_scores(content_tokens)
    return float(max(scores))


def _count_matched_tokens(query: str) -> int:
    """Count distinct content tokens that score >0 in at least one policy chunk."""
    from hybrid_rag import _retriever, _tokenise, _BM25_STOPWORDS
    _retriever._ensure_loaded()
    content_tokens = [
        t for t in _tokenise(query)
        if t not in _BM25_STOPWORDS and len(t) >= MIN_TOKEN_LEN
    ]
    if not content_tokens:
        return 0
    matched = 0
    for token in set(content_tokens):
        scores = _retriever._bm25.get_scores([token])
        if max(scores) > 0:
            matched += 1
    return matched


def is_low_confidence(query: str, chunks: list[dict]) -> bool:
    """
    Return True when the query is out of Arvind HR policy scope.

    Three-gate logic (must pass all to be considered on-topic):
      Gate 1 — policy keyword: explicit Arvind policy hit → always pass.
      Gate 2 — BM25 noise floor: combined content-token BM25 score must be
               above BM25_NOISE_FLOOR.
      Gate 3 — token coverage: at least BM25_MATCH_MIN distinct content tokens
               must independently appear somewhere in the policy corpus.
               Prevents single common words (e.g. "india") from inflating the
               score enough to pass generic/off-topic queries like
               "Who is the PM of India?".
    """
    if not chunks:
        return True
    from hybrid_rag import _detect_policy
    if _detect_policy(query):
        return False  # explicit policy match → always on-topic
    bm25_max = _max_bm25_content_score(query)
    if bm25_max < BM25_NOISE_FLOOR:
        return True
    matched = _count_matched_tokens(query)
    return matched < BM25_MATCH_MIN


def stream_answer(query: str, chat_history: list[dict]):
    """
    Retrieve context, build prompt, stream Claude response.
    Yields text chunks as they arrive.
    Also yields a special dict at the end: {"sources": [...]} for citation display.
    """
    chunks = retrieve(query)

    # Guardrail: short-circuit before touching the LLM if retrieval is empty or
    # the BM25 signal is below the confidence floor (query is out of scope / unknown).
    if is_low_confidence(query, chunks):
        yield _OUT_OF_SCOPE_MSG
        yield {"sources": []}
        return

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
