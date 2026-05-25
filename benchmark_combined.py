"""
Combined benchmark: original 8 policies (enterprise_test_suite.json)
                  + batch-1 5 policies (new_policies_test_suite.json)
                  + batch-2 4 policies (batch2_test_suite.json)
Total: 17 policies, ~10,752 cases.
"""
import json, re, time
from collections import defaultdict
import hybrid_rag

SUITES = [
    ("enterprise_test_suite.json",      "Original-8"),
    ("new_policies_test_suite.json",    "Batch-1"),
    ("batch2_test_suite.json",          "Batch-2"),
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


def check_keyfacts(chunks, key_facts):
    combined = " ".join(normalise(c["text"]) for c in chunks)
    missing = [kf for kf in key_facts if normalise(kf) and normalise(kf) not in combined]
    return len(missing) == 0, missing


def run():
    # Load all suites
    all_cases = []
    for path, label in SUITES:
        with open(path) as f:
            cases = json.load(f)
        for c in cases:
            c["_suite"] = label
        all_cases.extend(cases)
        print(f"  {label}: {len(cases)} cases from {path}")
    print(f"Total: {len(all_cases)} cases across 17 policies\n")

    # Warm up
    hybrid_rag.retrieve("warmup query", n_results=1)
    print("Retriever ready.\n")

    by_policy  = defaultdict(lambda: {"pass": 0, "total": 0})
    by_suite   = defaultdict(lambda: {"pass": 0, "total": 0})
    total_pass = 0
    failures   = []

    t0 = time.time()
    for i, case in enumerate(all_cases):
        chunks  = hybrid_rag.retrieve(case["query"], n_results=TOP_K)
        ok, missing = check_keyfacts(chunks, case["keyFacts"])
        src   = case["source"]
        suite = case["_suite"]

        by_policy[src]["total"]  += 1
        by_suite[suite]["total"] += 1

        if ok:
            total_pass += 1
            by_policy[src]["pass"]  += 1
            by_suite[suite]["pass"] += 1
        else:
            failures.append({
                "id":      case.get("id", "?"),
                "query":   case["query"],
                "source":  src,
                "suite":   suite,
                "missing": missing,
            })

        if (i + 1) % 500 == 0 or i == len(all_cases) - 1:
            acc = total_pass / (i + 1) * 100
            print(f"  [{i+1:5d}/{len(all_cases)}]  running acc = {acc:.2f}%", flush=True)

    elapsed = time.time() - t0
    total   = len(all_cases)
    pct     = total_pass / total * 100

    print(f"\n{'='*68}")
    print(f"COMBINED BENCHMARK — ARVIND HR PULSE (17 policies)")
    print(f"{'='*68}")
    print(f"Total cases  : {total}")
    print(f"Passed       : {total_pass}")
    print(f"Failed       : {total - total_pass}")
    print(f"OVERALL ACC  : {pct:.2f}%   (elapsed {elapsed:.0f}s)")

    print(f"\n{'='*68}")
    print(f"ACCURACY BY BATCH")
    print(f"{'='*68}")
    for suite, label in [("Original-8","Original 8 policies"),
                         ("Batch-1",  "Batch 1 (5 new)"),
                         ("Batch-2",  "Batch 2 (4 new)")]:
        v = by_suite[suite]
        if v["total"] == 0:
            continue
        a = v["pass"] / v["total"] * 100
        print(f"  {label:<30} {v['pass']:5d}/{v['total']:5d}  ({a:.2f}%)")

    print(f"\n{'='*68}")
    print(f"ACCURACY BY POLICY")
    print(f"{'='*68}")
    for pol in sorted(by_policy):
        v = by_policy[pol]
        a = v["pass"] / v["total"] * 100
        bar = "#" * int(a / 5)
        print(f"  {pol:<52} {v['pass']:4d}/{v['total']:4d}  ({a:.1f}%)")

    # Save failures
    with open("combined_failures.json", "w") as f:
        json.dump(failures[:200], f, indent=2)
    print(f"\nTop failures saved → combined_failures.json")
    print(f"\nFINAL OVERALL ACCURACY: {pct:.2f}%")


if __name__ == "__main__":
    run()
