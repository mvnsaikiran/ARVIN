"""
Enterprise-grade evaluation pipeline for all 18 ARVIN policies.

Phase 1 — Generate: Uses Groq to generate ~230 questions per policy across
          8 enterprise question types (3 Groq calls per policy = 54 calls total)

Phase 2 — Evaluate: Runs each question through the RAG pipeline, then scores
          with Ragas (faithfulness + answer_relevancy) using local ONNX embeddings

Usage:
    python eval/enterprise_eval.py --generate          # generate 900 questions
    python eval/enterprise_eval.py --evaluate          # run Ragas on saved questions
    python eval/enterprise_eval.py --all               # generate + evaluate end-to-end
    python eval/enterprise_eval.py --all --policy wb   # single policy
"""

import os
import sys
import time
import json
import re
import argparse
import requests
from typing import List

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

from langchain_openai import ChatOpenAI
from langchain_core.embeddings import Embeddings
from chromadb.utils import embedding_functions
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

# ── Config ────────────────────────────────────────────────────────────────────

GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL    = "llama-3.3-70b-versatile"
GROQ_TIMEOUT  = 90

EVAL_DIR        = os.path.dirname(os.path.abspath(__file__))
VECTORSTORE_DIR = os.path.join(EVAL_DIR, '..', 'vectorstore')

POLICY_MAP = {
    "wb":    ("policy_whistleblower",          "Whistleblower Policy"),
    "posh":  ("policy_posh",                   "POSH Policy"),
    "grv":   ("policy_grievance",              "Grievance Mechanism Policy"),
    "gen":   ("policy_gender",                 "Gender Policy"),
    "dt":    ("policy_domestic_travel",        "Domestic Travel Policy"),
    "jn":    ("policy_joining",                "Joining Policy"),
    "fnf":   ("policy_fnf",                    "Full & Final Settlement Policy"),
    "exp":   ("policy_expense",                "Employee Expense Reimbursement Policy"),
    "lc":    ("policy_local_conveyance",       "Local Conveyance Policy"),
    "ghi":   ("policy_ghi",                    "Group Health Insurance Policy"),
    "gpa":   ("policy_gpa",                    "Group Personal Accident Insurance"),
    "gtl":   ("policy_gtl",                    "Group Term Life Insurance"),
    "vdc":   ("policy_vdc",                    "Voluntary Death Contribution Policy"),
    "pankh": ("policy_pankh",                  "Pankh Employee Referral Policy"),
    "tm":    ("policy_talent_mobility",        "Talent Mobility Policy"),
    "mb":    ("policy_medibuddy",              "MediBuddy User Guide"),
    "ts":    ("policy_travel_settlement",      "Travel Settlement Guide"),
    "eap":   ("policy_eap",                    "1to1 Employee Assistance Program"),
}

RETRIEVER_MAP = {
    "wb":    "policies.whistleblower.retriever",
    "posh":  "policies.posh.retriever",
    "grv":   "policies.grievance.retriever",
    "gen":   "policies.gender.retriever",
    "dt":    "policies.domestic_travel.retriever",
    "jn":    "policies.joining.retriever",
    "fnf":   "policies.fnf.retriever",
    "exp":   "policies.expense.retriever",
    "lc":    "policies.local_conveyance.retriever",
    "ghi":   "policies.group_health.retriever",
    "gpa":   "policies.group_personal_accident.retriever",
    "gtl":   "policies.group_term_life.retriever",
    "vdc":   "policies.vdc.retriever",
    "pankh": "policies.pankh.retriever",
    "tm":    "policies.talent_mobility.retriever",
    "mb":    "policies.medibuddy.retriever",
    "ts":    "policies.travel_settlement.retriever",
    "eap":   "policies.eap.retriever",
}


# ── Groq helper ───────────────────────────────────────────────────────────────

def groq_call(prompt: str, max_tokens: int = 2048) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "temperature": 0.4,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    delay = 5
    for attempt in range(5):
        try:
            resp = requests.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=GROQ_TIMEOUT,
            )
            if resp.status_code == 429:
                wait = max(int(resp.headers.get("retry-after", delay)), delay)
                print(f"    [rate limit] waiting {wait}s...", flush=True)
                time.sleep(wait)
                delay *= 2
                continue
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == 4:
                raise
            time.sleep(delay)
            delay *= 2
    return ""


# ── PHASE 1: Question generation ──────────────────────────────────────────────

QUESTION_TYPE_BATCHES = [
    {
        "name": "batch_a",
        "count": 90,
        "instruction": """Generate exactly 90 questions split across these 3 types:

TYPE 1 — DIRECT FACTUAL (30 questions): Simple specific lookups.
  Examples: exact amounts, limits, names, dates, contact numbers, percentages.
  e.g. "What is the hotel limit for M2 grade?" / "What is the helpline number?"

TYPE 2 — PROCEDURAL (30 questions): Step-by-step how-to questions.
  Examples: how to file, submit, apply, report, claim, escalate.
  e.g. "How do I submit a claim?" / "What is the process to file a complaint?"

TYPE 3 — ELIGIBILITY & CONDITIONAL (30 questions): Who qualifies, under what conditions.
  Examples: grade/band eligibility, tenure requirements, conditions, exceptions.
  e.g. "Am I eligible if I joined 6 months ago?" / "Which grades are covered?"

Output ONLY a JSON array of exactly 90 question strings. No labels, no explanations.
"""
    },
    {
        "name": "batch_b",
        "count": 80,
        "instruction": """Generate exactly 80 questions split across these 3 types:

TYPE 4 — PARAPHRASE VARIATIONS (30 questions): Rephrase common policy questions in alternate wording.
  Same meaning, completely different sentence structure. Tests if the chatbot handles varied language.
  e.g. "Can I get reimbursed for cab rides?" as a variation of "Is local conveyance reimbursable?"

TYPE 5 — MULTI-TURN FOLLOW-UP (20 questions): Questions an employee would ask AFTER a first answer.
  e.g. "What if I missed the 15-day deadline?" / "What happens if my manager doesn't approve?" / "Can I appeal?"

TYPE 6 — ADVERSARIAL & EDGE CASES (30 questions): Tricky, ambiguous, boundary-pushing questions.
  e.g. "What if both POSH and Grievance apply to my situation?" /
       "Can I file anonymously and still get protection?" /
       "What if the accused is my skip-level manager?"

Output ONLY a JSON array of exactly 80 question strings. No labels, no explanations.
"""
    },
    {
        "name": "batch_c",
        "count": 60,
        "instruction": """Generate exactly 60 questions split across these 2 types:

TYPE 7 — OUT-OF-SCOPE REJECTION (30 questions): Questions completely outside this specific policy.
  The chatbot MUST return a fallback. Do NOT ask about anything this policy covers.
  e.g. for POSH policy: "What is my annual leave balance?" / "How do I apply for a home loan?"

TYPE 8 — CROSS-POLICY CONFUSION (30 questions): Questions where the employee might confuse
  this policy with a different Arvind policy (POSH vs Whistleblower vs Grievance etc.)
  e.g. "Should I use the grievance form or the whistleblower form for this?" /
       "Is this covered under POSH or the gender policy?"

Output ONLY a JSON array of exactly 60 question strings. No labels, no explanations.
"""
    },
]


def load_policy_chunks(collection: str) -> list[dict]:
    path = os.path.join(VECTORSTORE_DIR, f'{collection}_chunks.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def build_context_sample(chunks: list[dict], max_chars: int = 4000) -> str:
    """Sample the most content-rich chunks to feed to the question generator."""
    sorted_chunks = sorted(chunks, key=lambda c: len(c['text']), reverse=True)
    sample, total = [], 0
    for c in sorted_chunks:
        if total + len(c['text']) > max_chars:
            break
        sample.append(c['text'])
        total += len(c['text'])
    return "\n\n---\n\n".join(sample)


def _parse_question_array(raw: str) -> list[str]:
    """Extract a JSON array of questions from a Groq response."""
    try:
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            questions = json.loads(match.group())
            return [q for q in questions if isinstance(q, str) and q.strip() and len(q) > 10]
    except Exception:
        pass
    # Fallback: grab anything that looks like a question
    lines = [l.strip().strip('"').strip("'").rstrip(',') for l in raw.splitlines()]
    return [l for l in lines if l.endswith('?') and len(l) > 15]


def generate_questions(short: str) -> list[str]:
    """Generate ~230 questions per policy across all 8 types using 3 Groq calls."""
    collection, label = POLICY_MAP[short]
    chunks  = load_policy_chunks(collection)
    context = build_context_sample(chunks)

    all_questions = []
    for batch in QUESTION_TYPE_BATCHES:
        prompt = (
            f"You are building a test suite for an enterprise HR chatbot.\n"
            f"Policy: {label}\n\n"
            f"POLICY CONTENT (use this to make questions specific and realistic):\n"
            f"{context}\n\n"
            f"{batch['instruction']}"
        )
        print(f"    {batch['name']} ({batch['count']} questions)...", flush=True)
        try:
            raw = groq_call(prompt, max_tokens=3000)
            questions = _parse_question_array(raw)
            all_questions.extend(questions)
            print(f"      got {len(questions)}", flush=True)
        except Exception as e:
            print(f"      ⚠ {e}", flush=True)
        time.sleep(4)  # pause between batches

    return all_questions


def run_generate(policies: list[str]):
    print(f"\n{'='*60}")
    print(f"  PHASE 1: Generating enterprise test questions")
    print(f"  Policies: {len(policies)} | Target: ~230 per policy")
    print(f"  Types: Direct(30) + Procedural(30) + Eligibility(30)")
    print(f"         Paraphrase(30) + Follow-up(20) + Adversarial(30)")
    print(f"         OOS(30) + Cross-policy(30)")
    print(f"{'='*60}")

    summary = {}
    for i, short in enumerate(policies, 1):
        _, label = POLICY_MAP[short]
        print(f"\n  [{i:02d}/{len(policies)}] {label}", flush=True)
        try:
            questions = generate_questions(short)
            out_path  = os.path.join(EVAL_DIR, f'{short}_enterprise_tests.json')
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "policy":    label,
                    "short":     short,
                    "questions": questions,
                }, f, indent=2, ensure_ascii=False)
            summary[short] = len(questions)
            print(f"  ✓ {label}: {len(questions)} questions saved", flush=True)
            time.sleep(5)  # pause between policies
        except Exception as e:
            print(f"  ✗ {label}: ERROR — {e}", flush=True)
            summary[short] = 0

    total = sum(summary.values())
    print(f"\n  Total questions generated: {total} across {len(policies)} policies")
    return summary


# ── PHASE 2: Evaluation ───────────────────────────────────────────────────────

class ONNXEmbeddings(Embeddings):
    def __init__(self):
        self._fn = embedding_functions.ONNXMiniLM_L6_V2()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [v for v in self._fn(texts)]

    def embed_query(self, text: str) -> List[float]:
        return self._fn([text])[0]


def get_rag_response(short: str, question: str) -> tuple[str, str]:
    """Returns (context, answer) for a question against its policy retriever."""
    import importlib
    mod  = importlib.import_module(RETRIEVER_MAP[short])
    retr = getattr(mod, '_retriever')

    try:
        chunks  = retr.retrieve(question)
        context = "\n\n---\n\n".join(c['text'] for c in chunks)
    except Exception:
        context = ""

    from router import route
    result  = route(question)
    answer  = result.get('text', '')
    return context, answer


def evaluate_policy(short: str, questions: list[str]) -> dict:
    _, label = POLICY_MAP[short]
    print(f"\n  Evaluating {label} ({len(questions)} questions)...", flush=True)

    rows = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    for i, q in enumerate(questions, 1):
        print(f"    [{i:02d}/{len(questions)}] {q[:65]}...", flush=True)
        try:
            context, answer = get_rag_response(short, q)
        except Exception as e:
            context, answer = "", f"Error: {e}"
        rows["question"].append(q)
        rows["answer"].append(answer)
        rows["contexts"].append([context] if context else ["No context retrieved"])
        rows["ground_truth"].append("")
        time.sleep(1.5)

    dataset = Dataset.from_dict(rows)

    judge_llm  = ChatOpenAI(
        model=GROQ_MODEL,
        openai_api_key=GROQ_API_KEY,
        openai_api_base=GROQ_BASE_URL,
        temperature=0.0,
        max_tokens=1024,
        request_timeout=60,
    )
    embeddings = ONNXEmbeddings()

    print(f"    Running Ragas metrics...", flush=True)
    try:
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy],
            llm=judge_llm,
            embeddings=embeddings,
            raise_exceptions=False,
        )
        df     = result.to_pandas()
        faith  = float(df["faithfulness"].mean())
        relev  = float(df["answer_relevancy"].mean())

        # Per-question detail for the report
        per_q = []
        for _, row in df.iterrows():
            per_q.append({
                "question":         row["question"],
                "faithfulness":     round(float(row["faithfulness"]), 3) if not np.isnan(row["faithfulness"]) else None,
                "answer_relevancy": round(float(row["answer_relevancy"]), 3) if not np.isnan(row["answer_relevancy"]) else None,
            })
    except Exception as e:
        print(f"    ⚠ Ragas error: {e}", flush=True)
        faith, relev, per_q = 0.0, 0.0, []

    return {
        "policy":           label,
        "short":            short,
        "n_questions":      len(questions),
        "faithfulness":     round(faith,  3),
        "answer_relevancy": round(relev,  3),
        "overall":          round((faith + relev) / 2, 3),
        "per_question":     per_q,
    }


def run_evaluate(policies: list[str]) -> list[dict]:
    print(f"\n{'='*60}")
    print(f"  PHASE 2: Ragas evaluation")
    print(f"{'='*60}")

    results = []
    for short in policies:
        _, label = POLICY_MAP[short]
        test_path = os.path.join(EVAL_DIR, f'{short}_enterprise_tests.json')
        if not os.path.exists(test_path):
            print(f"  ⚠ {label}: no test file — run --generate first", flush=True)
            continue

        with open(test_path, encoding='utf-8') as f:
            data = json.load(f)
        questions = data.get('questions', [])

        result = evaluate_policy(short, questions)
        results.append(result)

        # Save intermediate (so a crash doesn't lose everything)
        interim = os.path.join(EVAL_DIR, f'{short}_eval_result.json')
        with open(interim, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

        time.sleep(5)

    return results


# ── Report ────────────────────────────────────────────────────────────────────

def print_report(results: list[dict]):
    print(f"\n{'='*72}")
    print(f"  ARVIN — Enterprise Policy-Wise Accuracy Report")
    print(f"  {len(results)} policies | ~230 questions each | Ragas metrics")
    print(f"{'='*72}")
    print(f"  {'Policy':<48} {'N':>4} {'Faith':>7} {'Relev':>7} {'Score':>7}")
    print(f"  {'-'*48} {'-'*4} {'-'*7} {'-'*7} {'-'*7}")

    for r in results:
        flag  = "✓" if r["overall"] >= 0.75 else ("△" if r["overall"] >= 0.60 else "✗")
        grade = _grade(r["overall"])
        print(
            f"  {flag} {r['policy']:<47} {r['n_questions']:>4} "
            f"{r['faithfulness']:>7.3f} {r['answer_relevancy']:>7.3f} "
            f"{r['overall']:>7.3f}  {grade}"
        )

    if results:
        af = sum(r["faithfulness"]     for r in results) / len(results)
        ar = sum(r["answer_relevancy"] for r in results) / len(results)
        ao = sum(r["overall"]          for r in results) / len(results)
        print(f"  {'─'*48} {'─'*4} {'─'*7} {'─'*7} {'─'*7}")
        print(f"  {'AVERAGE':<48} {sum(r['n_questions'] for r in results):>4} "
              f"{af:>7.3f} {ar:>7.3f} {ao:>7.3f}  {_grade(ao)}")

    # Save full report
    out = os.path.join(EVAL_DIR, 'enterprise_accuracy_report.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Full report saved → {out}")


def _grade(score: float) -> str:
    if score >= 0.90: return "A+"
    if score >= 0.85: return "A"
    if score >= 0.80: return "B+"
    if score >= 0.75: return "B"
    if score >= 0.65: return "C"
    return "D"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set. Add it to .env or set $env:GROQ_API_KEY")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("--generate",  action="store_true", help="Generate test questions")
    parser.add_argument("--evaluate",  action="store_true", help="Run Ragas evaluation")
    parser.add_argument("--all",       action="store_true", help="Generate + evaluate")
    parser.add_argument("--policy",    default="all",
                        help="Policy short code or 'all' (default)")
    args = parser.parse_args()

    policies = list(POLICY_MAP.keys()) if args.policy == "all" else [args.policy]
    for p in policies:
        if p not in POLICY_MAP:
            print(f"Unknown policy: {p}. Valid: {', '.join(POLICY_MAP)}")
            sys.exit(1)

    if not (args.generate or args.evaluate or args.all):
        parser.print_help()
        sys.exit(0)

    if args.generate or args.all:
        run_generate(policies)

    if args.evaluate or args.all:
        results = run_evaluate(policies)
        print_report(results)


if __name__ == "__main__":
    main()
