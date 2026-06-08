"""
End-to-end LLM accuracy benchmark for ARVIN.
Calls the /api/chat endpoint and checks if key_facts appear in the LLM answer.

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
DELAY   = 0.3   # seconds between calls (avoid Groq rate limit)


def normalise(t: str) -> str:
    t = t.lower()
    t = re.sub(r'rs\.?\s*', '', t)
    t = re.sub(r'₹\s*', '', t)
    t = re.sub(r'/-', '', t)
    t = re.sub(r',', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def check_answer(answer: str, key_facts: list[str]) -> bool:
    """Pass if any key_fact appears in the LLM answer (OR logic)."""
    norm_ans = normalise(answer)
    return any(normalise(kf) in norm_ans for kf in key_facts if normalise(kf))


def ask(query: str) -> str:
    """Call the backend chat endpoint and return the answer text."""
    try:
        r = requests.post(
            f"{BACKEND}/api/chat",
            json={"query": query, "employeeId": "benchmark"},
            timeout=30,
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
        print("ERROR: Backend not running. Start with: python backend.py")
        sys.exit(1)

    with open(HOLDOUT) as f:
        cases = json.load(f)

    print(f"\nRunning LLM benchmark on {len(cases)} questions...\n")

    by_policy = defaultdict(lambda: {"pass": 0, "total": 0})
    total_pass = 0
    failures = []
    t0 = time.time()

    for i, case in enumerate(cases):
        query = case.get("query", "")
        key_facts = case.get("key_facts", [])
        policy = case.get("policy", "?")

        answer = ask(query)
        ok = check_answer(answer, key_facts)

        by_policy[policy]["total"] += 1
        if ok:
            total_pass += 1
            by_policy[policy]["pass"] += 1
        else:
            failures.append({
                "query": query,
                "policy": policy,
                "key_facts": key_facts,
                "answer": answer[:300],
            })

        if (i + 1) % 10 == 0 or i == len(cases) - 1:
            acc = total_pass / (i + 1) * 100
            print(f"  [{i+1:4d}/{len(cases)}]  running acc = {acc:.1f}%", flush=True)

        time.sleep(DELAY)

    elapsed = time.time() - t0
    total = len(cases)
    pct = total_pass / total * 100

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


if __name__ == "__main__":
    main()
