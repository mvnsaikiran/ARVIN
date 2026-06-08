"""
End-to-end LLM accuracy benchmark for ARVIN.
Calls the /api/chat endpoint and checks if key facts appear in the LLM answer.

Run this on your LOCAL machine (requires backend running with Groq key):
  python backend.py   (in one terminal)
  python benchmark_llm.py   (in another terminal)

Reports per-policy LLM accuracy.
"""

import json, re, time, sys
from collections import defaultdict
import requests

BACKEND = "http://127.0.0.1:8001"
HOLDOUT = "adversarial_holdout.json"
DELAY   = 0.5   # seconds between calls (avoid Groq rate limit)

# Short display names for policies in the question prefix
POLICY_SHORT = {
    "Domestic Travel Expense Settlement Procedure": "Domestic Travel Expense Settlement",
    "Domestic Travel Policy": "Domestic Travel Policy",
    "Employee Assistance Program (EAP)": "Employee Assistance Program (EAP)",
    "Employee Expense Reimbursement Policy": "Employee Expense Reimbursement Policy",
    "Exit & Full & Final Settlement Policy": "Exit and Full & Final Settlement Policy",
    "Gender Policy 2025": "Gender Policy",
    "Grievance Mechanism Policy 2025": "Grievance Mechanism Policy",
    "Group Health Insurance Policy": "Group Health Insurance Policy",
    "Group Personal Accident Insurance Scheme": "Group Personal Accident Insurance",
    "Group Term Life Insurance": "Group Term Life Insurance",
    "Joining Policy": "Joining Policy",
    "Local Conveyance Policy": "Local Conveyance Policy",
    "MediBuddy Health & Wellness (User Manual)": "MediBuddy Health & Wellness",
    "POSH Policy (Prevention of Sexual Harassment)": "POSH Policy",
    "Pankh Employee Referral": "Pankh Employee Referral Policy",
    "Talent Mobility Policy": "Talent Mobility Policy",
    "Voluntary Death Contribution Scheme": "Voluntary Death Contribution Scheme",
    "Whistleblower Policy": "Whistleblower Policy",
}


def normalise(t: str) -> str:
    t = t.lower()
    t = re.sub(r'rs\.?\s*', '', t)
    t = re.sub(r'₹\s*', '', t)
    t = re.sub(r'/-', '', t)
    t = re.sub(r',', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def extract_numbers(t: str) -> set:
    """Extract all numbers (4+ digits) from text for numerical matching."""
    return set(re.findall(r'\d{4,}', re.sub(r',', '', t)))


def check_answer(answer: str, key_facts: list[str]) -> bool:
    """
    Pass if any key_fact matches the LLM answer.
    Uses two checks:
      1. Substring match after normalisation (exact text)
      2. Numerical match — if key_fact has 4+ digit numbers, all must appear in answer
    """
    norm_ans = normalise(answer)
    for kf in key_facts:
        if not normalise(kf):
            continue
        # Check 1: substring
        if normalise(kf) in norm_ans:
            return True
        # Check 2: all significant numbers from key_fact appear in answer
        kf_nums = extract_numbers(kf)
        if kf_nums and kf_nums.issubset(extract_numbers(answer)):
            return True
        # Check 3: key words (3+ char tokens) from key_fact appear in answer
        kf_words = set(w for w in re.findall(r'\b[a-zA-Z]{4,}\b', kf.lower()))
        ans_words = set(w for w in re.findall(r'\b[a-zA-Z]{4,}\b', norm_ans))
        if kf_words and len(kf_words & ans_words) >= max(1, len(kf_words) // 2):
            return True
    return False


def ask(query: str, policy: str) -> str:
    """Call backend with policy-prefixed query for accurate routing."""
    short = POLICY_SHORT.get(policy, policy)
    full_query = f"Regarding the {short}: {query}"
    try:
        r = requests.post(
            f"{BACKEND}/api/chat",
            json={"query": full_query, "employeeId": "benchmark"},
            timeout=45,
        )
        r.raise_for_status()
        return r.json().get("text", "")
    except Exception as e:
        return f"ERROR: {e}"


def main():
    # Health check
    try:
        r = requests.get(f"{BACKEND}/api/health", timeout=5)
        print(f"Backend: {r.json()}")
    except Exception:
        print("ERROR: Backend not running. Start with:")
        print("  set GROQ_API_KEY=your_groq_key_here")
        print("  python backend.py")
        sys.exit(1)

    with open(HOLDOUT) as f:
        cases = json.load(f)

    print(f"\nRunning LLM benchmark on {len(cases)} questions...\n")

    by_policy = defaultdict(lambda: {"pass": 0, "total": 0})
    total_pass = 0
    failures = []
    t0 = time.time()

    for i, case in enumerate(cases):
        query     = case.get("query", "")
        key_facts = case.get("key_facts", [])
        policy    = case.get("policy", "?")

        answer = ask(query, policy)
        ok = check_answer(answer, key_facts)

        by_policy[policy]["total"] += 1
        if ok:
            total_pass += 1
            by_policy[policy]["pass"] += 1
        else:
            failures.append({
                "query":     query,
                "policy":    policy,
                "key_facts": key_facts,
                "answer":    answer[:400],
            })

        if (i + 1) % 10 == 0 or i == len(cases) - 1:
            acc = total_pass / (i + 1) * 100
            print(f"  [{i+1:4d}/{len(cases)}]  running acc = {acc:.1f}%", flush=True)

        time.sleep(DELAY)

    elapsed = time.time() - t0
    total   = len(cases)
    pct     = total_pass / total * 100

    print(f"\n{'='*68}")
    print(f"LLM ACCURACY: {total_pass}/{total}  =  {pct:.2f}%  (elapsed {elapsed:.0f}s)")
    print(f"{'='*68}")
    print("\nBy policy:")
    for pol in sorted(by_policy):
        v = by_policy[pol]
        a = v["pass"] / v["total"] * 100
        flag = " ◄ LOW" if a < 90 else ""
        print(f"  {pol:<55} {v['pass']:4d}/{v['total']:4d}  ({a:.1f}%){flag}")

    with open("llm_benchmark_failures.json", "w") as f:
        json.dump(failures, f, indent=2)
    print(f"\nFailures saved -> llm_benchmark_failures.json")
    print(f"Total time: {elapsed:.0f}s")


if __name__ == "__main__":
    main()
