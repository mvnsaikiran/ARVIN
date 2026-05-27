"""
Ragas evaluation for all 18 ARVIN policies.

Usage:
    python eval/ragas_eval.py                  # evaluate all policies
    python eval/ragas_eval.py --policy wb      # single policy by short code

Metrics (reference-free — no golden answers needed):
    faithfulness     — LLM answer is grounded in retrieved context (no hallucination)
    answer_relevancy — LLM answer addresses the actual question

LLM judge: Groq llama-3.3-70b-versatile (free tier) via OpenAI-compatible endpoint
Embeddings: sentence-transformers/all-MiniLM-L6-v2 (local)
"""

import os
import sys
import time
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))


# ── Ragas + LangChain wiring ─────────────────────────────────────────────────

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

def make_judge_llm():
    return ChatOpenAI(
        model="llama-3.3-70b-versatile",
        openai_api_key=GROQ_API_KEY,
        openai_api_base=GROQ_BASE_URL,
        temperature=0.0,
        max_tokens=1024,
        request_timeout=60,
    )

def make_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=GROQ_API_KEY,
        openai_api_base=GROQ_BASE_URL,
    )


# ── Per-policy test questions (10 in-scope + 2 OOS per policy) ───────────────

POLICY_TESTS = {
    "wb": {
        "label": "Whistleblower Policy",
        "questions": [
            "What is the purpose of the Whistleblower Policy at Arvind?",
            "Who can file a disclosure under the Whistleblower Policy?",
            "What types of concerns can be reported through the Whistleblower Policy?",
            "How is confidentiality maintained for a whistleblower?",
            "What is the role of the Whistleblower Committee?",
            "Can a whistleblower report anonymously?",
            "What happens if a whistleblower is victimized or retaliated against?",
            "What are the available channels to report a protected disclosure?",
            "Within how many days must a complaint under the whistleblower policy be investigated?",
            "What protections are given to the whistleblower under this policy?",
            # OOS
            "How do I apply for a home loan?",
            "What is the annual leave entitlement?",
        ],
    },
    "posh": {
        "label": "POSH Policy",
        "questions": [
            "What constitutes sexual harassment under the POSH Policy?",
            "Who are the members of the Anti Harassment Committee (AIC)?",
            "How do I file a complaint under the POSH Policy?",
            "What is the timeline for completing a POSH inquiry?",
            "Can a male employee file a POSH complaint?",
            "What is the role of the Internal Complaints Committee under POSH?",
            "What disciplinary action can be taken against a harasser?",
            "Is the identity of the complainant kept confidential under POSH?",
            "What interim relief can the AIC provide to the complainant?",
            "What happens if a complaint is found to be malicious or false?",
            # OOS
            "What is my medical insurance premium?",
            "How many days of paternity leave do I get?",
        ],
    },
    "grv": {
        "label": "Grievance Mechanism Policy",
        "questions": [
            "How do I raise a workplace grievance at Arvind?",
            "What is the timeline for resolving a grievance?",
            "What are the escalation levels in the grievance process?",
            "Who handles the first level of grievance resolution?",
            "Can a grievance be submitted anonymously?",
            "What issues can be raised through the grievance mechanism?",
            "How is the confidentiality of the complainant maintained?",
            "What happens if my grievance is not resolved at the first level?",
            "Is there a formal written acknowledgment of grievance submission?",
            "What role does the Ethics Helpline play in grievance resolution?",
            # OOS
            "What is my notice period for resignation?",
            "Can I get an advance on my salary?",
        ],
    },
    "gen": {
        "label": "Gender Policy",
        "questions": [
            "What is Arvind's Gender Policy about?",
            "What principles does Arvind follow for gender equality?",
            "How can an employee report gender discrimination?",
            "What is the definition of gender identity under this policy?",
            "Is there protection against gender-based harassment at Arvind?",
            "What are the escalation channels for gender-related complaints?",
            "How often is the Gender Policy reviewed?",
            "What does inclusive workplace mean under the Gender Policy?",
            "Are LGBTQ employees protected under this policy?",
            "What disciplinary action is taken for gender-based harassment?",
            # OOS
            "What is the process for performance appraisal?",
            "How do I get my salary slip?",
        ],
    },
    "dt": {
        "label": "Domestic Travel Policy",
        "questions": [
            "What is the booking process for domestic air travel at Arvind?",
            "What are the hotel accommodation limits for Grade M2 employees?",
            "What is the per diem (daily allowance) for domestic travel?",
            "Can I book travel directly or must I use a travel management company?",
            "What is the advance travel allowance process?",
            "Are travel expenses reimbursed on actuals or at fixed rates?",
            "What documents are required for travel expense reimbursement?",
            "What is the deadline to submit travel expense claims?",
            "What class of flight is an E2 grade employee entitled to?",
            "Are taxi expenses covered under domestic travel?",
            # OOS
            "Can I carry forward annual leave?",
            "What is the probation period for new employees?",
        ],
    },
    "jn": {
        "label": "Joining Policy",
        "questions": [
            "What relocation benefits does Arvind provide to new joiners?",
            "What accommodation is provided to new employees?",
            "Is brokerage reimbursed for renting accommodation during joining?",
            "What is the joining allowance for an M2 grade employee?",
            "How soon after joining do relocation benefits need to be claimed?",
            "What household goods transportation support is provided?",
            "Are there any conditions to receive joining benefits?",
            "What travel class is applicable during joining travel?",
            "Can a new joiner claim both accommodation and relocation benefits?",
            "What documents are needed to claim joining benefits?",
            # OOS
            "What is the process for applying for a promotion?",
            "How do I access my payslip on the HR portal?",
        ],
    },
    "fnf": {
        "label": "Full and Final Settlement Policy",
        "questions": [
            "What is included in the Full and Final Settlement at Arvind?",
            "How many days does Arvind take to process FnF after resignation?",
            "What is recovered from FnF if an employee leaves before notice period?",
            "Is tuition fee recovered from FnF if an employee resigns early?",
            "What components are included in notice pay recovery?",
            "How are earned leaves encashed during FnF?",
            "What is the FnF process for an employee who is terminated?",
            "Is gratuity included in FnF at Arvind?",
            "How is the last working date determined for FnF?",
            "Can the FnF be disputed by the employee?",
            # OOS
            "What is the maternity leave policy?",
            "How do I apply for a training programme?",
        ],
    },
    "exp": {
        "label": "Employee Expense Reimbursement Policy",
        "questions": [
            "What types of expenses can I claim under the expense reimbursement policy?",
            "What is the deadline for submitting an expense reimbursement claim?",
            "Who approves my expense reimbursement at Arvind?",
            "Are entertainment expenses covered under this policy?",
            "What receipts are required for expense claims?",
            "Is there a maximum limit on expense claims per trip?",
            "Can I claim mobile phone reimbursement under this policy?",
            "How are expenses reimbursed — through salary or separately?",
            "What happens if I submit an expense claim late?",
            "Are client entertainment expenses reimbursable?",
            # OOS
            "How do I apply for a car loan?",
            "What is the ESOP policy at Arvind?",
        ],
    },
    "lc": {
        "label": "Local Conveyance Policy",
        "questions": [
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
            # OOS
            "What is the group personal accident policy?",
            "How do I enrol for the employee health insurance?",
        ],
    },
    "ghi": {
        "label": "Group Health Insurance Policy",
        "questions": [
            "What is the sum insured under the Group Health Insurance Policy?",
            "Are pre-existing diseases covered under the Arvind health insurance?",
            "What is the room rent limit for hospitalization under health insurance?",
            "How do I file a cashless claim under the Arvind health policy?",
            "Are parents covered under the group health insurance?",
            "What is the FHPL helpline number for health insurance claims?",
            "What is the process for reimbursement of medical expenses?",
            "Is maternity covered under the group health insurance?",
            "What is the ICU room limit under the health insurance policy?",
            "Are day-care procedures covered under the policy?",
            # OOS
            "How do I apply for a promotion?",
            "Can I work remotely?",
        ],
    },
    "gpa": {
        "label": "Group Personal Accident Insurance",
        "questions": [
            "What does the Group Personal Accident Insurance cover?",
            "What is the compensation for permanent total disability under GPA?",
            "Is accidental death covered under the Group Personal Accident Insurance?",
            "What percentage of the sum insured is paid for partial disability?",
            "How do I file a claim under the Group Personal Accident Insurance?",
            "Are dependents covered under the GPA policy?",
            "What is the sum insured under Group Personal Accident Insurance?",
            "Is temporary total disability covered under GPA?",
            "What is the procedure after an accident — who do I notify?",
            "Does the GPA cover accidents outside working hours?",
            # OOS
            "What is the leave encashment policy?",
            "Can I avail flexible working hours?",
        ],
    },
    "gtl": {
        "label": "Group Term Life Insurance",
        "questions": [
            "What is the sum insured under the Group Term Life Insurance?",
            "How is the death benefit calculated under GTL?",
            "Who are the eligible nominees under the Group Term Life Insurance?",
            "How do I nominate a beneficiary under the GTL policy?",
            "What is the claim procedure under Group Term Life Insurance?",
            "Is the GTL premium paid by the employee or Arvind?",
            "Is there a natural death benefit under Group Term Life Insurance?",
            "Is accidental death benefit different from normal death under GTL?",
            "What documents are needed to file a GTL claim?",
            "Can I increase my GTL coverage voluntarily?",
            # OOS
            "What is the uniform policy?",
            "Can I take an unpaid leave of absence?",
        ],
    },
    "vdc": {
        "label": "Voluntary Death Contribution Policy",
        "questions": [
            "What is the Voluntary Death Contribution scheme at Arvind?",
            "How much do employees contribute under the VDC scheme?",
            "Who is eligible to receive benefits under the VDC scheme?",
            "How is the contribution collected from employees?",
            "When is the VDC benefit paid out?",
            "Is the VDC contribution compulsory for all employees?",
            "What happens to the VDC fund if there are no deaths in a year?",
            "Can an employee opt out of the VDC scheme?",
            "How is the VDC amount calculated per employee?",
            "Are there any conditions on VDC payouts?",
            # OOS
            "What is the annual increment policy?",
            "How do I apply for study leave?",
        ],
    },
    "pankh": {
        "label": "Pankh Employee Referral Policy",
        "questions": [
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
            # OOS
            "What is the vehicle allowance policy?",
            "How do I update my emergency contact in the HR system?",
        ],
    },
    "tm": {
        "label": "Talent Mobility Policy",
        "questions": [
            "What is Arvind's Talent Mobility Policy?",
            "What is the minimum tenure required before applying for internal job posting?",
            "Can my manager block my internal mobility application?",
            "Who can approve exceptions to the Talent Mobility Policy?",
            "What is the SIA process under Talent Mobility?",
            "Is there a financial adjustment on internal mobility?",
            "What is the role of the MAB committee in talent mobility?",
            "Can an employee apply for an IJP within their first year?",
            "What is the mobility adjustment amount?",
            "How do I apply for an internal job posting?",
            # OOS
            "What is the policy for receiving gifts from vendors?",
            "Can I hold a second job outside Arvind?",
        ],
    },
    "mb": {
        "label": "MediBuddy User Guide",
        "questions": [
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
            # OOS
            "How do I claim travel allowance?",
            "What is the company's leave without pay policy?",
        ],
    },
    "ts": {
        "label": "Travel Settlement Guide",
        "questions": [
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
            # OOS
            "How do I apply for flexible work arrangements?",
            "What is the policy on sabbaticals?",
        ],
    },
    "eap": {
        "label": "1to1 Employee Assistance Program",
        "questions": [
            "What is the Employee Assistance Program (EAP) at Arvind?",
            "Is the EAP service free for employees?",
            "Is the EAP service confidential?",
            "What type of counselling does the EAP provide?",
            "How do I contact the 1to1 EAP helpline?",
            "Can family members of employees use the EAP?",
            "How many EAP sessions are covered per employee?",
            "Does using EAP get reported to my manager or HR?",
            "What issues can be addressed through the EAP?",
            "Is the EAP available 24x7?",
            # OOS
            "What is the company's internet usage policy?",
            "How do I request a transfer to another city?",
        ],
    },
}


# ── Retrieval helper ──────────────────────────────────────────────────────────

def get_context_and_answer(policy_short: str, question: str) -> tuple[str, str]:
    """Call the policy retriever and return (context_str, answer_str)."""
    from router import route

    result = route(question)
    if not result.get("matched"):
        return "", result.get("text", "")

    # Re-call the specific policy retriever to get raw context
    policy_cfg = {
        "wb":    ("policies.whistleblower.retriever",   "answer"),
        "posh":  ("policies.posh.retriever",            "answer"),
        "grv":   ("policies.grievance.retriever",       "answer"),
        "gen":   ("policies.gender.retriever",          "answer"),
        "dt":    ("policies.domestic_travel.retriever", "answer"),
        "jn":    ("policies.joining.retriever",         "answer"),
        "fnf":   ("policies.fnf.retriever",             "answer"),
        "exp":   ("policies.expense.retriever",         "answer"),
        "lc":    ("policies.local_conveyance.retriever","answer"),
        "ghi":   ("policies.group_health.retriever",    "answer"),
        "gpa":   ("policies.group_personal_accident.retriever", "answer"),
        "gtl":   ("policies.group_term_life.retriever", "answer"),
        "vdc":   ("policies.vdc.retriever",             "answer"),
        "pankh": ("policies.pankh.retriever",           "answer"),
        "tm":    ("policies.talent_mobility.retriever", "answer"),
        "mb":    ("policies.medibuddy.retriever",       "answer"),
        "ts":    ("policies.travel_settlement.retriever","answer"),
        "eap":   ("policies.eap.retriever",             "answer"),
    }

    retriever_map = {
        "wb":    ("policies.whistleblower.retriever",   "_retriever"),
        "posh":  ("policies.posh.retriever",            "_retriever"),
        "grv":   ("policies.grievance.retriever",       "_retriever"),
        "gen":   ("policies.gender.retriever",          "_retriever"),
        "dt":    ("policies.domestic_travel.retriever", "_retriever"),
        "jn":    ("policies.joining.retriever",         "_retriever"),
        "fnf":   ("policies.fnf.retriever",             "_retriever"),
        "exp":   ("policies.expense.retriever",         "_retriever"),
        "lc":    ("policies.local_conveyance.retriever","_retriever"),
        "ghi":   ("policies.group_health.retriever",    "_retriever"),
        "gpa":   ("policies.group_personal_accident.retriever", "_retriever"),
        "gtl":   ("policies.group_term_life.retriever", "_retriever"),
        "vdc":   ("policies.vdc.retriever",             "_retriever"),
        "pankh": ("policies.pankh.retriever",           "_retriever"),
        "tm":    ("policies.talent_mobility.retriever", "_retriever"),
        "mb":    ("policies.medibuddy.retriever",       "_retriever"),
        "ts":    ("policies.travel_settlement.retriever","_retriever"),
        "eap":   ("policies.eap.retriever",             "_retriever"),
    }

    import importlib
    module_path, attr = retriever_map[policy_short]
    mod = importlib.import_module(module_path)
    retriever = getattr(mod, attr)
    chunks = retriever.retrieve(question)
    context = "\n\n---\n\n".join(c["text"] for c in chunks)
    return context, result.get("text", "")


# ── Build Ragas dataset ───────────────────────────────────────────────────────

def build_dataset(policy_short: str) -> Dataset:
    cfg      = POLICY_TESTS[policy_short]
    label    = cfg["label"]
    questions = cfg["questions"]

    rows = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    for i, q in enumerate(questions, 1):
        print(f"  [{i:02d}/{len(questions)}] {q[:70]}...", flush=True)
        try:
            context, answer = get_context_and_answer(policy_short, q)
        except Exception as e:
            print(f"    ⚠ retrieval error: {e}")
            context, answer = "", f"Error: {e}"

        rows["question"].append(q)
        rows["answer"].append(answer)
        rows["contexts"].append([context] if context else ["No context retrieved"])
        rows["ground_truth"].append("")  # reference-free: not needed for faithfulness/relevancy
        time.sleep(1.5)  # respect Groq rate limits during retrieval

    return Dataset.from_dict(rows)


# ── Run Ragas evaluation ──────────────────────────────────────────────────────

def run_policy_eval(policy_short: str) -> dict:
    cfg = POLICY_TESTS[policy_short]
    print(f"\n{'='*60}")
    print(f"  Evaluating: {cfg['label']}")
    print(f"{'='*60}")

    dataset = build_dataset(policy_short)

    judge_llm  = make_judge_llm()
    embeddings = make_embeddings()

    print("  Running Ragas metrics (faithfulness + answer_relevancy)...")
    try:
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy],
            llm=judge_llm,
            embeddings=embeddings,
            raise_exceptions=False,
        )
        scores = result.to_pandas()
        faith  = float(scores["faithfulness"].mean())
        relev  = float(scores["answer_relevancy"].mean())
        overall = (faith + relev) / 2
    except Exception as e:
        print(f"  ⚠ Ragas error: {e}")
        faith, relev, overall = 0.0, 0.0, 0.0

    return {
        "policy":           cfg["label"],
        "faithfulness":     round(faith, 3),
        "answer_relevancy": round(relev, 3),
        "overall":          round(overall, 3),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set in .env")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default="all",
                        help="Policy short code (wb, posh, grv, ...) or 'all'")
    args = parser.parse_args()

    to_eval = list(POLICY_TESTS.keys()) if args.policy == "all" else [args.policy]

    results = []
    for policy_short in to_eval:
        if policy_short not in POLICY_TESTS:
            print(f"Unknown policy: {policy_short}. Valid: {', '.join(POLICY_TESTS)}")
            continue
        result = run_policy_eval(policy_short)
        results.append(result)
        time.sleep(3)  # pause between policies to avoid Groq rate limits

    print(f"\n{'='*70}")
    print(f"  ARVIN — Ragas Evaluation Summary ({len(results)} policies)")
    print(f"{'='*70}")
    print(f"  {'Policy':<45} {'Faithful':>9} {'Relevant':>9} {'Overall':>9}")
    print(f"  {'-'*45} {'-'*9} {'-'*9} {'-'*9}")
    for r in results:
        flag = "✓" if r["overall"] >= 0.75 else "✗"
        print(f"  {flag} {r['policy']:<44} {r['faithfulness']:>9.3f} {r['answer_relevancy']:>9.3f} {r['overall']:>9.3f}")

    if results:
        avg_faith  = sum(r["faithfulness"]     for r in results) / len(results)
        avg_relev  = sum(r["answer_relevancy"]  for r in results) / len(results)
        avg_all    = sum(r["overall"]           for r in results) / len(results)
        print(f"\n  {'AVERAGE':<45} {avg_faith:>9.3f} {avg_relev:>9.3f} {avg_all:>9.3f}")

    out_path = os.path.join(os.path.dirname(__file__), "ragas_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved → {out_path}")


if __name__ == "__main__":
    main()
