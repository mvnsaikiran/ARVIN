"""
Semantic policy router.

Pre-computes ONNX embeddings for 6-8 representative "intent anchor"
questions per policy at first call, then routes incoming queries by
cosine similarity — no keyword matching needed.

Hybrid strategy used by router.py:
  1. If keyword count >= 1 → keyword result (fast, high-confidence)
  2. Else if best semantic similarity >= THRESHOLD → semantic result
  3. Else → None (OOS / unrecognised)
"""

import numpy as np
from chromadb.utils import embedding_functions

THRESHOLD = 0.55   # min cosine similarity to claim a policy match

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
    ],
    "POSH Policy": [
        "I am being harassed at work, what should I do?",
        "How do I file a sexual harassment complaint?",
        "Who is on the anti-harassment committee at Arvind?",
        "How long does the POSH inquiry take?",
        "What action is taken after a harassment complaint is filed?",
        "What counts as sexual harassment under the POSH policy?",
        "Can I file a complaint against a colleague for harassment?",
    ],
    "Grievance Mechanism Policy": [
        "I have a complaint about my manager, what should I do?",
        "How do I raise a workplace grievance at Arvind?",
        "What is the escalation process for unresolved complaints?",
        "Who handles the first level of grievance resolution?",
        "What is the timeline to resolve a grievance?",
        "Can I raise a grievance about unfair treatment?",
        "How do I formally complain about a workplace issue?",
    ],
    "Gender Policy": [
        "Is there a policy protecting LGBTQ employees at Arvind?",
        "What is Arvind's stance on gender equality?",
        "How do I report gender-based discrimination?",
        "Are transgender employees protected under any policy?",
        "What is the gender sensitisation programme at Arvind?",
        "Does Arvind have an equal opportunity policy for women?",
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
    ],
    "Full & Final Settlement Policy": [
        "How long does full and final settlement take after resignation?",
        "What is deducted if I do not serve my full notice period?",
        "How is earned leave encashed when I leave the company?",
        "When will I receive my relieving letter?",
        "What components are included in the FnF payment?",
        "How do I clear my dues and get the no-dues certificate?",
        "What is the FnF process when I resign from Arvind?",
    ],
    "Employee Expense Reimbursement Policy": [
        "How do I claim reimbursement for a birthday celebration expense?",
        "What is the deadline to submit expense claims?",
        "Who approves my expense reimbursement at Arvind?",
        "What receipts are required for expense claims?",
        "Can I claim for car maintenance or fuel expenses?",
        "Is there a puja or farewell expense reimbursement at Arvind?",
    ],
    "Local Conveyance Policy": [
        "What is the per km rate for using my personal vehicle for office work?",
        "Can I claim Ola or Uber rides for local office travel?",
        "Is home to office commute reimbursable at Arvind?",
        "What is the monthly cap on local conveyance claims?",
        "How do I submit a local conveyance claim?",
        "What is the cab allowance for field visits within the city?",
    ],
    "Group Health Insurance Policy": [
        "What is my health insurance coverage at Arvind?",
        "Are my parents covered under the company health insurance?",
        "What is the room rent limit for hospitalisation?",
        "How do I make a cashless health insurance claim?",
        "What is the sum insured under the group mediclaim?",
        "What is the FHPL helpline number for health claims?",
        "Are pre-existing diseases covered under Arvind health insurance?",
    ],
    "Group Personal Accident Insurance Policy": [
        "What insurance do I get if I meet with an accident?",
        "What is the compensation for permanent disability due to an accident?",
        "Is accidental death covered by Arvind's insurance?",
        "What percentage is paid for partial disability?",
        "Does the accident insurance cover me during personal time?",
        "How do I file a personal accident insurance claim?",
        "What is the GPA cover for loss of limb or eyesight?",
    ],
    "Group Term Life Insurance Policy": [
        "What life insurance does Arvind provide to employees?",
        "How much does my family receive if I die while employed?",
        "How do I nominate my spouse as beneficiary for life insurance?",
        "Is the life insurance premium paid by Arvind or the employee?",
        "What documents are needed to file a death claim under GTL?",
        "What is the GTL sum insured for my grade?",
        "How is the term life insurance benefit calculated?",
    ],
    "Voluntary Death Contribution Policy": [
        "What is the voluntary death contribution scheme at Arvind?",
        "How much do employees contribute when a colleague passes away?",
        "Who receives the VDC benefit amount?",
        "Is VDC mandatory for all employees?",
        "Can I opt out of the death contribution scheme?",
        "What is the process to claim VDC benefit for a deceased employee?",
    ],
    "Pankh Employee Referral Policy": [
        "How much do I get for referring a female candidate to Arvind?",
        "What is the Pankh referral bonus amount?",
        "How and when is the referral bonus paid?",
        "Can I refer someone outside the company for a job?",
        "Is there a bonus for referring a transgender candidate?",
        "What is the Pankh employee referral programme?",
    ],
    "Talent Mobility Policy": [
        "How do I apply for an internal job transfer at Arvind?",
        "What is the minimum tenure to apply for an internal role?",
        "Can my manager stop me from moving to another department?",
        "What is the IJP or internal job posting process?",
        "Who approves exceptions to the talent mobility policy?",
        "What is the mobility adjustment benefit?",
        "How do I apply for a lateral move within Arvind?",
    ],
    "MediBuddy User Guide": [
        "How do I register on the MediBuddy app?",
        "How do I consult a doctor online through MediBuddy?",
        "Is MediBuddy Gold free for Arvind employees?",
        "What services are covered under MediBuddy Gold?",
        "How do I book a teleconsultation on MediBuddy?",
        "What is the MediBuddy customer care number?",
        "Can I book a diagnostic test through MediBuddy?",
    ],
    "Travel Settlement Guide": [
        "How do I submit my travel expenses after returning from a trip?",
        "What is the deadline to claim travel settlement at Arvind?",
        "How do I use the MyTour dashboard to file travel claims?",
        "What happens if I miss the 15-day travel expense submission deadline?",
        "What is the auto-settlement rule on day 16?",
        "What documents do I need to attach for travel settlement?",
        "How do I submit hotel and flight bills on the travel portal?",
    ],
    "1to1 Employee Assistance Program": [
        "Is there a counselling service available for Arvind employees?",
        "How do I contact the employee assistance helpline?",
        "Is the EAP service free and confidential?",
        "Can my family members use the EAP counselling?",
        "What is the 1to1 EAP helpline number?",
        "I am feeling stressed at work, who can I talk to at Arvind?",
        "Does using EAP get reported to my manager?",
    ],
}

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------
_ef = None
_anchor_matrix: dict[str, np.ndarray] = {}   # policy → (n_anchors, dim)


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


def _cosine_to_matrix(q_vec: np.ndarray, mat: np.ndarray) -> np.ndarray:
    """Return cosine similarity between q_vec and every row in mat."""
    norms = np.linalg.norm(mat, axis=1)
    norms = np.where(norms == 0, 1e-9, norms)
    q_norm = float(np.linalg.norm(q_vec)) or 1e-9
    return (mat @ q_vec) / (norms * q_norm)


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
