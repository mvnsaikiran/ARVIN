"""
Fast benchmark: Baseline  vs  LlamaIndex-MQQ  on holdout sets only.

Runs on:
  1. Semantic holdout   (~1887 cases, mostly policy-detected → fast)
  2. Adversarial holdout (73 clean cases, all cross-policy → Gemini called)

Training accuracy is derived mathematically:
  LlamaQQ training ≈ Baseline training since 90.2% of training queries
  are policy-detected and take the identical path.
"""

import json, re, time
from collections import defaultdict
import hybrid_rag
import hybrid_rag_llamaqq

TOP_K = 10


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


def eval_case(retrieve_fn, case: dict, logic: str = "any") -> bool:
    chunks = retrieve_fn(case["query"], TOP_K)
    if "key_facts" in case:
        return check_any(chunks, case["key_facts"])
    return check_all(chunks, case["keyFacts"]) if logic == "all" else check_any(chunks, case["keyFacts"])


def run_holdout(label: str, cases: list[dict], logic: str = "any",
                verbose: bool = True) -> dict:
    b_pass = l_pass = 0
    by_pol_b: dict = defaultdict(lambda: {"pass": 0, "total": 0})
    by_pol_l: dict = defaultdict(lambda: {"pass": 0, "total": 0})
    t0 = time.time()

    for i, case in enumerate(cases):
        pol = case.get("policy", case.get("source", "?"))

        b_ok = eval_case(hybrid_rag.retrieve,         case, logic)
        l_ok = eval_case(hybrid_rag_llamaqq.retrieve,  case, logic)

        by_pol_b[pol]["total"] += 1
        by_pol_l[pol]["total"] += 1
        if b_ok:
            b_pass += 1
            by_pol_b[pol]["pass"] += 1
        if l_ok:
            l_pass += 1
            by_pol_l[pol]["pass"] += 1

        if verbose and ((i + 1) % 100 == 0 or i == len(cases) - 1 or len(cases) < 100):
            ba = b_pass / (i + 1) * 100
            la = l_pass / (i + 1) * 100
            marker = "✓" if b_ok else "✗"
            lmarker = "✓" if l_ok else "✗"
            print(f"  [{i+1:3d}/{len(cases)}]  "
                  f"Base={ba:.1f}%({marker})  "
                  f"Llama={la:.1f}%({lmarker})  "
                  f"[{pol[:40]}]", flush=True)

    total   = len(cases)
    b_pct   = b_pass / total * 100 if total else 0
    l_pct   = l_pass / total * 100 if total else 0
    elapsed = time.time() - t0

    print(f"\n  >> {label}:  Baseline={b_pct:.2f}%   LlamaQQ={l_pct:.2f}%"
          f"   delta={l_pct - b_pct:+.2f}pp   ({elapsed:.0f}s)\n")

    return {
        "label":    label,
        "total":    total,
        "b_pass":   b_pass,  "b_pct":  b_pct,
        "l_pass":   l_pass,  "l_pct":  l_pct,
        "by_pol_b": dict(by_pol_b),
        "by_pol_l": dict(by_pol_l),
    }


def main():
    print("Warming up retrievers...")
    hybrid_rag.retrieve("warmup", n_results=1)
    hybrid_rag_llamaqq.retrieve("warmup", n_results=1)
    print("All retrievers warmed up.\n")

    # ── Semantic holdout ─────────────────────────────────────────────────────
    print("=" * 72)
    print("SEMANTIC HOLDOUT")
    print("=" * 72)
    with open("semantic_holdout.json") as f:
        sem_cases = json.load(f)
    print(f"Cases: {len(sem_cases)}\n")
    sem_r = run_holdout("Semantic Holdout", sem_cases, logic="any", verbose=False)

    # ── Adversarial holdout ──────────────────────────────────────────────────
    print("=" * 72)
    print("ADVERSARIAL HOLDOUT  (73 clean plain-English cases)")
    print("=" * 72)
    with open("adversarial_holdout_clean.json") as f:
        adv_cases = json.load(f)
    print(f"Cases: {len(adv_cases)}\n")
    adv_r = run_holdout("Adversarial Holdout", adv_cases, logic="any", verbose=True)

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("OVERALL SUMMARY")
    print("=" * 72)
    print(f"{'Variant':<30} {'Training':>10} {'Semantic HO':>13} {'Adversarial':>13}")
    print("-" * 70)
    print(f"{'Baseline (96.58%)':<30} {'96.58%':>10} "
          f"{sem_r['b_pct']:>12.2f}%  {adv_r['b_pct']:>12.2f}%")
    print(f"{'LlamaQQ':<30} {'~96.58%*':>10} "
          f"{sem_r['l_pct']:>12.2f}%  {adv_r['l_pct']:>12.2f}%")
    print(f"\n  * LlamaQQ training ≈ Baseline: 90.2% of training queries are policy-")
    print(f"    detected and take the identical path. Only 9.8% trigger Gemini.")

    # ── Policy-wise adversarial ──────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("POLICY-WISE ADVERSARIAL ACCURACY")
    print("=" * 72)
    print(f"{'Policy':<55} {'Baseline':>10} {'LlamaQQ':>10} {'Delta':>8}")
    print("-" * 88)
    pols = sorted(set(list(adv_r["by_pol_b"].keys()) + list(adv_r["by_pol_l"].keys())))
    for pol in pols:
        vb = adv_r["by_pol_b"].get(pol, {"pass": 0, "total": 0})
        vl = adv_r["by_pol_l"].get(pol, {"pass": 0, "total": 0})
        ab = vb["pass"] / vb["total"] * 100 if vb["total"] else 0
        al = vl["pass"] / vl["total"] * 100 if vl["total"] else 0
        delta = al - ab
        flag = f"{delta:+.1f}pp" if abs(delta) > 0.5 else "  same"
        print(f"  {pol:<55} {ab:>8.1f}%  {al:>8.1f}%  {flag:>7}")

    # Failure analysis for adversarial
    print("\n" + "=" * 72)
    print("ADVERSARIAL FAILURES  (LlamaQQ misses but Baseline hits, or vice versa)")
    print("=" * 72)
    print(f"{'Query':<55} {'B':>3} {'L':>3} {'Policy'}")
    print("-" * 80)
    # re-run to collect per-case results
    b_results = []
    l_results = []
    for case in adv_cases:
        chunks_b = hybrid_rag.retrieve(case["query"], TOP_K)
        chunks_l = hybrid_rag_llamaqq.retrieve(case["query"], TOP_K)
        kf = case.get("key_facts", case.get("keyFacts", []))
        pol = case.get("policy", "?")
        combined_b = " ".join(normalise(c["text"]) for c in chunks_b)
        combined_l = " ".join(normalise(c["text"]) for c in chunks_l)
        b_ok = any(normalise(kf_) in combined_b for kf_ in kf if normalise(kf_))
        l_ok = any(normalise(kf_) in combined_l for kf_ in kf if normalise(kf_))
        if b_ok != l_ok:
            b_sym = "✓" if b_ok else "✗"
            l_sym = "✓" if l_ok else "✗"
            print(f"  {case['query'][:55]:<55} {b_sym:>3} {l_sym:>3}  {pol[:35]}")


if __name__ == "__main__":
    main()
