"""
Full 18-policy benchmark — original suites + expanded/balanced suites.

Suites included:
  Original:   enterprise (10k) + new_policies (480) + batch2 (272) + medibuddy (95)
  Expanded:   expanded_small_policies_suite (2496 new cases for 8 under-tested policies)
  Balanced:   whistleblower_balanced_suite (360) + posh_balanced_suite (456)

Run:  python3 benchmark_full18.py
Output:  full18_failures.json  (capped at 500)
"""

import json, re, time
from collections import defaultdict
import hybrid_rag

SUITES = [
    # (file, label, format)
    ("enterprise_test_suite.json",            "Original-8",       "old"),
    ("new_policies_test_suite.json",          "Batch-1 (5)",      "old"),
    ("batch2_test_suite.json",                "Batch-2 (4)",      "old"),
    ("medibuddy_test_suite.json",             "Batch-3 (MB)",     "new"),
    ("expanded_small_policies_suite.json",    "Expanded-Small-8", "old"),
    ("whistleblower_balanced_suite.json",     "WB-Balanced",      "old"),
    ("posh_balanced_suite.json",              "POSH-Balanced",    "old"),
]

TOP_K = 10


def normalise(t: str) -> str:
    t = t.lower()
    t = re.sub(r'rs\.?\s*', '', t)
    t = re.sub(r'₹\s*', '', t)
    t = re.sub(r'/-', '', t)
    t = re.sub(r',', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def check_old(chunks, key_facts):
    combined = " ".join(normalise(c["text"]) for c in chunks)
    missing = [kf for kf in key_facts if normalise(kf) and normalise(kf) not in combined]
    return len(missing) == 0, missing


def check_new(chunks, key_facts):
    combined = " ".join(normalise(c["text"]) for c in chunks)
    found = any(normalise(kf) in combined for kf in key_facts)
    return found, [] if found else key_facts


def run():
    all_cases = []
    for path, label, fmt in SUITES:
        try:
            data = json.load(open(path))
        except FileNotFoundError:
            print(f"  SKIP (not found): {path}")
            continue
        for c in data:
            c["_suite"] = label
            c["_fmt"]   = fmt
        all_cases.extend(data)
        print(f"  {label:<30} {len(data):5d} cases  ({path})")

    total_cases = len(all_cases)
    print(f"\nTotal: {total_cases} cases across 18 policies\n")

    hybrid_rag.retrieve("warmup", n_results=1)
    print("Retriever ready.\n")

    by_policy  = defaultdict(lambda: {"pass": 0, "fail": 0, "total": 0})
    by_suite   = defaultdict(lambda: {"pass": 0, "fail": 0, "total": 0})
    total_pass = 0
    failures   = []

    t0 = time.time()
    for i, case in enumerate(all_cases):
        chunks = hybrid_rag.retrieve(case["query"], n_results=TOP_K)
        fmt    = case["_fmt"]

        if fmt == "old":
            kf  = case["keyFacts"]
            src = case["source"]
            ok, missing = check_old(chunks, kf)
        else:
            kf  = case["key_facts"]
            src = case.get("policy", "?")
            ok, missing = check_new(chunks, kf)

        suite = case["_suite"]
        by_policy[src]["total"]  += 1
        by_suite[suite]["total"] += 1

        if ok:
            total_pass += 1
            by_policy[src]["pass"]  += 1
            by_suite[suite]["pass"] += 1
        else:
            by_policy[src]["fail"]  += 1
            by_suite[suite]["fail"] += 1
            failures.append({
                "id":      case.get("id", "?"),
                "query":   case["query"],
                "source":  src,
                "suite":   suite,
                "category": case.get("category", "?"),
                "missing": missing,
            })

        if (i + 1) % 1000 == 0 or i == total_cases - 1:
            acc = total_pass / (i + 1) * 100
            elapsed_so_far = time.time() - t0
            print(f"  [{i+1:6d}/{total_cases}]  running acc = {acc:.2f}%  ({elapsed_so_far:.0f}s)", flush=True)

    elapsed = time.time() - t0
    pct     = total_pass / total_cases * 100

    SEP = "=" * 72
    print(f"\n{SEP}")
    print(f"FULL-18 BENCHMARK — ARVIND HR  ({total_cases} cases, {elapsed:.0f}s)")
    print(SEP)
    print(f"Passed  : {total_pass}")
    print(f"Failed  : {total_cases - total_pass}")
    print(f"OVERALL : {pct:.2f}%")

    print(f"\n{SEP}")
    print("ACCURACY BY POLICY")
    print(SEP)
    print(f"  {'Policy':<55} {'Pass':>5} {'Total':>5}  {'Fail':>5}  {'Acc':>6}")
    print(f"  {'-'*55} {'-'*5} {'-'*5}  {'-'*5}  {'-'*6}")
    for pol in sorted(by_policy, key=lambda p: by_policy[p]["pass"] / by_policy[p]["total"]):
        v   = by_policy[pol]
        acc = v["pass"] / v["total"] * 100
        print(f"  {pol:<55} {v['pass']:>5} {v['total']:>5}  {v['fail']:>5}  {acc:>5.1f}%")

    print(f"\n{SEP}")
    print("ACCURACY BY SUITE")
    print(SEP)
    for _, label, _ in SUITES:
        v = by_suite.get(label)
        if not v or v["total"] == 0:
            continue
        acc = v["pass"] / v["total"] * 100
        print(f"  {label:<30} {v['pass']:5d}/{v['total']:<5d}  {acc:.2f}%")

    with open("full18_failures.json", "w") as f:
        json.dump(failures[:500], f, indent=2)

    print(f"\nFailures saved → full18_failures.json (capped 500)")
    print(f"\nFINAL OVERALL ACCURACY: {pct:.2f}%")


if __name__ == "__main__":
    run()
