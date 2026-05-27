"""
Semantic policy router.

Two-tier semantic routing:

Tier 1 — Synthetic-anchor ChromaDB index (preferred when built):
  900 LLM-generated questions (50 per policy) covering diverse employee phrasings.
  Route by finding the closest synthetic question; top-3 majority vote.
  Build with:  python scripts/generate_synthetic_anchors.py
               python scripts/build_router_index.py

Tier 2 — ONNX in-memory anchor matrix (fallback / cold-start):
  12-14 handcrafted intent anchors per policy, embedded at first call.
  Always available, no build step needed.

Hybrid strategy used by router.py:
  1. Keyword match on original → route
  2. Keyword match on normalised → route
  3. Synthetic router index (if built) → route if confidence ≥ THRESHOLD
  4. ONNX anchor matrix → route if confidence ≥ THRESHOLD
  5. Graceful degradation: clarify with top-2 if confidence 0.40-0.55
  6. OOS fallback
"""

import os
import numpy as np
from chromadb.utils import embedding_functions

THRESHOLD   = 0.55   # min cosine similarity to claim a policy match
_ROUTER_COL = "arvin_router_index"
_VS_DIR     = os.path.join(os.path.dirname(__file__), '..', 'vectorstore')

# ---------------------------------------------------------------------------
# Intent anchors — 6-8 natural-language questions an employee would actually
# type for each policy.  These should cover topic breadth, not just policy
# jargon.
# ---------------------------------------------------------------------------
POLICY_ANCHORS: dict[str, list[str]] = {
    "Whistleblower Policy": [
        "How do I report fraud or corruption at Arvind?",
        "Is my identity protected if I blow the whistle?",
        "What is the ethics helpline number?",
        "Can I report misconduct anonymously?",
        "What happens after I report wrongdoing?",
        "How do I report a bribery case at work?",
        "Will I face any action for reporting unethical behaviour?",
        "Who can file a protected disclosure under the whistleblower scheme?",
        "What channels are available to report a protected disclosure?",
        "What happens if a whistleblower faces retaliation?",
        "How does the whistleblower policy protect confidentiality?",
        "What are the disciplinary consequences under the whistleblower policy?",
        "What is the purpose of the Whistleblower Policy at Arvind?",
        "What is the eligibility to file a whistleblower complaint?",
    ],
    "POSH Policy": [
        "I am being harassed at work, what should I do?",
        "How do I file a sexual harassment complaint?",
        "Who is on the anti-harassment committee at Arvind?",
        "How long does the POSH inquiry take?",
        "What action is taken after a harassment complaint is filed?",
        "What counts as sexual harassment under the POSH policy?",
        "Can I file a complaint against a colleague for harassment?",
        "What is the role of the Anti Harassment Committee under POSH?",
        "What disciplinary action follows a POSH complaint?",
        "What are the disciplinary consequences under the POSH policy?",
        "What is the inquiry timeline under the POSH policy?",
        "Who is eligible to file a POSH complaint at Arvind?",
        "What are the steps in the POSH complaint procedure?",
    ],
    "Grievance Mechanism Policy": [
        "I have a complaint about my manager, what should I do?",
        "How do I raise a workplace grievance at Arvind?",
        "What is the escalation process for unresolved complaints?",
        "Who handles the first level of grievance resolution?",
        "What is the timeline to resolve a grievance?",
        "Can I raise a grievance about unfair treatment?",
        "How do I formally complain about a workplace issue?",
        "Can a grievance be submitted anonymously at Arvind?",
        "What are the escalation levels in the grievance process?",
        "What is the grievance resolution timeline?",
        "Who is eligible to raise a grievance under this policy?",
    ],
    "Gender Policy": [
        "Is there a policy protecting LGBTQ employees at Arvind?",
        "What is Arvind's stance on gender equality?",
        "How do I report gender-based discrimination?",
        "Are transgender employees protected under any policy?",
        "What is the gender sensitisation programme at Arvind?",
        "Does Arvind have an equal opportunity policy for women?",
        "What disciplinary action is taken for gender-based harassment?",
        "How can an employee report gender discrimination at Arvind?",
        "Are LGBTQ employees protected under the Gender Policy?",
        "What are the disciplinary consequences under the gender policy?",
        "Who is eligible for protection under the gender diversity policy?",
    ],
    "Domestic Travel Policy": [
        "What is my hotel allowance for a business trip?",
        "How do I book a flight for official travel?",
        "What travel class am I entitled to based on my grade?",
        "How much daily allowance do I get for outstation travel?",
        "What is the deadline to submit travel claims after a trip?",
        "Are taxi expenses covered during business travel?",
        "What is the per diem rate for domestic travel?",
        "How do I book tickets on MyBiz for office travel?",
        "What are the hotel limits for M2 grade employees on domestic travel?",
        "What class of travel is an E2 grade employee entitled to?",
        "Are taxi expenses covered under domestic travel policy?",
        "What is the amount limit for hotel accommodation in domestic travel?",
        "Who is eligible for domestic travel reimbursement at Arvind?",
        "What are the steps to book domestic travel at Arvind?",
    ],
    "Joining Policy": [
        "What relocation benefits do I get as a new joiner at Arvind?",
        "Is brokerage covered when I move cities to join Arvind?",
        "What support does Arvind provide for household goods transport?",
        "How long do I have to claim my joining benefits?",
        "What documents do I need to submit on my first day?",
        "What onboarding support does Arvind provide?",
        "Is there a joining bonus or induction allowance?",
        "How do I claim my relocation allowance after joining?",
        "What household goods transportation support is provided to new joiners?",
        "Is brokerage reimbursed for renting accommodation while joining Arvind?",
        "How long does a new joiner have to claim relocation benefits?",
        "What documents are needed to claim joining benefits at Arvind?",
        "What is the amount provided for relocation when joining?",
        "Who is eligible for joining benefits at Arvind?",
    ],
    "Full & Final Settlement Policy": [
        "How long does full and final settlement take after resignation?",
        "What is deducted if I do not serve my full notice period?",
        "How is earned leave encashed when I leave the company?",
        "When will I receive my relieving letter?",
        "What components are included in the FnF payment?",
        "How do I clear my dues and get the no-dues certificate?",
        "What is the FnF process when I resign from Arvind?",
        "How many days does Arvind take to process full and final settlement?",
        "What components are deducted in notice pay recovery during FnF?",
        "What is included in the Full and Final Settlement payment?",
        "What is recovered from FnF if notice period is not served?",
        "What is the timeline for full and final settlement at Arvind?",
        "Who is eligible for earned leave encashment during FnF?",
    ],
    "Employee Expense Reimbursement Policy": [
        "How do I claim reimbursement for a birthday celebration expense?",
        "What is the deadline to submit expense claims?",
        "Who approves my expense reimbursement at Arvind?",
        "What receipts are required for expense claims?",
        "Can I claim for car maintenance or fuel expenses?",
        "Is there a puja or farewell expense reimbursement at Arvind?",
        "Are entertainment expenses covered under the expense reimbursement policy?",
        "What types of expenses can I claim for reimbursement at Arvind?",
        "What is the deadline for submitting an expense claim?",
        "What receipts are needed for expense reimbursement claims?",
        "Who is eligible for expense reimbursement at Arvind?",
        "What are the steps to submit an expense claim?",
    ],
    "Local Conveyance Policy": [
        "What is the per km rate for using my personal vehicle for office work?",
        "Can I claim Ola or Uber rides for local office travel?",
        "Is home to office commute reimbursable at Arvind?",
        "What is the monthly cap on local conveyance claims?",
        "How do I submit a local conveyance claim?",
        "What is the cab allowance for field visits within the city?",
        "What is the rate per km for a personal two-wheeler for local conveyance?",
        "Is home-to-office commute reimbursable under the local conveyance policy?",
        "Are OLA or UBER rides covered under local conveyance at Arvind?",
        "What is the amount limit on local conveyance claims per month?",
        "Who is eligible for local conveyance reimbursement?",
    ],
    "Group Health Insurance Policy": [
        "What is my health insurance coverage at Arvind?",
        "Are my parents covered under the company health insurance?",
        "What is the room rent limit for hospitalisation?",
        "How do I make a cashless health insurance claim?",
        "What is the sum insured under the group mediclaim?",
        "What is the FHPL helpline number for health claims?",
        "Are pre-existing diseases covered under Arvind health insurance?",
        "What is the sum insured under Group Health Insurance at Arvind?",
        "How do I file a cashless health insurance claim?",
        "What is the FHPL helpline number?",
        "What is the room rent limit for hospitalization under group health insurance?",
        "Who is eligible for group health insurance at Arvind?",
        "What are the steps to file a health insurance claim?",
    ],
    "Group Personal Accident Insurance Policy": [
        "What insurance do I get if I meet with an accident?",
        "What is the compensation for permanent disability due to an accident?",
        "Is accidental death covered by Arvind's insurance?",
        "What percentage is paid for partial disability?",
        "Does the accident insurance cover me during personal time?",
        "How do I file a personal accident insurance claim?",
        "What is the GPA cover for loss of limb or eyesight?",
        "What does the Group Personal Accident Insurance cover at Arvind?",
        "Is accidental death covered under GPA?",
        "Does GPA cover accidents outside working hours?",
        "What is the compensation for permanent total disability under GPA?",
        "Who is eligible for group personal accident insurance?",
        "What are the benefit amounts under the accident insurance policy?",
    ],
    "Group Term Life Insurance Policy": [
        "What life insurance does Arvind provide to employees?",
        "How much does my family receive if I die while employed?",
        "How do I nominate my spouse as beneficiary for life insurance?",
        "Is the life insurance premium paid by Arvind or the employee?",
        "What documents are needed to file a death claim under GTL?",
        "What is the GTL sum insured for my grade?",
        "How is the term life insurance benefit calculated?",
        "Is the GTL premium paid by the employee or by Arvind?",
        "What documents are needed to file a GTL death claim?",
        "How is the GTL death benefit calculated?",
        "How do I nominate a beneficiary under Group Term Life Insurance?",
        "What is the sum insured under Group Term Life Insurance?",
        "Who is eligible for group term life insurance at Arvind?",
        "What are the steps to file a life insurance claim?",
    ],
    "Voluntary Death Contribution Policy": [
        "What is the voluntary death contribution scheme at Arvind?",
        "How much do employees contribute when a colleague passes away?",
        "Who receives the VDC benefit amount?",
        "Is VDC mandatory for all employees?",
        "Can I opt out of the death contribution scheme?",
        "What is the process to claim VDC benefit for a deceased employee?",
        "What is the Voluntary Death Contribution scheme?",
        "How much do employees contribute under VDC?",
        "Who receives VDC benefits when an employee passes away?",
        "Is VDC contribution compulsory for all employees at Arvind?",
        "Can an employee opt out of the VDC scheme?",
        "What is the amount contributed by employees under VDC?",
        "Who is eligible for VDC benefits at Arvind?",
    ],
    "Pankh Employee Referral Policy": [
        "How much do I get for referring a female candidate to Arvind?",
        "What is the Pankh referral bonus amount?",
        "How and when is the referral bonus paid?",
        "Can I refer someone outside the company for a job?",
        "Is there a bonus for referring a transgender candidate?",
        "What is the Pankh employee referral programme?",
        "What is the Pankh Employee Referral Programme at Arvind?",
        "Are transgender referrals eligible for bonus under Pankh?",
        "How many tranches is the Pankh referral bonus paid in?",
        "What is the referral bonus for referring a female candidate under Pankh?",
        "Who is eligible for the Pankh referral bonus?",
        "What are the steps to refer a candidate under the Pankh programme?",
    ],
    "Talent Mobility Policy": [
        "How do I apply for an internal job transfer at Arvind?",
        "What is the minimum tenure to apply for an internal role?",
        "Can my manager stop me from moving to another department?",
        "What is the IJP or internal job posting process?",
        "Who approves exceptions to the talent mobility policy?",
        "What is the mobility adjustment benefit?",
        "How do I apply for a lateral move within Arvind?",
        "What is the minimum tenure to apply for an internal job posting?",
        "Can a manager block an employee's mobility application?",
        "Who approves exceptions to the Talent Mobility Policy?",
        "What is the mobility adjustment amount under talent mobility?",
        "Who is eligible to apply for an internal transfer at Arvind?",
        "What are the steps to apply for internal job posting?",
    ],
    "MediBuddy User Guide": [
        "How do I register on the MediBuddy app?",
        "How do I consult a doctor online through MediBuddy?",
        "Is MediBuddy Gold free for Arvind employees?",
        "What services are covered under MediBuddy Gold?",
        "How do I book a teleconsultation on MediBuddy?",
        "What is the MediBuddy customer care number?",
        "Can I book a diagnostic test through MediBuddy?",
        "What is MediBuddy Gold for Arvind employees?",
        "Who is covered under MediBuddy Gold at Arvind?",
        "What is the MediBuddy helpline number?",
        "What are the steps to register on the MediBuddy app?",
        "Who is eligible for MediBuddy Gold at Arvind?",
    ],
    "Travel Settlement Guide": [
        "How do I submit my travel expenses after returning from a trip?",
        "What is the deadline to claim travel settlement at Arvind?",
        "How do I use the MyTour dashboard to file travel claims?",
        "What happens if I miss the 15-day travel expense submission deadline?",
        "What is the auto-settlement rule on day 16?",
        "What documents do I need to attach for travel settlement?",
        "How do I submit hotel and flight bills on the travel portal?",
        "How do I submit expenses on the MyTour Dashboard?",
        "What documents are required for travel settlement at Arvind?",
        "What is the deadline to submit travel expense claims?",
        "What is the auto-settlement policy on day 16 of travel settlement?",
        "What happens if I miss the 15-day expense submission deadline?",
        "Who is eligible to submit travel expense claims?",
        "What are the steps to file a travel expense claim on MyTour?",
    ],
    "1to1 Employee Assistance Program": [
        "Is there a counselling service available for Arvind employees?",
        "How do I contact the employee assistance helpline?",
        "Is the EAP service free and confidential?",
        "Can my family members use the EAP counselling?",
        "What is the 1to1 EAP helpline number?",
        "I am feeling stressed at work, who can I talk to at Arvind?",
        "Does using EAP get reported to my manager?",
        "What is the Employee Assistance Program at Arvind?",
        "Is the 1to1 EAP service free and confidential for employees?",
        "How do I contact the 1to1 EAP helpline?",
        "Can family members use the EAP counselling service?",
        "Who is eligible for the Employee Assistance Program at Arvind?",
        "What are the services available under the EAP program?",
    ],
}

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------
_ef = None
_anchor_matrix: dict[str, np.ndarray] = {}   # policy → (n_anchors, dim)
_router_col    = None   # ChromaDB synthetic-anchor collection
_router_loaded = False  # whether we've tried loading it


def _get_ef():
    global _ef
    if _ef is None:
        _ef = embedding_functions.ONNXMiniLM_L6_V2()
    return _ef


def _load_anchors():
    global _anchor_matrix
    if _anchor_matrix:
        return
    ef = _get_ef()
    for policy, anchors in POLICY_ANCHORS.items():
        vecs = ef(anchors)
        _anchor_matrix[policy] = np.array(vecs, dtype=np.float32)


def _get_router_col():
    """Lazy-load the synthetic router index. Returns None if not built yet."""
    global _router_col, _router_loaded
    if _router_loaded:
        return _router_col
    _router_loaded = True
    try:
        import chromadb
        client      = chromadb.PersistentClient(path=os.path.abspath(_VS_DIR))
        ef          = _get_ef()
        _router_col = client.get_collection(_ROUTER_COL, embedding_function=ef)
    except Exception:
        _router_col = None
    return _router_col


def _cosine_to_matrix(q_vec: np.ndarray, mat: np.ndarray) -> np.ndarray:
    """Return cosine similarity between q_vec and every row in mat."""
    norms = np.linalg.norm(mat, axis=1)
    norms = np.where(norms == 0, 1e-9, norms)
    q_norm = float(np.linalg.norm(q_vec)) or 1e-9
    return (mat @ q_vec) / (norms * q_norm)


def route_via_router_index(query: str) -> tuple[str | None, float]:
    """
    Tier-1 semantic routing: query the synthetic anchor ChromaDB collection.

    Returns (policy_label, confidence) where confidence = 1 - cosine_distance.
    Uses top-3 majority vote for robustness against individual false positives.
    Returns (None, score) when index not built or confidence < THRESHOLD.
    """
    col = _get_router_col()
    if col is None or col.count() == 0:
        return None, 0.0

    k = min(5, col.count())
    results = col.query(
        query_texts=[query],
        n_results=k,
        include=["metadatas", "distances"],
    )

    if not results["metadatas"] or not results["metadatas"][0]:
        return None, 0.0

    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # Top-1 confidence (ChromaDB cosine distance: 0=identical, 1=orthogonal)
    top_confidence = 1.0 - float(distances[0])

    # Majority vote from top-3 (ties broken by highest confidence)
    from collections import Counter
    top3_policies = [m["policy"] for m in metadatas[:3]]
    votes = Counter(top3_policies)
    top_policy = votes.most_common(1)[0][0]

    if top_confidence >= THRESHOLD:
        return top_policy, top_confidence
    return None, top_confidence


def detect_policy_semantic(query: str) -> tuple[str | None, float]:
    """
    Return (best_policy_label, confidence_score).
    Returns (None, 0.0) if confidence < THRESHOLD.
    """
    _load_anchors()
    ef = _get_ef()
    q_vec = np.array(ef([query])[0], dtype=np.float32)

    best_policy, best_score = None, 0.0
    for policy, mat in _anchor_matrix.items():
        sims = _cosine_to_matrix(q_vec, mat)
        score = float(sims.max())       # best single-anchor match
        if score > best_score:
            best_score, best_policy = score, policy

    if best_score >= THRESHOLD:
        return best_policy, best_score
    return None, best_score


def detect_top2_semantic(query: str) -> list[tuple[str, float]]:
    """
    Return the top-2 (policy_label, score) candidates sorted by confidence.
    Always returns scores regardless of THRESHOLD — caller decides what to do.
    """
    _load_anchors()
    ef = _get_ef()
    q_vec = np.array(ef([query])[0], dtype=np.float32)

    all_scores: list[tuple[str, float]] = []
    for policy, mat in _anchor_matrix.items():
        sims = _cosine_to_matrix(q_vec, mat)
        all_scores.append((policy, float(sims.max())))

    return sorted(all_scores, key=lambda x: -x[1])[:2]
