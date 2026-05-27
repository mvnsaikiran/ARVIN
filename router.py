"""
Policy router — detects which policy a query is about and delegates to it.
Grows as we add more policies: just register them in POLICY_REGISTRY.
"""

from policies.whistleblower.config   import KEYWORDS as WB_KEYWORDS
from policies.whistleblower.retriever import answer as wb_answer

# Registry: each entry is (keywords_list, answer_function, policy_label)
POLICY_REGISTRY = [
    (WB_KEYWORDS, wb_answer, "Whistleblower Policy"),
    # Policy 2 will be added here once built
]

_FALLBACK_MSG = (
    "I'm sorry, I wasn't able to find relevant information in Arvind's HR policy "
    "documents for your question.\n\n"
    "This could mean:\n"
    "- The topic is not covered by the policies I have access to, or\n"
    "- Your question may be outside the scope of HR policies.\n\n"
    "**What you can do:**\n"
    "- Rephrase your question using policy-specific terms\n"
    "- Contact your **Business HR representative** directly\n"
    "- Reach the **Ethics Helpline** at `1800 200 8301` or `arvind@ethicshelpline.in`"
)


def detect_policy(query: str) -> str | None:
    """Return the matched policy label, or None if no match."""
    q = query.lower()
    best_policy, best_count = None, 0
    for keywords, _, label in POLICY_REGISTRY:
        count = sum(1 for kw in keywords if kw in q)
        if count > best_count:
            best_policy, best_count = label, count
    return best_policy if best_count >= 1 else None


def route(query: str, chat_history: list[dict] = None) -> dict:
    """
    Route query to the right policy retriever.
    Returns: {text, sources, policy, matched}
    """
    q = query.lower()
    for keywords, answer_fn, label in POLICY_REGISTRY:
        if any(kw in q for kw in keywords):
            result = answer_fn(query, chat_history or [])
            result["matched"] = True
            return result

    return {
        "text":    _FALLBACK_MSG,
        "sources": [],
        "policy":  None,
        "matched": False,
    }
