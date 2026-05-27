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

# Routing confidence thresholds
_HIGH_CONF  = 0.55   # semantic THRESHOLD — route directly
_LOW_CONF   = 0.42   # below THRESHOLD but non-trivial — ask for clarification
_AMBIG_GAP  = 0.05   # if top-2 scores differ by less than this → ambiguous

_POLICY_BLURB: dict[str, str] = {
    "Whistleblower Policy":                    "reporting fraud, misconduct, or ethics violations",
    "POSH Policy":                             "sexual harassment complaints and the Anti-Harassment Committee",
    "Grievance Mechanism Policy":              "raising and resolving workplace complaints",
    "Gender Policy":                           "gender equality and LGBTQ inclusion",
    "Domestic Travel Policy":                  "hotel limits, flight booking, and daily allowances for business trips",
    "Joining Policy":                          "relocation benefits and onboarding for new hires",
    "Full & Final Settlement Policy":          "notice period, FnF settlement, and relieving letters",
    "Employee Expense Reimbursement Policy":   "claiming reimbursement for work-related expenses",
    "Local Conveyance Policy":                 "per-km rates and claiming local travel costs",
    "Group Health Insurance Policy":           "cashless hospitalisation and mediclaim coverage",
    "Group Personal Accident Insurance Policy":"compensation for accidental injury or disability",
    "Group Term Life Insurance Policy":        "life insurance cover and nominee nominations",
    "Voluntary Death Contribution Policy":     "the VDC solidarity fund when a colleague passes away",
    "Pankh Employee Referral Policy":          "bonuses for referring female or transgender candidates",
    "Talent Mobility Policy":                  "internal job postings and lateral transfers",
    "MediBuddy User Guide":                    "the MediBuddy app, teleconsultations, and health services",
    "Travel Settlement Guide":                 "submitting hotel and flight bills via MyTour after a trip",
    "1to1 Employee Assistance Program":        "free confidential counselling for employees and family",
}

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


def _clarification_response(
    query: str,
    top_policy: "str | None",
    second_policy: "str | None",
) -> dict:
    """
    Graceful degradation: when routing confidence is low, ask the employee
    to clarify rather than guessing and potentially giving wrong information.
    """
    lines = [
        "I'm not fully certain which policy that refers to. Could you clarify if you're asking about:"
    ]
    if top_policy:
        blurb = _POLICY_BLURB.get(top_policy, "")
        lines.append(f"\n1. **{top_policy}**" + (f" — {blurb}" if blurb else ""))
    if second_policy:
        blurb = _POLICY_BLURB.get(second_policy, "")
        lines.append(f"2. **{second_policy}**" + (f" — {blurb}" if blurb else ""))
    lines.append(
        "\nOr feel free to **rephrase** your question, "
        "or contact your **Business HR representative** directly."
    )
    return {
        "text":       "\n".join(lines),
        "sources":    [],
        "policy":     None,
        "matched":    False,
        "confidence": 0.0,
    }


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
    Hybrid router (4-tier):
      1. Keyword match on original query — handles raw abbreviations (vdc, ghi, posh…)
      2. Keyword match on normalised query — handles Hindi-English mixed, expansions
      3. Synthetic router index — 50 LLM-generated questions per policy (if built)
      4. ONNX anchor matrix — 12-14 handcrafted anchors per policy (always available)
    """
    kw_result, kw_count = _keyword_detect(query)
    if kw_count >= 1:
        return kw_result

    from core.query_normalizer import normalise
    normalised = normalise(query)
    kw_result, kw_count = _keyword_detect(normalised)
    if kw_count >= 1:
        return kw_result

    from core.semantic_router import route_via_router_index, detect_policy_semantic
    ri_result, _ = route_via_router_index(normalised)
    if ri_result:
        return ri_result

    sem_result, _ = detect_policy_semantic(normalised)
    return sem_result


def _find_answer_fn(label: str):
    for _, answer_fn, lbl in POLICY_REGISTRY:
        if lbl == label:
            return answer_fn
    return None


def route(query: str, chat_history: list[dict] = None) -> dict:
    from core.query_normalizer import normalise
    from core.confidence_logger import log_routing_event
    normalised = normalise(query)

    # ── Step 1 & 2: keyword match ──────────────────────────────────────────
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
        result["matched"]    = True
        result["confidence"] = 1.0
        log_routing_event(query, result.get("policy"), 1.0, "keyword")
        return result

    # ── Step 3: synthetic router index ─────────────────────────────────────
    from core.semantic_router import route_via_router_index, detect_top2_semantic
    ri_label, ri_score = route_via_router_index(normalised)
    if ri_label and ri_score >= _HIGH_CONF:
        fn = _find_answer_fn(ri_label)
        if fn:
            result = fn(query, chat_history or [])
            result["matched"]    = True
            result["confidence"] = ri_score
            log_routing_event(query, ri_label, ri_score, "router_index")
            return result

    # ── Step 4: ONNX anchor matrix ─────────────────────────────────────────
    top2 = detect_top2_semantic(normalised)
    top_label, top_score   = top2[0] if top2 else (None, 0.0)
    sec_label, sec_score   = top2[1] if len(top2) > 1 else (None, 0.0)

    # Prefer the router-index label if it's in the top-2
    if ri_label and ri_score >= _LOW_CONF and ri_label in (top_label, sec_label):
        top_label, top_score = ri_label, max(ri_score, top_score)

    if top_score >= _HIGH_CONF:
        # Ambiguity check: two policies very close together
        if sec_score and top_score - sec_score < _AMBIG_GAP:
            log_routing_event(query, None, top_score, "clarification")
            return _clarification_response(query, top_label, sec_label)

        fn = _find_answer_fn(top_label)
        if fn:
            result = fn(query, chat_history or [])
            result["matched"]    = True
            result["confidence"] = top_score
            log_routing_event(query, top_label, top_score, "semantic")
            return result

    # ── Step 5: graceful degradation (low-confidence) ──────────────────────
    if top_score >= _LOW_CONF:
        sec_display = sec_label if sec_score and sec_score >= 0.35 else None
        log_routing_event(query, None, top_score, "clarification")
        return _clarification_response(query, top_label, sec_display)

    # ── Step 6: OOS fallback ───────────────────────────────────────────────
    log_routing_event(query, None, top_score, "oos")
    return {
        "text":       _FALLBACK_MSG,
        "sources":    [],
        "policy":     None,
        "matched":    False,
        "confidence": 0.0,
    }
