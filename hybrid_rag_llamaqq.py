"""
LlamaIndex-style Multi-Query Retrieval using Gemini REST API.

Architecture (mirrors LlamaIndex QueryFusionRetriever):
  1. Gemini generates N policy-vocabulary reformulations of the query
  2. Run hybrid_rag.retrieve() on each reformulation + the original
  3. Reciprocal Rank Fusion (RRF) merges all candidate sets
  4. Return deduplicated top-K

Only activates for cross-policy queries (_detect_policy = None).
Policy-detected queries use the standard hybrid_rag path unchanged.
"""

import os, json, re, requests
from dotenv import load_dotenv
import hybrid_rag
from hybrid_rag import _detect_policy, FINAL_K, RRF_K

load_dotenv()

# ── Gemini REST config ─────────────────────────────────────────────────────────
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)
N_QUERIES  = 4      # reformulations to generate
TIMEOUT_S  = 8      # REST call timeout

# ── Prompt (LlamaIndex QueryFusionRetriever style, HR-domain tuned) ────────────
_SYSTEM = (
    "You are a search query generator for Arvind Limited's HR policy database. "
    "The database contains 18 policies: Domestic Travel, Joining Policy, "
    "Local Conveyance, Talent Mobility (MAB/SIA), POSH, Whistleblower, "
    "Gender Policy, Grievance Mechanism, Group Health Insurance (GHI/FHPL), "
    "Group Term Life Insurance (GTL/GTI), Group Personal Accident (GPA), "
    "Employee Assistance Program (EAP/1to1help), Employee Expense Reimbursement, "
    "Exit & Full & Final Settlement (F&F), Voluntary Death Contribution (VDCS), "
    "Pankh Employee Referral, MediBuddy, Domestic Travel Expense Settlement."
)

_USER_TMPL = (
    "An Arvind Limited employee asked: \"{question}\"\n\n"
    "Generate exactly {n} search queries to find the answer in the HR policy database. "
    "Rules:\n"
    "- Use specific Arvind HR terms: reimbursement, POSH, GHI, EAP, VDCS, MAB, SIA, F&F, GTL, GPA\n"
    "- Include policy names, grade codes (OT/E1/E2/M1/M2/M3/BMH), or contact details where relevant\n"
    "- Cover different policies that might have the answer\n"
    "- Each query must be a complete search phrase (5-12 words)\n\n"
    "Output ONLY the {n} queries, one per line, no numbering, no extra text."
)


def _call_gemini(question: str) -> list[str]:
    """Call Gemini REST API and return a list of reformulated queries."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return []

    payload = {
        "system_instruction": {"parts": [{"text": _SYSTEM}]},
        "contents": [{"parts": [{"text": _USER_TMPL.format(n=N_QUERIES, question=question)}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 400},
    }
    try:
        resp = requests.post(
            GEMINI_ENDPOINT,
            params={"key": api_key},
            json=payload,
            timeout=TIMEOUT_S,
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        return lines[:N_QUERIES]
    except Exception as e:
        return []   # graceful fallback to base retrieval


def _rrf_merge(ranked_lists: list[list[dict]], k: int = FINAL_K) -> list[dict]:
    """Reciprocal Rank Fusion across multiple ranked result lists."""
    scores: dict[str, float] = {}
    best:   dict[str, dict]  = {}

    for results in ranked_lists:
        for rank, chunk in enumerate(results):
            key = chunk["text"][:80]
            scores[key] = scores.get(key, 0.0) + 1.0 / (RRF_K + rank + 1)
            if key not in best:
                best[key] = chunk

    merged = sorted(scores.items(), key=lambda x: -x[1])
    return [best[key] for key, _ in merged[:k]]


def retrieve(query: str, n_results: int = FINAL_K) -> list[dict]:
    """
    LlamaIndex-style Multi-Query Retrieval.
    Falls back to standard hybrid_rag if Gemini is unavailable.
    """
    # Standard path for policy-detected queries — don't touch what works
    if _detect_policy(query):
        return hybrid_rag.retrieve(query, n_results)

    # Generate reformulations via Gemini
    reformulations = _call_gemini(query)

    # If Gemini failed, fall back to base retriever
    if not reformulations:
        return hybrid_rag.retrieve(query, n_results)

    # Retrieve for original + all reformulations
    all_queries = [query] + reformulations
    all_results = []
    seen_queries: set[str] = set()
    for q in all_queries:
        q_norm = q.lower().strip()
        if q_norm in seen_queries:
            continue
        seen_queries.add(q_norm)
        chunks = hybrid_rag.retrieve(q, n_results)
        all_results.append(chunks)

    return _rrf_merge(all_results, k=n_results)
