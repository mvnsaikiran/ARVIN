"""
Evaluation script for ARVIN policy chatbot.
Runs test questions, scores retrieval + routing + answer quality.

Usage:
    python eval/run_eval.py --policy whistleblower
    python eval/run_eval.py --policy whistleblower --verbose
    python eval/run_eval.py --policy whistleblower --output eval/results.json
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from router import route, detect_policy


# ── Scoring helpers ───────────────────────────────────────────────────────────

def score_routing(result: dict, test: dict) -> tuple[bool, str]:
    """Did the router send this to the right policy (or correctly reject it)?"""
    matched = result.get("matched", False)
    expected = test["expected_routed"]
    correct = matched == expected
    note = ""
    if not correct:
        if expected and not matched:
            note = "MISS — should have routed to policy"
        else:
            note = "FALSE POSITIVE — should have been rejected"
    return correct, note


def score_answer(answer_text: str, test: dict) -> tuple[bool, list[str], list[str]]:
    """
    Check if expected keywords appear in the answer.
    Returns (pass, found_keywords, missing_keywords).
    Out-of-scope questions (no expected_keywords) always pass if answer exists.
    """
    expected_kws = test.get("expected_keywords", [])
    if not expected_kws:
        return True, [], []

    text_lower = answer_text.lower()
    found   = [kw for kw in expected_kws if kw.lower() in text_lower]
    missing = [kw for kw in expected_kws if kw.lower() not in text_lower]

    # Pass if at least 60% of expected keywords found
    pass_threshold = 0.6
    ratio = len(found) / len(expected_kws) if expected_kws else 1.0
    passed = ratio >= pass_threshold
    return passed, found, missing


def score_hallucination(answer_text: str, test: dict) -> bool:
    """
    Rough hallucination check: answer should NOT contain confident claims
    about topics not in the policy (very basic signal only).
    """
    hallucination_signals = [
        "as per the leave policy",
        "as per the travel policy",
        "salary",
        "bonus amount",
        "paris",
    ]
    text_lower = answer_text.lower()
    return not any(sig in text_lower for sig in hallucination_signals)


# ── Main eval loop ────────────────────────────────────────────────────────────

def run_eval(testset_path: str, verbose: bool = False) -> dict:
    with open(testset_path, encoding='utf-8') as f:
        tests = json.load(f)

    results = []
    total = len(tests)
    passed_routing  = 0
    passed_answer   = 0
    passed_no_halluc = 0
    total_in_scope  = sum(1 for t in tests if t["expected_routed"])
    total_oos       = sum(1 for t in tests if not t["expected_routed"])

    print(f"\n{'='*60}")
    print(f"  ARVIN Eval — Whistleblower Policy")
    print(f"  {total} test cases  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    for i, test in enumerate(tests, 1):
        qid      = test["id"]
        question = test["question"]
        category = test["category"]
        diff     = test["difficulty"]

        print(f"[{i:02d}/{total}] {qid} ({diff}) — {question[:65]}...")

        # Small delay between in-scope questions to respect Groq free-tier rate limits
        if test["expected_routed"] and i > 1:
            time.sleep(2)

        t0 = time.time()
        try:
            result = route(question, [])
            elapsed = time.time() - t0
        except Exception as e:
            print(f"         ERROR: {e}\n")
            results.append({
                "id": qid, "question": question, "category": category,
                "difficulty": diff, "error": str(e),
                "routing_pass": False, "answer_pass": False, "halluc_pass": False,
            })
            continue

        answer_text = result.get("text", "")

        # Score dimensions
        routing_ok, routing_note  = score_routing(result, test)
        answer_ok, found_kws, missing_kws = score_answer(answer_text, test)
        halluc_ok = score_hallucination(answer_text, test)

        if routing_ok:   passed_routing  += 1
        if answer_ok:    passed_answer   += 1
        if halluc_ok:    passed_no_halluc += 1

        status_r = "✓" if routing_ok  else "✗"
        status_a = "✓" if answer_ok   else "✗"
        status_h = "✓" if halluc_ok   else "✗"

        print(f"         Route:{status_r}  Answer:{status_a}  Halluc:{status_h}  "
              f"({elapsed:.1f}s)")

        if verbose or not (routing_ok and answer_ok):
            if routing_note:
                print(f"         ROUTING: {routing_note}")
            if missing_kws:
                print(f"         MISSING KWS: {missing_kws}")
            if not answer_ok and test["expected_routed"]:
                snippet = answer_text[:200].replace('\n', ' ')
                print(f"         ANSWER SNIPPET: {snippet}...")
        print()

        results.append({
            "id":            qid,
            "question":      question,
            "category":      category,
            "difficulty":    diff,
            "routing_pass":  routing_ok,
            "answer_pass":   answer_ok,
            "halluc_pass":   halluc_ok,
            "routing_note":  routing_note,
            "found_keywords":   found_kws,
            "missing_keywords": missing_kws,
            "answer_snippet":   answer_text[:300],
            "latency_s":     round(elapsed, 2),
        })

    # ── Summary ───────────────────────────────────────────────────────────────
    routing_acc = passed_routing   / total * 100
    answer_acc  = passed_answer    / total * 100
    halluc_acc  = passed_no_halluc / total * 100

    # In-scope answer accuracy (only tests where routing was expected)
    in_scope_results = [r for r in results if tests[results.index(r)]["expected_routed"]]
    in_scope_answer_pass = sum(1 for r in in_scope_results if r.get("answer_pass"))
    in_scope_acc = in_scope_answer_pass / total_in_scope * 100 if total_in_scope else 0

    # Out-of-scope rejection accuracy
    oos_results = [r for r in results if not tests[results.index(r)]["expected_routed"]]
    oos_pass = sum(1 for r in oos_results if r.get("routing_pass"))
    oos_acc  = oos_pass / total_oos * 100 if total_oos else 0

    # Per-difficulty breakdown
    diff_groups = {}
    for r, t in zip(results, tests):
        d = t["difficulty"]
        diff_groups.setdefault(d, {"total": 0, "pass": 0})
        diff_groups[d]["total"] += 1
        if r.get("routing_pass") and r.get("answer_pass"):
            diff_groups[d]["pass"] += 1

    # Per-category breakdown
    cat_groups = {}
    for r, t in zip(results, tests):
        c = t["category"]
        cat_groups.setdefault(c, {"total": 0, "pass": 0})
        cat_groups[c]["total"] += 1
        if r.get("routing_pass") and r.get("answer_pass"):
            cat_groups[c]["pass"] += 1

    avg_latency = sum(r.get("latency_s", 0) for r in results) / total

    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"  Total test cases        : {total}")
    print(f"  Routing accuracy        : {passed_routing}/{total}  ({routing_acc:.1f}%)")
    print(f"  Answer accuracy (all)   : {passed_answer}/{total}  ({answer_acc:.1f}%)")
    print(f"  In-scope answer acc     : {in_scope_answer_pass}/{total_in_scope}  ({in_scope_acc:.1f}%)")
    print(f"  OOS rejection accuracy  : {oos_pass}/{total_oos}  ({oos_acc:.1f}%)")
    print(f"  No hallucination        : {passed_no_halluc}/{total}  ({halluc_acc:.1f}%)")
    print(f"  Avg latency             : {avg_latency:.1f}s")
    print()
    print(f"  By difficulty:")
    for d, g in sorted(diff_groups.items()):
        pct = g["pass"] / g["total"] * 100
        bar = "█" * int(pct // 10) + "░" * (10 - int(pct // 10))
        print(f"    {d:8s}  {bar}  {g['pass']}/{g['total']}  ({pct:.0f}%)")
    print()
    print(f"  By category (end-to-end pass):")
    for c, g in sorted(cat_groups.items()):
        pct = g["pass"] / g["total"] * 100
        status = "✓" if pct == 100 else ("~" if pct >= 50 else "✗")
        print(f"    {status} {c:30s} {g['pass']}/{g['total']}  ({pct:.0f}%)")
    print(f"{'='*60}\n")

    summary = {
        "timestamp":          datetime.now().isoformat(),
        "policy":             "whistleblower",
        "total":              total,
        "routing_accuracy":   round(routing_acc, 1),
        "answer_accuracy":    round(answer_acc, 1),
        "in_scope_accuracy":  round(in_scope_acc, 1),
        "oos_rejection_acc":  round(oos_acc, 1),
        "halluc_accuracy":    round(halluc_acc, 1),
        "avg_latency_s":      round(avg_latency, 1),
        "by_difficulty":      {d: {"pass": g["pass"], "total": g["total"],
                                   "pct": round(g["pass"]/g["total"]*100, 1)}
                               for d, g in diff_groups.items()},
        "by_category":        {c: {"pass": g["pass"], "total": g["total"],
                                   "pct": round(g["pass"]/g["total"]*100, 1)}
                               for c, g in cat_groups.items()},
        "test_results":       results,
    }
    return summary


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARVIN policy eval")
    parser.add_argument("--policy",  default="whistleblower", help="Policy to evaluate")
    parser.add_argument("--verbose", action="store_true",     help="Show answer snippets for all tests")
    parser.add_argument("--output",  default="",              help="Save JSON results to file")
    args = parser.parse_args()

    testset_map = {
        "whistleblower": os.path.join(os.path.dirname(__file__), "whistleblower_testset.json"),
        "posh":          os.path.join(os.path.dirname(__file__), "posh_testset.json"),
    }

    if args.policy not in testset_map:
        print(f"Unknown policy: {args.policy}. Available: {list(testset_map.keys())}")
        sys.exit(1)

    summary = run_eval(testset_map[args.policy], verbose=args.verbose)

    if args.output:
        out_path = args.output
        os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {out_path}")
