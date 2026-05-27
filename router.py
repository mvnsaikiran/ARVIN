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


def detect_policy(query: str) -> str | None:
    q = query.lower()
    best_policy, best_count = None, 0
    for keywords, _, label in POLICY_REGISTRY:
        count = sum(1 for kw in keywords if kw in q)
        if count > best_count:
            best_policy, best_count = label, count
    return best_policy if best_count >= 1 else None


def route(query: str, chat_history: list[dict] = None) -> dict:
    q = query.lower()
    best_fn, best_count = None, 0
    for keywords, answer_fn, _ in POLICY_REGISTRY:
        count = sum(1 for kw in keywords if kw in q)
        if count > best_count:
            best_fn, best_count = answer_fn, count

    if best_fn:
        result = best_fn(query, chat_history or [])
        result["matched"] = True
        return result

    return {
        "text":    _FALLBACK_MSG,
        "sources": [],
        "policy":  None,
        "matched": False,
    }
