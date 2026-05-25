"""
Benchmark MediBuddy Health & Wellness (User Manual) — 95 test cases.
"""
import json, re, time
from collections import defaultdict
import hybrid_rag

SUITE_FILE = "medibuddy_test_suite.json"
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
    return any(normalise(kf) in combined for kf in key_facts)


def run():
    with open(SUITE_FILE) as f:
        suite = json.load(f)

    passed = failed = 0
    by_cat = defaultdict(lambda: [0, 0])
    failures = []

    t0 = time.time()
    for i, case in enumerate(suite, 1):
        q = case["query"]
        kf = case["key_facts"]
        cat = case.get("category", "?")
        chunks = hybrid_rag.retrieve(q, n_results=TOP_K)
        ok = check_keyfacts(chunks, kf)
        if ok:
            passed += 1
            by_cat[cat][0] += 1
        else:
            failed += 1
            by_cat[cat][1] += 1
            failures.append({"query": q, "key_facts": kf, "category": cat,
                             "retrieved": [c["text"][:120] for c in chunks[:3]]})
        if i % 20 == 0:
            print(f"  {i}/{len(suite)} done…")

    elapsed = int(time.time() - t0)
    total = passed + failed
    acc = 100.0 * passed / total if total else 0

    print(f"\n{'='*60}")
    print(f"MediBuddy Benchmark — {total} cases")
    print(f"{'='*60}")
    print(f"Passed  : {passed}")
    print(f"Failed  : {failed}")
    print(f"Accuracy: {acc:.1f}%   (elapsed {elapsed}s)")

    print(f"\n{'='*60}")
    print("BY CATEGORY")
    print(f"{'='*60}")
    for cat, (p, f_) in sorted(by_cat.items()):
        t = p + f_
        print(f"  {cat:<30} {p}/{t:>3}  ({100*p/t:.0f}%)")

    if failures:
        with open("medibuddy_failures.json", "w") as fp:
            json.dump(failures[:50], fp, indent=2)
        print(f"\nTop failures → medibuddy_failures.json ({len(failures)} total)")

    return acc


if __name__ == "__main__":
    run()
