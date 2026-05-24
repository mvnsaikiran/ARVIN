"""
Enterprise-scale benchmark for Arvind HR Pulse RAG system.
Tests 8928 cases from enterprise_test_suite.json against hybrid_rag retrieval.

Matching: keyFact (normalised + whitespace-collapsed) must appear in ANY
          returned chunk's normalised+collapsed text.
"""

import json, re, sys, time
from collections import defaultdict
import hybrid_rag

SUITE_FILE = "enterprise_test_suite.json"
TOP_K = 10
BATCH_PRINT = 100  # print progress every N cases


def normalise(t: str) -> str:
    """Normalise text for substring matching."""
    t = t.lower()
    t = re.sub(r'rs\.?\s*', '', t)
    t = re.sub(r'₹\s*', '', t)
    t = re.sub(r'/-', '', t)
    t = re.sub(r',', '', t)
    t = re.sub(r'\s+', ' ', t)   # collapse ALL whitespace (including \n) to single space
    return t.strip()


def check_keyfacts(chunks: list[dict], key_facts: list[str]) -> tuple[bool, list[str]]:
    """
    Returns (passed, missing_facts).
    passed = True if ALL keyFacts appear in the combined retrieved text.
    """
    combined = " ".join(normalise(c["text"]) for c in chunks)
    missing = []
    for kf in key_facts:
        norm_kf = normalise(kf)
        if norm_kf and norm_kf not in combined:
            missing.append(kf)
    return len(missing) == 0, missing


def check_source(chunks: list[dict], expected_source: str) -> bool:
    """Return True if expected_source appears in at least one chunk's policy_name."""
    return any(c["policy_name"] == expected_source for c in chunks)


def run_benchmark():
    print(f"Loading enterprise test suite...", flush=True)
    with open(SUITE_FILE) as f:
        suite = json.load(f)
    total = len(suite)
    print(f"Loaded {total} test cases\n", flush=True)

    # Force-load the retriever once
    print("Warming up retriever...", flush=True)
    hybrid_rag.retrieve("test warmup query", n_results=1)
    print("Retriever ready.\n", flush=True)

    results = []
    cat_stats = defaultdict(lambda: {"total": 0, "pass": 0, "source_pass": 0})
    policy_stats = defaultdict(lambda: {"total": 0, "pass": 0})

    start = time.time()
    failures = []

    for i, tc in enumerate(suite):
        tc_id   = tc.get("id", f"?{i}")
        query   = tc.get("query", "")
        kfacts  = tc.get("keyFacts", [])
        source  = tc.get("source", "")
        cat     = tc.get("category", "unknown")

        chunks = hybrid_rag.retrieve(query, n_results=TOP_K)
        passed, missing = check_keyfacts(chunks, kfacts)
        src_ok = check_source(chunks, source) if source else True

        cat_stats[cat]["total"] += 1
        policy_stats[source]["total"] += 1
        if passed:
            cat_stats[cat]["pass"] += 1
            policy_stats[source]["pass"] += 1
        if src_ok:
            cat_stats[cat]["source_pass"] += 1

        results.append({
            "id": tc_id,
            "passed": passed,
            "source_ok": src_ok,
            "category": cat,
            "source": source,
            "missing": missing,
        })

        if not passed:
            failures.append({
                "id": tc_id, "query": query, "category": cat,
                "source": source, "missing": missing,
            })

        if (i + 1) % BATCH_PRINT == 0 or i == total - 1:
            elapsed = time.time() - start
            done = i + 1
            pct = done / total * 100
            passes = sum(1 for r in results if r["passed"])
            acc = passes / done * 100
            eta = (elapsed / done) * (total - done)
            print(f"  [{done:5d}/{total}] {pct:5.1f}%  acc={acc:.1f}%  "
                  f"elapsed={elapsed:.0f}s  ETA={eta:.0f}s", flush=True)

    elapsed = time.time() - start
    total_pass = sum(1 for r in results if r["passed"])
    total_src  = sum(1 for r in results if r["source_ok"])

    print(f"\n{'='*60}")
    print(f"ENTERPRISE BENCHMARK RESULTS")
    print(f"{'='*60}")
    print(f"Total cases  : {total}")
    print(f"Passed       : {total_pass} ({total_pass/total*100:.1f}%)")
    print(f"Failed       : {total - total_pass} ({(total-total_pass)/total*100:.1f}%)")
    print(f"Source acc   : {total_src}/{total} ({total_src/total*100:.1f}%)")
    print(f"Time         : {elapsed:.0f}s  ({elapsed/total*1000:.1f}ms/case)")

    print(f"\n{'='*60}")
    print(f"BY POLICY (source accuracy / retrieval accuracy)")
    print(f"{'='*60}")
    for pol in sorted(policy_stats):
        s = policy_stats[pol]
        t = s["total"]
        p = s["pass"]
        print(f"  {pol:<45} {p:4d}/{t:4d}  ({p/t*100:5.1f}%)")

    print(f"\n{'='*60}")
    print(f"BY CATEGORY (top 30 by failure count)")
    print(f"{'='*60}")
    cat_rows = sorted(cat_stats.items(), key=lambda x: x[1]["total"] - x[1]["pass"], reverse=True)
    for cat, s in cat_rows[:30]:
        t = s["total"]
        p = s["pass"]
        f = t - p
        sp = s["source_pass"]
        print(f"  {cat:<40} {p:4d}/{t:4d}  ({p/t*100:5.1f}%)  src={sp/t*100:.0f}%  fail={f}")

    # Save failure report
    fail_file = "enterprise_failures.json"
    with open(fail_file, "w") as fout:
        json.dump(failures[:500], fout, indent=2)   # cap at 500 for readability
    print(f"\nFirst {min(len(failures),500)} failures saved → {fail_file}")

    # Sample failures per category
    print(f"\n{'='*60}")
    print(f"SAMPLE FAILURES (up to 2 per category)")
    print(f"{'='*60}")
    shown = defaultdict(int)
    for f in failures:
        cat = f["category"]
        if shown[cat] < 2:
            shown[cat] += 1
            print(f"\n  [{f['id']}] {cat}")
            print(f"  Q: {f['query'][:120]}")
            print(f"  Missing: {f['missing'][:2]}")

    return total_pass / total * 100


if __name__ == "__main__":
    acc = run_benchmark()
    print(f"\nFinal accuracy: {acc:.2f}%")
