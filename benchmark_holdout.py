"""
Benchmark on holdout sets produced by Method 2 and Method 3.

Usage:
  python benchmark_holdout.py --adversarial    # benchmark adversarial_holdout.json
  python benchmark_holdout.py --semantic       # benchmark semantic_holdout.json
  python benchmark_holdout.py --both           # both
  python benchmark_holdout.py                  # both (default)

Each file uses "new" format: {query, key_facts, policy, ...}
The adversarial file uses OR-logic (any key_fact found → pass).
The semantic file preserves original format and logic.
"""

import argparse, json, re, time
from collections import defaultdict
import hybrid_rag

TOP_K = 10


def normalise(t: str) -> str:
    t = t.lower()
    t = re.sub(r'rs\.?\s*', '', t)
    t = re.sub(r'₹\s*', '', t)
    t = re.sub(r'/-', '', t)
    t = re.sub(r',', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def check_any(chunks: list[dict], key_facts: list[str]) -> tuple[bool, list]:
    """OR logic: pass if any key_fact found in combined chunk text."""
    combined = " ".join(normalise(c["text"]) for c in chunks)
    found = any(normalise(kf) in combined for kf in key_facts if normalise(kf))
    return found, [] if found else key_facts


def check_all(chunks: list[dict], key_facts: list[str]) -> tuple[bool, list]:
    """AND logic: pass only if ALL key_facts found."""
    combined = " ".join(normalise(c["text"]) for c in chunks)
    missing = [kf for kf in key_facts if normalise(kf) and normalise(kf) not in combined]
    return len(missing) == 0, missing


def run_benchmark(path: str, label: str, logic: str = "any") -> dict:
    """Run benchmark on a single file. logic='any' or 'all'."""
    print(f"\n{'='*68}")
    print(f"BENCHMARK: {label}  [{path}]")
    print(f"{'='*68}")

    try:
        with open(path) as f:
            cases = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {path} not found. Run the generator first.")
        return {}

    print(f"Cases: {len(cases)}  |  Logic: {logic.upper()}")

    # Detect format: new format has 'key_facts' and 'policy'
    # old format has 'keyFacts' and 'source'
    def get_kf_pol(c):
        if "key_facts" in c:
            return c["key_facts"], c.get("policy", "?"), "new"
        elif "keyFacts" in c:
            return c["keyFacts"], c.get("source", "?"), "old"
        else:
            return [], "?", "?"

    by_policy = defaultdict(lambda: {"pass": 0, "total": 0})
    total_pass = 0
    failures   = []
    t0 = time.time()

    for i, case in enumerate(cases):
        chunks = hybrid_rag.retrieve(case["query"], n_results=TOP_K)
        kf, pol, fmt = get_kf_pol(case)

        # For semantic holdout with mixed formats, respect original format
        if logic == "auto":
            ok, missing = (check_any if fmt == "new" else check_all)(chunks, kf)
        elif logic == "any":
            ok, missing = check_any(chunks, kf)
        else:
            ok, missing = check_all(chunks, kf)

        by_policy[pol]["total"] += 1
        if ok:
            total_pass += 1
            by_policy[pol]["pass"] += 1
        else:
            failures.append({
                "query":   case["query"],
                "policy":  pol,
                "missing": missing,
            })

        if (i + 1) % 200 == 0 or i == len(cases) - 1:
            acc = total_pass / (i + 1) * 100
            print(f"  [{i+1:5d}/{len(cases)}]  running acc = {acc:.2f}%", flush=True)

    elapsed = time.time() - t0
    total   = len(cases)
    pct     = total_pass / total * 100 if total else 0.0

    print(f"\nFinal: {total_pass}/{total}  =  {pct:.2f}%  (elapsed {elapsed:.0f}s)")
    print(f"\nBy policy:")
    for pol in sorted(by_policy):
        v = by_policy[pol]
        a = v["pass"] / v["total"] * 100
        flag = " ◄ LOW" if a < 80 else ""
        print(f"  {pol:<55} {v['pass']:4d}/{v['total']:4d}  ({a:.1f}%){flag}")

    # Save failures
    out_fail = path.replace(".json", "_failures.json")
    with open(out_fail, "w") as f:
        json.dump(failures, f, indent=2)
    print(f"\nFailures saved → {out_fail}")

    return {"label": label, "total": total, "pass": total_pass, "pct": pct}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adversarial", action="store_true")
    parser.add_argument("--semantic",    action="store_true")
    parser.add_argument("--both",        action="store_true")
    args = parser.parse_args()

    # Default = both
    do_adversarial = args.adversarial or args.both or not (args.adversarial or args.semantic)
    do_semantic    = args.semantic    or args.both or not (args.adversarial or args.semantic)

    hybrid_rag.retrieve("warmup", n_results=1)
    print("Retriever warmed up.\n")

    results = []

    if do_adversarial:
        r = run_benchmark("adversarial_holdout.json", "Adversarial Paraphrase Holdout", logic="any")
        if r:
            results.append(r)

    if do_semantic:
        r = run_benchmark("semantic_holdout.json",    "Semantic Similarity Holdout",    logic="auto")
        if r:
            results.append(r)

    if len(results) >= 2:
        print(f"\n{'='*68}")
        print("SUMMARY — HOLDOUT ACCURACY vs TRAINING ACCURACY")
        print(f"{'='*68}")
        print(f"  {'Set':<40} {'Passed':>8} {'Total':>8} {'Accuracy':>10}")
        print(f"  {'-'*66}")
        for r in results:
            print(f"  {r['label']:<40} {r['pass']:>8} {r['total']:>8} {r['pct']:>9.2f}%")
        print(f"\n  NOTE: Training accuracy (benchmark_all18) ≈ 99%")
        print(f"  Gap between training and holdout = inflated accuracy estimate")


if __name__ == "__main__":
    main()
