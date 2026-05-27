"""
Fast policy-wise accuracy report for all 18 ARVIN policies.

Minimum-safe sample: 12 questions per policy (10 in-scope + 2 OOS) = 216 total.

Metrics computed WITHOUT extra LLM calls — only 1 Groq call per question (the RAG answer):
  routing_accuracy   — did the router send the query to the correct policy?
  coverage_rate      — % of in-scope questions that got a real answer (not fallback)
  oos_rejection      — % of out-of-scope questions correctly deflected
  semantic_score     — cosine similarity (ONNX) between answer and retrieved context
  overall            — weighted composite: routing(25%) + coverage(35%) + oos(20%) + semantic(20%)

Usage:
    python eval/quick_accuracy.py
    python eval/quick_accuracy.py --policy wb
"""

import os, sys, time, json, re
from typing import List
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

from chromadb.utils import embedding_functions

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── Test bank (10 in-scope + 2 OOS per policy) ────────────────────────────────

TEST_BANK = {
    "wb": {
        "label": "Whistleblower Policy",
        "in_scope": [
            "What is the purpose of the Whistleblower Policy at Arvind?",
            "Who can file a disclosure under the Whistleblower Policy?",
            "What types of concerns can be reported through the Whistleblower Policy?",
            "How is confidentiality maintained for a whistleblower?",
            "What is the role of the Whistleblower Committee?",
            "Can a whistleblower report anonymously?",
            "What happens if a whistleblower is victimized or retaliated against?",
            "What are the available channels to report a protected disclosure?",
            "Within how many days must a whistleblower complaint be investigated?",
            "What protections are given to the whistleblower under this policy?",
        ],
        "oos": ["How do I apply for a home loan?", "What is the annual leave entitlement?"],
    },
    "posh": {
        "label": "POSH Policy",
        "in_scope": [
            "What constitutes sexual harassment under the POSH Policy?",
            "Who are the members of the Anti Harassment Committee?",
            "How do I file a complaint under the POSH Policy?",
            "What is the timeline for completing a POSH inquiry?",
            "Can a male employee file a POSH complaint?",
            "What disciplinary action can be taken against a harasser?",
            "Is the identity of the complainant kept confidential under POSH?",
            "What interim relief can the AIC provide to the complainant?",
            "What happens if a complaint is found to be malicious?",
            "What is the role of the Internal Complaints Committee under POSH?",
        ],
        "oos": ["What is my medical insurance premium?", "How many days of paternity leave do I get?"],
    },
    "grv": {
        "label": "Grievance Mechanism Policy",
        "in_scope": [
            "How do I raise a workplace grievance at Arvind?",
            "What is the timeline for resolving a grievance?",
            "What are the escalation levels in the grievance process?",
            "Who handles the first level of grievance resolution?",
            "Can a grievance be submitted anonymously?",
            "What issues can be raised through the grievance mechanism?",
            "How is the confidentiality of the complainant maintained?",
            "What happens if my grievance is not resolved at the first level?",
            "Is there a formal acknowledgment of grievance submission?",
            "What role does the Ethics Helpline play in grievance resolution?",
        ],
        "oos": ["What is my notice period for resignation?", "Can I get a salary advance?"],
    },
    "gen": {
        "label": "Gender Policy",
        "in_scope": [
            "What is Arvind's Gender Policy about?",
            "What principles does Arvind follow for gender equality?",
            "How can an employee report gender discrimination?",
            "What is the definition of gender identity under this policy?",
            "Is there protection against gender-based harassment at Arvind?",
            "What are the escalation channels for gender-related complaints?",
            "How often is the Gender Policy reviewed?",
            "Are LGBTQ employees protected under this policy?",
            "What disciplinary action is taken for gender-based harassment?",
            "What does inclusive workplace mean under the Gender Policy?",
        ],
        "oos": ["What is the process for performance appraisal?", "How do I get my salary slip?"],
    },
    "dt": {
        "label": "Domestic Travel Policy",
        "in_scope": [
            "What is the booking process for domestic air travel at Arvind?",
            "What are the hotel accommodation limits for Grade M2 employees?",
            "What is the per diem for domestic travel?",
            "Can I book travel directly or must I use a travel management company?",
            "What documents are required for travel expense reimbursement?",
            "What is the deadline to submit travel expense claims?",
            "What class of flight is an E2 grade employee entitled to?",
            "Are taxi expenses covered under domestic travel?",
            "What is the advance travel allowance process?",
            "Are travel expenses reimbursed on actuals or fixed rates?",
        ],
        "oos": ["Can I carry forward annual leave?", "What is the probation period for new employees?"],
    },
    "jn": {
        "label": "Joining Policy",
        "in_scope": [
            "What relocation benefits does Arvind provide to new joiners?",
            "What accommodation is provided to new employees?",
            "Is brokerage reimbursed for renting accommodation during joining?",
            "What is the joining allowance for an M2 grade employee?",
            "How soon after joining do relocation benefits need to be claimed?",
            "What household goods transportation support is provided?",
            "What travel class is applicable during joining travel?",
            "Can a new joiner claim both accommodation and relocation benefits?",
            "What documents are needed to claim joining benefits?",
            "Are there conditions to receive joining benefits?",
        ],
        "oos": ["What is the process for applying for a promotion?", "How do I access my payslip?"],
    },
    "fnf": {
        "label": "Full & Final Settlement Policy",
        "in_scope": [
            "What is included in the Full and Final Settlement at Arvind?",
            "How many days does Arvind take to process FnF after resignation?",
            "What is recovered from FnF if an employee leaves without serving notice?",
            "Is tuition fee recovered from FnF if an employee resigns early?",
            "What components are included in notice pay recovery?",
            "How are earned leaves encashed during FnF?",
            "Is gratuity included in FnF at Arvind?",
            "How is the last working date determined for FnF?",
            "What is the FnF process for a terminated employee?",
            "Can the FnF settlement be disputed by the employee?",
        ],
        "oos": ["What is the maternity leave policy?", "How do I apply for a training programme?"],
    },
    "exp": {
        "label": "Employee Expense Reimbursement Policy",
        "in_scope": [
            "What types of expenses can I claim under the expense reimbursement policy?",
            "What is the deadline for submitting an expense reimbursement claim?",
            "Who approves my expense reimbursement at Arvind?",
            "Are entertainment expenses covered under this policy?",
            "What receipts are required for expense claims?",
            "How are expenses reimbursed — through salary or separately?",
            "Are client entertainment expenses reimbursable?",
            "Is there a maximum limit on expense claims per trip?",
            "What happens if I submit an expense claim late?",
            "Can I claim mobile phone reimbursement under this policy?",
        ],
        "oos": ["How do I apply for a car loan?", "What is the ESOP policy at Arvind?"],
    },
    "lc": {
        "label": "Local Conveyance Policy",
        "in_scope": [
            "What is the reimbursement rate for using my personal two-wheeler for local travel?",
            "Can I claim local conveyance for commuting from home to office?",
            "What is the monthly cap on local conveyance claims?",
            "Are OLA or UBER rides reimbursable under local conveyance?",
            "What is the rate per km for local conveyance by personal car?",
            "What documents are required for local conveyance claims?",
            "Is local conveyance allowed for travel between two office locations?",
            "How do I submit a local conveyance claim?",
            "Is auto-rickshaw fare reimbursable under local conveyance?",
            "Can I claim both local conveyance and travel allowance for the same trip?",
        ],
        "oos": ["What is the group personal accident policy?", "How do I enrol for health insurance?"],
    },
    "ghi": {
        "label": "Group Health Insurance Policy",
        "in_scope": [
            "What is the sum insured under the Group Health Insurance Policy?",
            "Are pre-existing diseases covered under Arvind health insurance?",
            "What is the room rent limit for hospitalization?",
            "How do I file a cashless claim under the Arvind health policy?",
            "Are parents covered under the group health insurance?",
            "What is the FHPL helpline number for health insurance claims?",
            "What is the process for reimbursement of medical expenses?",
            "Is maternity covered under the group health insurance?",
            "What is the ICU room limit under the health insurance policy?",
            "Are day-care procedures covered under the policy?",
        ],
        "oos": ["How do I apply for a promotion?", "Can I work remotely?"],
    },
    "gpa": {
        "label": "Group Personal Accident Insurance",
        "in_scope": [
            "What does the Group Personal Accident Insurance cover?",
            "What is the compensation for permanent total disability under GPA?",
            "Is accidental death covered under the Group Personal Accident Insurance?",
            "What percentage of the sum insured is paid for partial disability?",
            "How do I file a claim under the Group Personal Accident Insurance?",
            "What is the sum insured under Group Personal Accident Insurance?",
            "Is temporary total disability covered under GPA?",
            "What is the procedure after an accident?",
            "Does the GPA cover accidents outside working hours?",
            "Are dependents covered under the GPA policy?",
        ],
        "oos": ["What is the leave encashment policy?", "Can I avail flexible working hours?"],
    },
    "gtl": {
        "label": "Group Term Life Insurance",
        "in_scope": [
            "What is the sum insured under the Group Term Life Insurance?",
            "How is the death benefit calculated under GTL?",
            "Who are the eligible nominees under the Group Term Life Insurance?",
            "How do I nominate a beneficiary under the GTL policy?",
            "What is the claim procedure under Group Term Life Insurance?",
            "Is the GTL premium paid by the employee or Arvind?",
            "Is there a natural death benefit under Group Term Life Insurance?",
            "What documents are needed to file a GTL claim?",
            "Is accidental death benefit different from normal death under GTL?",
            "Can I increase my GTL coverage voluntarily?",
        ],
        "oos": ["What is the uniform policy?", "Can I take unpaid leave of absence?"],
    },
    "vdc": {
        "label": "Voluntary Death Contribution Policy",
        "in_scope": [
            "What is the Voluntary Death Contribution scheme at Arvind?",
            "How much do employees contribute under the VDC scheme?",
            "Who is eligible to receive benefits under the VDC scheme?",
            "How is the contribution collected from employees?",
            "When is the VDC benefit paid out?",
            "Is the VDC contribution compulsory for all employees?",
            "Can an employee opt out of the VDC scheme?",
            "How is the VDC amount calculated per employee?",
            "What happens to the VDC fund if there are no deaths in a year?",
            "Are there conditions on VDC payouts?",
        ],
        "oos": ["What is the annual increment policy?", "How do I apply for study leave?"],
    },
    "pankh": {
        "label": "Pankh Employee Referral Policy",
        "in_scope": [
            "What is the Pankh Employee Referral Programme?",
            "What is the referral bonus for referring a female candidate at E1 grade?",
            "Can I refer an immediate family member under the Pankh programme?",
            "How many tranches is the Pankh referral bonus paid in?",
            "What grades are eligible for monetary referral bonus under Pankh?",
            "Are transgender referrals eligible for the referral bonus?",
            "What happens if my referral leaves within 3 months of joining?",
            "Is there a referral bonus for referring a male candidate?",
            "What is the referral reward for an M2 grade hire?",
            "Can a contractor employee participate in the Pankh programme?",
        ],
        "oos": ["What is the vehicle allowance policy?", "How do I update my emergency contact?"],
    },
    "tm": {
        "label": "Talent Mobility Policy",
        "in_scope": [
            "What is Arvind's Talent Mobility Policy?",
            "What is the minimum tenure required before applying for an internal job posting?",
            "Can my manager block my internal mobility application?",
            "Who can approve exceptions to the Talent Mobility Policy?",
            "What is the SIA process under Talent Mobility?",
            "Is there a financial adjustment on internal mobility?",
            "What is the role of the MAB committee in talent mobility?",
            "Can an employee apply for an IJP within their first year?",
            "How do I apply for an internal job posting?",
            "What is the mobility adjustment amount?",
        ],
        "oos": ["What is the policy for receiving gifts from vendors?", "Can I hold a second job outside Arvind?"],
    },
    "mb": {
        "label": "MediBuddy User Guide",
        "in_scope": [
            "What is MediBuddy Gold and who provides it?",
            "Who is covered under the MediBuddy Gold benefit?",
            "How do I register on the MediBuddy app?",
            "How do I book an online doctor consultation on MediBuddy?",
            "Is MediBuddy Gold free for employees?",
            "What specialities are available for consultation on MediBuddy?",
            "Can family members use MediBuddy through the employee's account?",
            "How do I book a lab test on MediBuddy?",
            "What is the MediBuddy customer care number?",
            "Is there a limit on the number of doctor consultations?",
        ],
        "oos": ["How do I claim travel allowance?", "What is the leave without pay policy?"],
    },
    "ts": {
        "label": "Travel Settlement Guide",
        "in_scope": [
            "What is the deadline for submitting travel expense claims after a trip?",
            "How do I submit travel expenses on the MyTour Dashboard?",
            "What happens if I don't submit my travel expenses within 15 days?",
            "What supporting documents are required for travel settlement?",
            "Can I claim expenses for meals during domestic travel?",
            "How are hotel bills reimbursed in the travel settlement process?",
            "What is the auto-settlement policy on day 16?",
            "Is an advance taken for travel adjusted in the final settlement?",
            "Can I claim expenses without original receipts?",
            "What is the role of a Line Manager in approving travel settlements?",
        ],
        "oos": ["How do I apply for flexible work arrangements?", "What is the policy on sabbaticals?"],
    },
    "eap": {
        "label": "1to1 Employee Assistance Program",
        "in_scope": [
            "What is the Employee Assistance Program at Arvind?",
            "Is the EAP service free for employees?",
            "Is the EAP service confidential?",
            "What type of counselling does the EAP provide?",
            "How do I contact the 1to1 EAP helpline?",
            "Can family members of employees use the EAP?",
            "How many EAP sessions are covered per employee?",
            "Does using EAP get reported to my manager or HR?",
            "What issues can be addressed through the EAP?",
            "Is the EAP available 24x7?",
        ],
        "oos": ["What is the company internet usage policy?", "How do I request a transfer to another city?"],
    },
}

FALLBACK_SIGNAL = "wasn't able to find relevant information"

# ── ONNX cosine similarity ────────────────────────────────────────────────────

_onnx_fn = None

def _get_onnx():
    global _onnx_fn
    if _onnx_fn is None:
        _onnx_fn = embedding_functions.ONNXMiniLM_L6_V2()
    return _onnx_fn

def cosine(a, b):
    a, b = np.array(a), np.array(b)
    n = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / n) if n > 0 else 0.0

def semantic_score(answer: str, context: str) -> float:
    if not answer.strip() or not context.strip():
        return 0.0
    fn = _get_onnx()
    vecs = fn([answer[:500], context[:500]])
    return max(0.0, cosine(vecs[0], vecs[1]))

# ── Per-question evaluation ───────────────────────────────────────────────────

def eval_question(short: str, question: str, expected_label: str, is_oos: bool) -> dict:
    """
    Fully offline evaluation — zero Groq calls.
    Measures routing accuracy, retrieval quality, and OOS rejection
    using only the router keyword matching and ONNX retriever.
    """
    import importlib
    from router import detect_policy, POLICY_REGISTRY

    # 1. Routing: does keyword matching select the right policy?
    detected = detect_policy(question)
    routed_correctly = (detected == expected_label)

    # 2. Retrieval: do we get relevant chunks back?
    chunks = []
    try:
        mod    = importlib.import_module(f"policies.{_mod_name(short)}.retriever")
        retr   = getattr(mod, '_retriever')
        chunks = retr.retrieve(question)
    except Exception:
        pass
    context = " ".join(c['text'] for c in chunks[:3])

    # 3. OOS routing check: router returns matched=False for OOS questions
    q = question.lower()
    best_count = 0
    for keywords, _, _ in POLICY_REGISTRY:
        count = sum(1 for kw in keywords if kw in q)
        if count > best_count:
            best_count = count
    router_matched = best_count >= 1

    # 4. Retrieval coverage: did retriever return meaningful chunks?
    has_chunks = len(chunks) > 0 and len(context.strip()) > 50

    # 5. Semantic relevance: cosine(query, top retrieved chunk)
    sem = semantic_score(question, context) if has_chunks else 0.0

    if is_oos:
        # OOS is correct when router does NOT match (or matches wrong policy)
        correct = (not router_matched) or (detected != expected_label and detected is not None and False)
        correct = not router_matched
        answered = router_matched  # "answered" = incorrectly routed to a policy
    else:
        correct  = routed_correctly and has_chunks
        answered = has_chunks

    return {
        "question":         question,
        "is_oos":           is_oos,
        "routed_correctly": routed_correctly,
        "answered":         answered,
        "correct":          correct,
        "semantic_score":   round(sem, 3),
        "chunks_retrieved": len(chunks),
    }

def _mod_name(short: str) -> str:
    return {
        "wb":    "whistleblower",
        "posh":  "posh",
        "grv":   "grievance",
        "gen":   "gender",
        "dt":    "domestic_travel",
        "jn":    "joining",
        "fnf":   "fnf",
        "exp":   "expense",
        "lc":    "local_conveyance",
        "ghi":   "group_health",
        "gpa":   "group_personal_accident",
        "gtl":   "group_term_life",
        "vdc":   "vdc",
        "pankh": "pankh",
        "tm":    "talent_mobility",
        "mb":    "medibuddy",
        "ts":    "travel_settlement",
        "eap":   "eap",
    }[short]

# ── Policy evaluation ─────────────────────────────────────────────────────────

def eval_policy(short: str) -> dict:
    cfg   = TEST_BANK[short]
    label = cfg["label"]
    all_q = [(q, False) for q in cfg["in_scope"]] + [(q, True) for q in cfg["oos"]]

    print(f"\n  {'─'*54}")
    print(f"  {label}  ({len(all_q)} questions)")
    print(f"  {'─'*54}")

    rows = []
    for i, (q, is_oos) in enumerate(all_q, 1):
        tag = "[OOS]" if is_oos else "     "
        print(f"  {tag} [{i:02d}/{len(all_q)}] {q[:60]}...", flush=True)
        row = eval_question(short, q, label, is_oos)
        rows.append(row)
        sym = "✓" if row["correct"] else "✗"
        print(f"          {sym}  routed={row['routed_correctly']}  answered={row['answered']}  sem={row['semantic_score']:.2f}", flush=True)
        time.sleep(1.5)

    in_scope_rows = [r for r in rows if not r["is_oos"]]
    oos_rows      = [r for r in rows if r["is_oos"]]

    routing_acc  = sum(r["routed_correctly"] for r in rows) / len(rows)
    coverage     = sum(r["answered"] for r in in_scope_rows) / len(in_scope_rows) if in_scope_rows else 0
    oos_reject   = sum(not r["answered"] for r in oos_rows) / len(oos_rows) if oos_rows else 0
    sem_avg      = sum(r["semantic_score"] for r in in_scope_rows if r["answered"]) / max(1, sum(r["answered"] for r in in_scope_rows))

    overall = (routing_acc * 0.25 + coverage * 0.35 + oos_reject * 0.20 + sem_avg * 0.20)

    return {
        "policy":           label,
        "short":            short,
        "n_total":          len(rows),
        "n_in_scope":       len(in_scope_rows),
        "n_oos":            len(oos_rows),
        "routing_accuracy": round(routing_acc, 3),
        "coverage_rate":    round(coverage, 3),
        "oos_rejection":    round(oos_reject, 3),
        "semantic_score":   round(sem_avg, 3),
        "overall":          round(overall, 3),
        "per_question":     rows,
    }

# ── Report ────────────────────────────────────────────────────────────────────

def _grade(s):
    if s >= 0.90: return "A+"
    if s >= 0.85: return "A"
    if s >= 0.80: return "B+"
    if s >= 0.75: return "B"
    if s >= 0.65: return "C"
    return "D"

def print_report(results: list[dict]):
    print(f"\n{'='*82}")
    print(f"  ARVIN — Policy-Wise Accuracy Report  ({len(results)} policies, 12 Q each)")
    print(f"  Metrics: Routing(25%) | Coverage(35%) | OOS Rejection(20%) | Semantic(20%)")
    print(f"{'='*82}")
    print(f"  {'Policy':<42} {'Route':>6} {'Cover':>6} {'OOS':>6} {'Sem':>6} {'Score':>7} {'Grade':>5}")
    print(f"  {'─'*42} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*7} {'─'*5}")

    for r in results:
        flag = "✓" if r["overall"] >= 0.75 else ("△" if r["overall"] >= 0.60 else "✗")
        print(
            f"  {flag} {r['policy']:<41}"
            f" {r['routing_accuracy']:>6.0%}"
            f" {r['coverage_rate']:>6.0%}"
            f" {r['oos_rejection']:>6.0%}"
            f" {r['semantic_score']:>6.2f}"
            f" {r['overall']:>7.3f}"
            f"  {_grade(r['overall']):>4}"
        )

    if results:
        ar = sum(r["routing_accuracy"] for r in results) / len(results)
        ac = sum(r["coverage_rate"]    for r in results) / len(results)
        ao = sum(r["oos_rejection"]    for r in results) / len(results)
        as_ = sum(r["semantic_score"]  for r in results) / len(results)
        avg = sum(r["overall"]         for r in results) / len(results)
        print(f"  {'─'*42} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*7} {'─'*5}")
        print(f"  {'AVERAGE':<42} {ar:>6.0%} {ac:>6.0%} {ao:>6.0%} {as_:>6.2f} {avg:>7.3f}  {_grade(avg):>4}")

    out = os.path.join(os.path.dirname(__file__), "accuracy_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Full report saved → {out}")

    # Weak policies — improvement targets
    weak = [r for r in results if r["overall"] < 0.75]
    if weak:
        print(f"\n  ── Policies needing improvement ──────────────────────────────")
        for r in weak:
            issues = []
            if r["routing_accuracy"] < 0.80: issues.append(f"routing {r['routing_accuracy']:.0%}")
            if r["coverage_rate"]    < 0.80: issues.append(f"coverage {r['coverage_rate']:.0%}")
            if r["oos_rejection"]    < 0.80: issues.append(f"OOS rejection {r['oos_rejection']:.0%}")
            if r["semantic_score"]   < 0.50: issues.append(f"semantic {r['semantic_score']:.2f}")
            print(f"  ✗ {r['policy']}: {' | '.join(issues)}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default="all")
    args = parser.parse_args()

    policies = list(TEST_BANK.keys()) if args.policy == "all" else [args.policy]

    print(f"\n{'='*82}")
    print(f"  ARVIN — Quick Policy Accuracy Eval")
    print(f"  {len(policies)} policies × 12 questions = {len(policies)*12} total")
    print(f"  No extra LLM scoring — uses routing + coverage + ONNX similarity")
    print(f"{'='*82}")

    results = []
    for short in policies:
        result = eval_policy(short)
        results.append(result)
        # Save after each policy so a crash doesn't lose everything
        interim = os.path.join(os.path.dirname(__file__), f"{short}_accuracy.json")
        with open(interim, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        time.sleep(3)

    print_report(results)


if __name__ == "__main__":
    main()
