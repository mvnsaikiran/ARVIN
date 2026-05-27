"""
ARVIN — Offline Policy Accuracy Evaluator
Zero LLM calls. Runs entirely on local ONNX embeddings + router keyword matching.

Question generation: extracts 50+ questions per policy directly from chunk text
using sentence patterns (definitions, procedures, timelines, amounts, roles, OOS).

Metrics:
  routing_accuracy  — router keyword match sends query to correct policy (%)
  retrieval_hit     — retriever returns relevant chunks for in-scope queries (%)
  oos_rejection     — OOS queries correctly NOT matched by router (%)
  semantic_score    — ONNX cosine similarity: query ↔ top retrieved chunk (0–1)
  overall           — weighted composite

Usage:
    python eval/offline_accuracy.py
    python eval/offline_accuracy.py --policy wb
    python eval/offline_accuracy.py --questions-only   # show generated questions
"""

import os, sys, re, json, argparse
from typing import List
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from chromadb.utils import embedding_functions

EVAL_DIR        = os.path.dirname(os.path.abspath(__file__))
VECTORSTORE_DIR = os.path.join(EVAL_DIR, '..', 'vectorstore')
TARGET_PER_POLICY = 50   # minimum questions per policy

# ── ONNX embeddings ───────────────────────────────────────────────────────────

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

def batch_cosine(queries: List[str], docs: List[str]) -> List[float]:
    if not queries or not docs:
        return []
    fn   = _get_onnx()
    vecs = fn(queries + docs)
    q_vecs = vecs[:len(queries)]
    d_vecs = vecs[len(queries):]
    return [cosine(q, d) for q, d in zip(q_vecs, d_vecs)]

# ── Policy config ─────────────────────────────────────────────────────────────

POLICY_MAP = {
    "wb":    ("policy_whistleblower",          "Whistleblower Policy",               "whistleblower"),
    "posh":  ("policy_posh",                   "POSH Policy",                        "posh"),
    "grv":   ("policy_grievance",              "Grievance Mechanism Policy",         "grievance"),
    "gen":   ("policy_gender",                 "Gender Policy",                      "gender"),
    "dt":    ("policy_domestic_travel",        "Domestic Travel Policy",             "domestic_travel"),
    "jn":    ("policy_joining",                "Joining Policy",                     "joining"),
    "fnf":   ("policy_fnf",                    "Full & Final Settlement Policy",     "fnf"),
    "exp":   ("policy_expense",                "Employee Expense Reimbursement Policy", "expense"),
    "lc":    ("policy_local_conveyance",       "Local Conveyance Policy",            "local_conveyance"),
    "ghi":   ("policy_ghi",                    "Group Health Insurance Policy",      "group_health"),
    "gpa":   ("policy_gpa",                    "Group Personal Accident Insurance Policy",  "group_personal_accident"),
    "gtl":   ("policy_gtl",                    "Group Term Life Insurance Policy",          "group_term_life"),
    "vdc":   ("policy_vdc",                    "Voluntary Death Contribution Policy","vdc"),
    "pankh": ("policy_pankh",                  "Pankh Employee Referral Policy",     "pankh"),
    "tm":    ("policy_talent_mobility",        "Talent Mobility Policy",             "talent_mobility"),
    "mb":    ("policy_medibuddy",              "MediBuddy User Guide",               "medibuddy"),
    "ts":    ("policy_travel_settlement",      "Travel Settlement Guide",            "travel_settlement"),
    "eap":   ("policy_eap",                    "1to1 Employee Assistance Program",   "eap"),
}

# Out-of-scope question pool (shared across all policies)
OOS_POOL = [
    "How do I apply for a home loan from Arvind?",
    "What is the annual leave balance for this year?",
    "Can I work from home permanently?",
    "What is the salary increment cycle at Arvind?",
    "How do I get a no-objection certificate?",
    "What is the dress code policy at Arvind?",
    "How do I change my bank account for salary credit?",
    "What is the probation period for new joiners?",
    "Can I carry forward my earned leave to next year?",
    "How do I apply for early retirement?",
    "What is the process for getting a laptop from IT?",
    "How do I log a complaint about the canteen food?",
    "What is the policy on using personal mobile phones at work?",
    "How do I access the employee self-service portal?",
    "What happens to my PF if I resign?",
]

# ── Question generation from chunks ──────────────────────────────────────────

def load_chunks(collection: str) -> list[dict]:
    path = os.path.join(VECTORSTORE_DIR, f'{collection}_chunks.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def _sentences(text: str) -> list[str]:
    text = re.sub(r'\s+', ' ', text.strip())
    parts = re.split(r'(?<=[.?!])\s+', text)
    return [p.strip() for p in parts if len(p.strip()) > 30]

def _extract_amount(text: str) -> str | None:
    m = re.search(r'(₹\s*[\d,]+|Rs\.?\s*[\d,]+|\d+\s*(?:days?|months?|years?|hours?|%))', text, re.I)
    return m.group() if m else None

def _extract_role(text: str) -> str | None:
    roles = [
        'committee', 'officer', 'manager', 'hr', 'employee', 'complainant',
        'respondent', 'whistleblower', 'chairman', 'member', 'buhr', 'chro',
    ]
    for r in roles:
        if r in text.lower():
            return r
    return None

def generate_questions_from_chunks(short: str, chunks: list[dict], label: str) -> tuple[list[str], list[str]]:
    """Returns (in_scope_questions, oos_questions)."""
    in_scope = set()

    # Seed with handcrafted base questions per policy type
    base = _base_questions(short, label)
    in_scope.update(base)

    for chunk in chunks:
        text = chunk['text']
        sents = _sentences(text)

        for sent in sents:
            sl = sent.lower()

            # Pattern: definitions → "What is X?"
            m = re.match(r'(.{5,60})\s+(?:is defined as|refers to|means|shall mean)\s+(.{10,})', sent, re.I)
            if m:
                subject = m.group(1).strip().rstrip('.,;')
                in_scope.add(f"What is the definition of {subject} under this policy?")

            # Pattern: SHALL/MUST obligations → procedural questions
            if re.search(r'\b(shall|must|is required to|should)\b', sl):
                amount = _extract_amount(sent)
                role   = _extract_role(sent)
                if amount and role:
                    in_scope.add(f"What is the {amount} associated with the {role}'s obligation?")
                elif re.search(r'\b(submit|file|report|raise|lodge|escalate|apply)\b', sl):
                    verb = re.search(r'\b(submit|file|report|raise|lodge|escalate|apply)\b', sl).group()
                    in_scope.add(f"Who is required to {verb} under this policy?")

            # Pattern: timelines → "How many days..."
            m = re.search(r'(\d+)\s*(working\s*)?days?', sl)
            if m:
                days = m.group(0)
                # Create a question about this timeline
                ctx = sent[:80].strip()
                in_scope.add(f"What is the {days} timeline mentioned in the policy?")

            # Pattern: numbered steps → procedural
            if re.match(r'^\d+[\.\)]\s+', sent.strip()):
                step_text = re.sub(r'^\d+[\.\)]\s+', '', sent.strip())
                if len(step_text) > 20:
                    in_scope.add(f"What is one of the steps in the procedure described in the policy?")

            # Pattern: amounts/limits → entitlement questions
            m = re.search(r'(₹\s*[\d,]+|Rs\.?\s*[\d,]+)', sent)
            if m:
                amount = m.group()
                in_scope.add(f"What is the {amount} limit or amount mentioned in this policy?")

            # Pattern: eligibility
            if re.search(r'\b(eligible|entitled|covered|applicable|qualify)\b', sl):
                in_scope.add(f"Who is eligible or entitled under this policy?")

            # Pattern: escalation / appeal
            if re.search(r'\b(escalat|appeal|second level|third level|higher authority)\b', sl):
                in_scope.add(f"What is the escalation process described in this policy?")

            # Pattern: confidentiality
            if re.search(r'\b(confidential|identity|anonymous|protect)\b', sl):
                in_scope.add(f"How does the policy protect confidentiality?")

            # Pattern: consequences / penalties
            if re.search(r'\b(terminat|disciplinary|penalty|action|consequence)\b', sl):
                in_scope.add(f"What are the disciplinary consequences described in this policy?")

            if len(in_scope) >= TARGET_PER_POLICY * 2:
                break
        if len(in_scope) >= TARGET_PER_POLICY * 2:
            break

    # Deduplicate, trim very similar questions, cap at TARGET_PER_POLICY
    in_scope_list = _deduplicate(list(in_scope), TARGET_PER_POLICY)

    # OOS: pick 10 from the shared pool (shuffled by hash of label for determinism)
    import hashlib
    seed = int(hashlib.md5(label.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    oos_indices = rng.choice(len(OOS_POOL), size=min(10, len(OOS_POOL)), replace=False)
    oos_list = [OOS_POOL[i] for i in oos_indices]

    return in_scope_list, oos_list


def _deduplicate(questions: list[str], limit: int) -> list[str]:
    """Remove near-duplicate questions using simple token overlap."""
    kept = []
    seen_tokens = []
    for q in questions:
        tokens = set(q.lower().split())
        is_dup = any(len(tokens & s) / max(len(tokens | s), 1) > 0.75 for s in seen_tokens)
        if not is_dup:
            kept.append(q)
            seen_tokens.append(tokens)
        if len(kept) >= limit:
            break
    return kept


def _base_questions(short: str, label: str) -> list[str]:
    """5–10 manually crafted seed questions per policy for diversity."""
    BASE = {
        "wb":    ["What is the purpose of the Whistleblower Policy?",
                  "Who can file a protected disclosure?",
                  "How is confidentiality maintained for a whistleblower?",
                  "What happens if a whistleblower is retaliated against?",
                  "What channels are available to report a disclosure?"],
        "posh":  ["What constitutes sexual harassment under POSH?",
                  "How do I file a POSH complaint?",
                  "What is the role of the Anti Harassment Committee?",
                  "What is the inquiry timeline under POSH?",
                  "What disciplinary action follows a POSH complaint?"],
        "grv":   ["How do I raise a workplace grievance at Arvind?",
                  "What are the escalation levels in the grievance process?",
                  "What is the timeline for resolving a grievance?",
                  "Who handles the first level of grievance resolution?",
                  "Can a grievance be submitted anonymously?"],
        "gen":   ["What is the Gender Policy about?",
                  "How can an employee report gender discrimination?",
                  "Are LGBTQ employees protected under the Gender Policy?",
                  "What disciplinary action is taken for gender-based harassment?",
                  "How often is the Gender Policy reviewed?"],
        "dt":    ["What is the process for booking domestic air travel?",
                  "What are the hotel limits for M2 grade employees?",
                  "What class of travel is an E2 grade employee entitled to?",
                  "What is the deadline to submit travel claims?",
                  "Are taxi expenses covered under domestic travel?"],
        "jn":    ["What relocation benefits does Arvind provide to new joiners?",
                  "Is brokerage reimbursed for renting accommodation while joining?",
                  "What household goods transportation support is provided?",
                  "How long does a new joiner have to claim relocation benefits?",
                  "What documents are needed to claim joining benefits?"],
        "fnf":   ["What is included in the Full and Final Settlement?",
                  "How many days does Arvind take to process FnF?",
                  "What is recovered from FnF if notice period is not served?",
                  "How are earned leaves encashed during FnF?",
                  "What components are deducted in notice pay recovery?"],
        "exp":   ["What types of expenses can I claim for reimbursement?",
                  "What is the deadline for submitting an expense claim?",
                  "Who approves expense reimbursement at Arvind?",
                  "Are entertainment expenses covered under this policy?",
                  "What receipts are needed for expense claims?"],
        "lc":    ["What is the rate per km for a personal two-wheeler?",
                  "Is home-to-office commute reimbursable under local conveyance?",
                  "What is the monthly cap on local conveyance claims?",
                  "Are OLA or UBER rides covered under local conveyance?",
                  "How do I submit a local conveyance claim?"],
        "ghi":   ["What is the sum insured under Group Health Insurance?",
                  "Are pre-existing diseases covered under the health policy?",
                  "What is the room rent limit for hospitalization?",
                  "How do I file a cashless health insurance claim?",
                  "What is the FHPL helpline number?"],
        "gpa":   ["What does the Group Personal Accident Insurance cover?",
                  "What is the compensation for permanent total disability?",
                  "Is accidental death covered under GPA?",
                  "What percentage is paid for partial disability?",
                  "Does GPA cover accidents outside working hours?"],
        "gtl":   ["What is the sum insured under Group Term Life Insurance?",
                  "How is the GTL death benefit calculated?",
                  "How do I nominate a beneficiary under GTL?",
                  "What documents are needed to file a GTL claim?",
                  "Is the GTL premium paid by the employee or Arvind?"],
        "vdc":   ["What is the Voluntary Death Contribution scheme?",
                  "How much do employees contribute under VDC?",
                  "Who receives VDC benefits?",
                  "Is VDC contribution compulsory for all employees?",
                  "Can an employee opt out of the VDC scheme?"],
        "pankh": ["What is the Pankh Employee Referral Programme?",
                  "What is the referral bonus for referring a female candidate?",
                  "How many tranches is the Pankh bonus paid in?",
                  "Are transgender referrals eligible for bonus under Pankh?",
                  "Is there a bonus for referring a male candidate?"],
        "tm":    ["What is the Talent Mobility Policy?",
                  "What is the minimum tenure to apply for an internal job posting?",
                  "Can a manager block an employee's mobility application?",
                  "Who approves exceptions to the Talent Mobility Policy?",
                  "What is the mobility adjustment amount?"],
        "mb":    ["What is MediBuddy Gold?",
                  "Who is covered under MediBuddy Gold?",
                  "How do I register on the MediBuddy app?",
                  "Is MediBuddy Gold free for Arvind employees?",
                  "What is the MediBuddy customer care number?"],
        "ts":    ["What is the deadline to submit travel expense claims?",
                  "How do I submit expenses on the MyTour Dashboard?",
                  "What happens if I miss the 15-day expense submission deadline?",
                  "What is the auto-settlement policy on day 16?",
                  "What documents are required for travel settlement?"],
        "eap":   ["What is the Employee Assistance Program at Arvind?",
                  "Is the EAP service free and confidential?",
                  "How do I contact the 1to1 EAP helpline?",
                  "Can family members use the EAP?",
                  "Does using EAP get reported to my manager?"],
    }
    return BASE.get(short, [f"What is the {label} about?"])


# ── Evaluation ────────────────────────────────────────────────────────────────

def eval_question_offline(short: str, question: str, expected_label: str, is_oos: bool) -> dict:
    import importlib
    from router import detect_policy, POLICY_REGISTRY

    # 1. Routing check
    detected        = detect_policy(question)
    routed_correctly = (detected == expected_label)

    # 2. Retrieval
    chunks = []
    try:
        mod    = importlib.import_module(f"policies.{POLICY_MAP[short][2]}.retriever")
        retr   = getattr(mod, '_retriever')
        chunks = retr.retrieve(question)
    except Exception:
        pass
    context_text = " ".join(c['text'] for c in chunks[:3])
    has_chunks   = len(chunks) > 0 and len(context_text.strip()) > 50

    # 3. Router keyword match strength
    q = question.lower()
    best_count = 0
    for keywords, _, _ in POLICY_REGISTRY:
        cnt = sum(1 for kw in keywords if kw in q)
        best_count = max(best_count, cnt)
    router_matched = best_count >= 1

    # 4. Semantic: cosine(question, top chunk)
    sem = 0.0
    if has_chunks and chunks:
        try:
            sims = batch_cosine([question], [chunks[0]['text']])
            sem  = max(0.0, sims[0])
        except Exception:
            pass

    if is_oos:
        correct  = not router_matched
        answered = router_matched
    else:
        correct  = routed_correctly and has_chunks
        answered = has_chunks

    return {
        "question":          question,
        "is_oos":            is_oos,
        "routed_correctly":  routed_correctly,
        "router_matched":    router_matched,
        "has_chunks":        has_chunks,
        "answered":          answered,
        "correct":           correct,
        "semantic_score":    round(sem, 3),
        "chunks_retrieved":  len(chunks),
    }


def eval_policy(short: str, questions_only: bool = False) -> dict:
    collection, label, _ = POLICY_MAP[short]
    chunks = load_chunks(collection)

    in_scope, oos = generate_questions_from_chunks(short, chunks, label)
    all_q = [(q, False) for q in in_scope] + [(q, True) for q in oos]

    if questions_only:
        print(f"\n  ── {label} ({len(in_scope)} in-scope, {len(oos)} OOS) ──")
        for q in in_scope[:5]:
            print(f"     {q}")
        print(f"     ... and {len(in_scope)-5} more")
        return {}

    print(f"\n  ── {label}  ({len(in_scope)} in-scope + {len(oos)} OOS = {len(all_q)} total) ──", flush=True)

    rows = []
    for i, (q, is_oos) in enumerate(all_q, 1):
        row = eval_question_offline(short, q, label, is_oos)
        rows.append(row)
        sym = "✓" if row["correct"] else "✗"
        tag = "OOS" if is_oos else "   "
        if i % 10 == 0 or i == len(all_q):
            print(f"    [{i:03d}/{len(all_q)}] progress...", flush=True)

    in_scope_rows = [r for r in rows if not r["is_oos"]]
    oos_rows      = [r for r in rows if r["is_oos"]]

    routing_acc = sum(r["routed_correctly"] for r in rows)         / max(len(rows), 1)
    retrieval   = sum(r["has_chunks"]       for r in in_scope_rows) / max(len(in_scope_rows), 1)
    oos_reject  = sum(not r["router_matched"] for r in oos_rows)   / max(len(oos_rows), 1)
    sem_avg     = sum(r["semantic_score"]   for r in in_scope_rows) / max(len(in_scope_rows), 1)

    overall = routing_acc * 0.30 + retrieval * 0.30 + oos_reject * 0.20 + sem_avg * 0.20

    return {
        "policy":           label,
        "short":            short,
        "n_total":          len(rows),
        "n_in_scope":       len(in_scope_rows),
        "n_oos":            len(oos_rows),
        "routing_accuracy": round(routing_acc, 3),
        "retrieval_hit":    round(retrieval,   3),
        "oos_rejection":    round(oos_reject,  3),
        "semantic_score":   round(sem_avg,     3),
        "overall":          round(overall,     3),
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
    n_q = sum(r["n_total"] for r in results)
    print(f"\n{'='*84}")
    print(f"  ARVIN — Offline Policy Accuracy Report  ({len(results)} policies, {n_q} questions total)")
    print(f"  Routing(30%) | Retrieval Hit(30%) | OOS Rejection(20%) | Semantic(20%)")
    print(f"{'='*84}")
    print(f"  {'Policy':<42} {'N':>4} {'Route':>6} {'Retr':>6} {'OOS':>6} {'Sem':>6} {'Score':>7}  Grade")
    print(f"  {'─'*42} {'─'*4} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*7}  {'─'*5}")

    for r in results:
        flag = "✓" if r["overall"] >= 0.75 else ("△" if r["overall"] >= 0.60 else "✗")
        print(
            f"  {flag} {r['policy']:<41} {r['n_total']:>4}"
            f" {r['routing_accuracy']:>6.0%}"
            f" {r['retrieval_hit']:>6.0%}"
            f" {r['oos_rejection']:>6.0%}"
            f" {r['semantic_score']:>6.2f}"
            f" {r['overall']:>7.3f}"
            f"  {_grade(r['overall'])}"
        )

    if results:
        ar  = sum(r["routing_accuracy"] for r in results) / len(results)
        ah  = sum(r["retrieval_hit"]    for r in results) / len(results)
        ao  = sum(r["oos_rejection"]    for r in results) / len(results)
        as_ = sum(r["semantic_score"]   for r in results) / len(results)
        avg = sum(r["overall"]          for r in results) / len(results)
        nt  = sum(r["n_total"]          for r in results)
        print(f"  {'─'*42} {'─'*4} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*7}  {'─'*5}")
        print(f"  {'AVERAGE':<42} {nt:>4} {ar:>6.0%} {ah:>6.0%} {ao:>6.0%} {as_:>6.2f} {avg:>7.3f}  {_grade(avg)}")

    out = os.path.join(EVAL_DIR, "offline_accuracy_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Full report saved → {out}")

    # Improvement targets
    weak = sorted([r for r in results if r["overall"] < 0.80], key=lambda x: x["overall"])
    if weak:
        print(f"\n  ── Policies to boost ────────────────────────────────────────────")
        for r in weak:
            issues = []
            if r["routing_accuracy"] < 0.80: issues.append(f"routing {r['routing_accuracy']:.0%} → add keywords")
            if r["retrieval_hit"]    < 0.80: issues.append(f"retrieval {r['retrieval_hit']:.0%} → re-ingest / more chunks")
            if r["oos_rejection"]    < 0.80: issues.append(f"OOS {r['oos_rejection']:.0%} → tighten keywords")
            if r["semantic_score"]   < 0.40: issues.append(f"semantic {r['semantic_score']:.2f} → chunk quality low")
            print(f"  ✗ {r['policy']}")
            for issue in issues:
                print(f"      → {issue}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy",         default="all")
    parser.add_argument("--questions-only", action="store_true",
                        help="Just print generated questions, don't evaluate")
    args = parser.parse_args()

    policies = list(POLICY_MAP.keys()) if args.policy == "all" else [args.policy]

    if not args.questions_only:
        total_q = len(policies) * (TARGET_PER_POLICY + 10)
        print(f"\n{'='*84}")
        print(f"  ARVIN — Offline Accuracy Eval  ({len(policies)} policies, ~{total_q} questions)")
        print(f"  Zero LLM calls — routing + retrieval + ONNX similarity only")
        print(f"{'='*84}")

    results = []
    for short in policies:
        result = eval_policy(short, questions_only=args.questions_only)
        if result:
            results.append(result)
            interim = os.path.join(EVAL_DIR, f"{short}_offline_result.json")
            with open(interim, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

    if results:
        print_report(results)


if __name__ == "__main__":
    main()
