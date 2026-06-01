"""
Targeted benchmark for Local Conveyance + GPA — shows ALL failures.
"""
import json, re
from collections import Counter
import hybrid_rag

SUITES = [
    "enterprise_test_suite.json",
    "new_policies_test_suite.json",
    "batch2_test_suite.json",
    "expanded_small_policies_suite.json",
]

TARGET_POLICIES = {
    "Local Conveyance Policy",
    "Group Personal Accident Insurance Scheme",
}

TOP_K = 10


def normalise(t):
    t = t.lower()
    t = re.sub(r'rs\.?\s*', '', t)
    t = re.sub(r'â€"', '-', t)   # fix garbled em-dash
    t = re.sub(r'â€™', "'", t)   # fix garbled apostrophe
    t = re.sub(r'[–—―]', '-', t)  # real em/en dashes → hyphen
    t = re.sub(r'₹\s*', '', t)
    t = re.sub(r'/\s*-\s*', '', t)  # handles both "/- " and "/ - " (LCP rate format)
    t = re.sub(r',', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def run():
    cases = []
    for path in SUITES:
        try:
            data = json.load(open(path))
        except FileNotFoundError:
            continue
        for c in data:
            src = c.get("source") or c.get("policy", "?")
            if src in TARGET_POLICIES:
                cases.append(c)

    print(f"Loaded {len(cases)} cases for target policies\n")
    hybrid_rag.retrieve("warmup", n_results=1, rerank=False)

    all_failures = []
    by_policy = {p: {"pass": 0, "fail": 0, "cats": []} for p in TARGET_POLICIES}

    for c in cases:
        src  = c.get("source") or c.get("policy", "?")
        kf   = c.get("keyFacts", c.get("key_facts", []))
        cat  = c.get("category", "?")
        chunks = hybrid_rag.retrieve(c["query"], n_results=TOP_K, rerank=False)
        combined = " ".join(normalise(ch["text"]) for ch in chunks)
        missing = [k for k in kf if normalise(k) not in combined]
        if missing:
            by_policy[src]["fail"] += 1
            by_policy[src]["cats"].append(cat)
            all_failures.append({
                "query":    c["query"],
                "source":   src,
                "category": cat,
                "missing":  missing,
            })
        else:
            by_policy[src]["pass"] += 1

    for pol in TARGET_POLICIES:
        v     = by_policy[pol]
        total = v["pass"] + v["fail"]
        acc   = v["pass"] / total * 100 if total else 0
        print(f"=== {pol} ===")
        print(f"  {v['pass']}/{total}  ({acc:.1f}%)")
        cat_counts = Counter(v["cats"])
        print(f"  Failure categories:")
        for cat, n in cat_counts.most_common():
            print(f"    {n:3d}  {cat}")
        print()

    for pol in TARGET_POLICIES:
        pol_fails = [f for f in all_failures if f["source"] == pol]
        print(f"\n{'='*60}")
        print(f"ALL FAILURES — {pol}")
        print(f"{'='*60}")
        for i, f in enumerate(pol_fails, 1):
            print(f"  [{i:3d}] [{f['category']}]  {f['query']}")
            print(f"        Missing: {f['missing']}")


if __name__ == "__main__":
    run()
