"""
Policy router — routes queries to the correct policy retriever.
Uses best-match (highest keyword count) to prevent cross-policy conflicts.
"""

from policies.whistleblower.config      import KEYWORDS as WB_KEYWORDS
from policies.whistleblower.retriever   import answer as wb_answer
from policies.posh.config               import KEYWORDS as POSH_KEYWORDS
from policies.posh.retriever            import answer as posh_answer
from policies.grievance.config          import KEYWORDS as GRV_KEYWORDS
from policies.grievance.retriever       import answer as grv_answer
from policies.gender.config             import KEYWORDS as GEN_KEYWORDS
from policies.gender.retriever          import answer as gen_answer
from policies.domestic_travel.config    import KEYWORDS as DT_KEYWORDS
from policies.domestic_travel.retriever import answer as dt_answer
from policies.joining.config            import KEYWORDS as JN_KEYWORDS
from policies.joining.retriever         import answer as jn_answer
from policies.fnf.config                import KEYWORDS as FNF_KEYWORDS
from policies.fnf.retriever             import answer as fnf_answer
from policies.expense.config            import KEYWORDS as EXP_KEYWORDS
from policies.expense.retriever         import answer as exp_answer
from policies.local_conveyance.config   import KEYWORDS as LC_KEYWORDS
from policies.local_conveyance.retriever import answer as lc_answer
from policies.group_health.config       import KEYWORDS as GHI_KEYWORDS
from policies.group_health.retriever    import answer as ghi_answer
from policies.group_personal_accident.config   import KEYWORDS as GPA_KEYWORDS
from policies.group_personal_accident.retriever import answer as gpa_answer
from policies.group_term_life.config    import KEYWORDS as GTL_KEYWORDS
from policies.group_term_life.retriever import answer as gtl_answer
from policies.vdc.config                import KEYWORDS as VDC_KEYWORDS
from policies.vdc.retriever             import answer as vdc_answer
from policies.pankh.config              import KEYWORDS as PANKH_KEYWORDS
from policies.pankh.retriever           import answer as pankh_answer
from policies.talent_mobility.config    import KEYWORDS as TM_KEYWORDS
from policies.talent_mobility.retriever import answer as tm_answer
from policies.medibuddy.config          import KEYWORDS as MB_KEYWORDS
from policies.medibuddy.retriever       import answer as mb_answer
from policies.travel_settlement.config  import KEYWORDS as TS_KEYWORDS
from policies.travel_settlement.retriever import answer as ts_answer
from policies.eap.config                import KEYWORDS as EAP_KEYWORDS
from policies.eap.retriever             import answer as eap_answer

POLICY_REGISTRY = [
    (WB_KEYWORDS,   wb_answer,   "Whistleblower Policy"),
    (POSH_KEYWORDS, posh_answer, "POSH Policy"),
    (GRV_KEYWORDS,  grv_answer,  "Grievance Mechanism Policy"),
    (GEN_KEYWORDS,  gen_answer,  "Gender Policy"),
    (DT_KEYWORDS,   dt_answer,   "Domestic Travel Policy"),
    (JN_KEYWORDS,   jn_answer,   "Joining Policy"),
    (FNF_KEYWORDS,  fnf_answer,  "Full & Final Settlement Policy"),
    (EXP_KEYWORDS,  exp_answer,  "Employee Expense Reimbursement Policy"),
    (LC_KEYWORDS,   lc_answer,   "Local Conveyance Policy"),
    (GHI_KEYWORDS,  ghi_answer,  "Group Health Insurance Policy"),
    (GPA_KEYWORDS,  gpa_answer,  "Group Personal Accident Insurance Policy"),
    (GTL_KEYWORDS,  gtl_answer,  "Group Term Life Insurance Policy"),
    (VDC_KEYWORDS,  vdc_answer,  "Voluntary Death Contribution Policy"),
    (PANKH_KEYWORDS, pankh_answer, "Pankh Employee Referral Policy"),
    (TM_KEYWORDS,   tm_answer,   "Talent Mobility Policy"),
    (MB_KEYWORDS,   mb_answer,   "MediBuddy User Guide"),
    (TS_KEYWORDS,   ts_answer,   "Travel Settlement Guide"),
    (EAP_KEYWORDS,  eap_answer,  "1to1 Employee Assistance Program"),
]

_FALLBACK_MSG = (
    "I'm sorry, I wasn't able to find relevant information in Arvind's HR policy "
    "documents for your question.\n\n"
    "This could mean:\n"
    "- The topic is not covered by the policies I have access to, or\n"
    "- Your question may be outside the scope of HR policies.\n\n"
    "**What you can do:**\n"
    "- Rephrase your question using policy-specific terms\n"
    "- Contact your **Business HR representative** directly"
)


def _keyword_detect(query: str) -> tuple[str | None, int]:
    q = query.lower()
    best_policy, best_count = None, 0
    for keywords, _, label in POLICY_REGISTRY:
        count = sum(1 for kw in keywords if kw in q)
        if count > best_count:
            best_policy, best_count = label, count
    return best_policy if best_count >= 1 else None, best_count


def detect_policy(query: str) -> str | None:
    """
    Hybrid router:
      1. Keyword match on original query — handles raw abbreviations (vdc, ghi, posh…).
      2. Keyword match on normalised query — handles Hindi-English mixed, expansions.
      3. Semantic ONNX similarity — fallback for queries with no keywords in either form.
    """
    # Step 1: original keywords (abbreviations like 'vdc', 'ghi' must match before expansion)
    kw_result, kw_count = _keyword_detect(query)
    if kw_count >= 1:
        return kw_result

    # Step 2: normalised keywords
    from core.query_normalizer import normalise
    normalised = normalise(query)
    kw_result, kw_count = _keyword_detect(normalised)
    if kw_count >= 1:
        return kw_result

    # Step 3: semantic fallback on normalised query
    from core.semantic_router import detect_policy_semantic
    sem_result, _ = detect_policy_semantic(normalised)
    return sem_result


def route(query: str, chat_history: list[dict] = None) -> dict:
    from core.query_normalizer import normalise
    normalised = normalise(query)

    # Step 1: keyword match on original then normalised
    def _best_fn(q_text: str):
        best_fn_, best_cnt = None, 0
        for keywords, answer_fn, label in POLICY_REGISTRY:
            count = sum(1 for kw in keywords if kw in q_text.lower())
            if count > best_cnt:
                best_fn_, best_cnt = answer_fn, count
        return best_fn_, best_cnt

    best_fn, best_count = _best_fn(query)
    if best_count == 0:
        best_fn, best_count = _best_fn(normalised)

    if best_fn:
        result = best_fn(query, chat_history or [])
        result["matched"] = True
        return result

    # Step 2: semantic fallback
    from core.semantic_router import detect_policy_semantic
    sem_label, _ = detect_policy_semantic(normalised)
    if sem_label:
        for keywords, answer_fn, label in POLICY_REGISTRY:
            if label == sem_label:
                result = answer_fn(query, chat_history or [])
                result["matched"] = True
                return result

    return {
        "text":    _FALLBACK_MSG,
        "sources": [],
        "policy":  None,
        "matched": False,
    }
