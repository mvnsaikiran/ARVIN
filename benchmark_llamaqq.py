"""
Two-way benchmark: Baseline hybrid_rag  vs  LlamaIndex-MQQ hybrid_rag_llamaqq

Runs on:
  1. Full training set  (~10847 cases, batched: only cross-policy tested via LlamaQQ)
  2. Semantic holdout   (~1887 cases)
  3. Adversarial holdout (73 clean cases)

Training optimisation: policy-detected queries (90%) are identical for both
retrievers → only call LlamaQQ for cross-policy queries; for policy-detected
queries count both as equal.
"""

import json, re, time
from collections import defaultdict
import hybrid_rag
import hybrid_rag_llamaqq
from hybrid_rag import _detect_policy

TOP_K = 10

TRAINING_SUITES = [
    ("enterprise_test_suite.json",   "Original-8"),
    ("new_policies_test_suite.json", "Batch-1"),
    ("batch2_test_suite.json",       "Batch-2"),
]


def normalise(t: str) -> str:
    t = t.lower()
    t = re.sub(r'rs\.?\s*', '', t)
    t = re.sub(r'₹\s*', '', t)
    t = re.sub(r'/-', '', t)
    t = re.sub(r',', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def check_any(chunks, key_facts) -> bool:
    combined = " ".join(normalise(c["text"]) for c in chunks)
    return any(normalise(kf) in combined for kf in key_facts if normalise(kf))


def check_all(chunks, key_facts) -> bool:
    combined = " ".join(normalise(c["text"]) for c in chunks)
    return all(normalise(kf) in combined for kf in key_facts if normalise(kf))


def eval_case(retrieve_fn, case: dict, logic: str = "all") -> bool:
    chunks = retrieve_fn(case["query"], TOP_K)
    if "key_facts" in case:
        return check_any(chunks, case["key_facts"])
    return check_all(chunks, case["keyFacts"]) if logic == "all" else check_any(chunks, case["keyFacts"])


def run_suite_holdout(label: str, cases: list[dict], logic: str = "any") -> dict:
    """Run both retrievers on every case (used for small holdout sets)."""
    b_pass = l_pass = 0
    by_pol_b: dict = defaultdict(lambda: {"pass": 0, "total": 0})
    by_pol_l: dict = defaultdict(lambda: {"pass": 0, "total": 0})

    t0 = time.time()
    for i, case in enumerate(cases):
        pol = case.get("policy", case.get("source", "?"))

        b_ok = eval_case(hybrid_rag.retrieve, case, logic)
        l_ok = eval_case(hybrid_rag_llamaqq.retrieve, case, logic)

        by_pol_b[pol]["total"] += 1
        by_pol_l[pol]["total"] += 1
        if b_ok:
            b_pass += 1
            by_pol_b[pol]["pass"] += 1
        if l_ok:
            l_pass += 1
            by_pol_l[pol]["pass"] += 1

        print(f"  [{i+1:3d}/{len(cases)}]  "
              f"Baseline={b_pass/(i+1)*100:.1f}%  "
              f"LlamaQQ={l_pass/(i+1)*100:.1f}%"
              f"  ({'✓' if b_ok else '✗'}B {'✓' if l_ok else '✗'}L)"
              f"  [{pol[:35]}]", flush=True)

    total   = len(cases)
    b_pct   = b_pass / total * 100 if total else 0
    l_pct   = l_pass / total * 100 if total else 0
    elapsed = time.time() - t0

    print(f"\n  RESULT  Baseline={b_pct:.2f}%   LlamaQQ={l_pct:.2f}%"
          f"   delta={l_pct - b_pct:+.2f}pp   ({elapsed:.0f}s)")

    return {
        "label":    label,
        "total":    total,
        "b_pass":   b_pass,  "b_pct":  b_pct,
        "l_pass":   l_pass,  "l_pct":  l_pct,
        "by_pol_b": dict(by_pol_b),
        "by_pol_l": dict(by_pol_l),
    }


def run_training_optimised(cases: list[dict]) -> dict:
    """
    Optimised training run:
    - Policy-detected queries: run Baseline only; LlamaQQ is identical for these.
    - Cross-policy queries:     run both (LlamaQQ calls Gemini for these).
    """
    b_pass = l_pass = 0
    cross_b = cross_l = cross_total = 0
    total = len(cases)
    t0 = time.time()

    for i, case in enumerate(cases):
        pol = case.get("source", "?")
        is_cross = not bool(_detect_policy(case["query"]))

        b_ok = eval_case(hybrid_rag.retrieve, case, "all")
        if is_cross:
            l_ok = eval_case(hybrid_rag_llamaqq.retrieve, case, "all")
            cross_total += 1
            if b_ok:
                cross_b += 1
            if l_ok:
                cross_l += 1
        else:
            l_ok = b_ok   # identical path

        if b_ok:
            b_pass += 1
        if l_ok:
            l_pass += 1

        if (i + 1) % 500 == 0 or i == total - 1:
            print(f"  [{i+1:5d}/{total}]  "
                  f"Baseline={b_pass/(i+1)*100:.2f}%  "
                  f"LlamaQQ={l_pass/(i+1)*100:.2f}%  "
                  f"cross_tested={cross_total}", flush=True)

    elapsed = time.time() - t0
    b_pct = b_pass / total * 100
    l_pct = l_pass / total * 100
    cross_b_pct = cross_b / cross_total * 100 if cross_total else 0
    cross_l_pct = cross_l / cross_total * 100 if cross_total else 0

    print(f"\n  OVERALL  Baseline={b_pct:.2f}%   LlamaQQ={l_pct:.2f}%"
          f"   delta={l_pct - b_pct:+.2f}pp   ({elapsed:.0f}s)")
    print(f"  Cross-policy subset ({cross_total} cases):"
          f"  Baseline={cross_b_pct:.2f}%   LlamaQQ={cross_l_pct:.2f}%")

    return {
        "label": "Training", "total": total,
        "b_pass": b_pass, "b_pct": b_pct,
        "l_pass": l_pass, "l_pct": l_pct,
        "by_pol_b": {}, "by_pol_l": {},
    }


def main():
    print("Warming up retrievers...")
    hybrid_rag.retrieve("warmup", n_results=1)
    hybrid_rag_llamaqq.retrieve("warmup", n_results=1)
    print("Done.\n")

    results = []

    # ── 1. Training ──────────────────────────────────────────────────────────
    print("=" * 72)
    print("TRAINING SET  (optimised: Gemini called only for cross-policy)")
    print("=" * 72)
    training_cases = []
    for path, lbl in TRAINING_SUITES:
        with open(path) as f:
            cs = json.load(f)
        training_cases.extend(cs)
    print(f"Total training cases: {len(training_cases)}\n")
    r = run_training_optimised(training_cases)
    results.append(r)

    # ── 2. Semantic holdout ──────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("SEMANTIC HOLDOUT")
    print("=" * 72)
    with open("semantic_holdout.json") as f:
        sem_cases = json.load(f)
    print(f"Total semantic cases: {len(sem_cases)}\n")
    r = run_suite_holdout("Semantic HO", sem_cases, logic="any")
    results.append(r)

    # ── 3. Adversarial holdout ───────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("ADVERSARIAL HOLDOUT (73 clean plain-English cases)")
    print("=" * 72)
    with open("adversarial_holdout_clean.json") as f:
        adv_cases = json.load(f)
    print(f"Total adversarial cases: {len(adv_cases)}\n")
    r = run_suite_holdout("Adversarial", adv_cases, logic="any")
    results.append(r)

    # ── Overall summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("OVERALL SUMMARY")
    print("=" * 72)
    print(f"{'Variant':<30} {'Training':>10} {'Semantic HO':>13} {'Adversarial':>13}")
    print("-" * 70)
    train_r, sem_r, adv_r = results

    print(f"{'Baseline (96.58%)':<30} "
          f"{train_r['b_pct']:>9.2f}%  "
          f"{sem_r['b_pct']:>12.2f}%  "
          f"{adv_r['b_pct']:>12.2f}%")
    print(f"{'LlamaQQ':<30} "
          f"{train_r['l_pct']:>9.2f}%  "
          f"{sem_r['l_pct']:>12.2f}%  "
          f"{adv_r['l_pct']:>12.2f}%")

    # ── Policy-wise adversarial ──────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("POLICY-WISE ADVERSARIAL ACCURACY")
    print("=" * 72)
    print(f"{'Policy':<55} {'Baseline':>10} {'LlamaQQ':>10}")
    print("-" * 78)
    pols = sorted(set(list(adv_r["by_pol_b"].keys()) + list(adv_r["by_pol_l"].keys())))
    for pol in pols:
        vb = adv_r["by_pol_b"].get(pol, {"pass": 0, "total": 0})
        vl = adv_r["by_pol_l"].get(pol, {"pass": 0, "total": 0})
        ab = vb["pass"] / vb["total"] * 100 if vb["total"] else 0
        al = vl["pass"] / vl["total"] * 100 if vl["total"] else 0
        delta = al - ab
        flag = f"  +{delta:.1f}pp" if delta > 1 else (f"  {delta:.1f}pp" if delta < -1 else "")
        print(f"  {pol:<55} {ab:>8.1f}%  {al:>8.1f}%{flag}")


if __name__ == "__main__":
    main()
