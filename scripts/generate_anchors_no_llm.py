"""
Generate synthetic anchor questions using template extraction — no LLM needed.

Pulls from eval/large_scale_eval.py:
  - 20-25 handcrafted seeds per policy
  - 3-5 Hindi-English variants per policy
  - Paraphrase expansion (3-4x each seed)
  - Template questions from chunk text

Output: data/synthetic_anchors/{collection}.json  (same format as LLM generator)
Target: 50-100 questions per policy.

Usage:
    python scripts/generate_anchors_no_llm.py        # all 18 policies
    python scripts/generate_anchors_no_llm.py --policy wb
    python scripts/generate_anchors_no_llm.py --force
"""
import os, sys, json, argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(REPO, 'data', 'synthetic_anchors')
VS_DIR     = os.path.join(REPO, 'vectorstore')
TARGET     = 60   # questions per policy (achievable with templates)

from eval.offline_accuracy import POLICY_MAP
from eval.large_scale_eval import (
    _seeds, _hindi_variants, _paraphrase,
    _generic_policy_questions, _sentences,
    _extract_amounts, _extract_days, _extract_months, _extract_roles,
)


def _load_chunks(collection: str) -> list[dict]:
    path = os.path.join(VS_DIR, f'{collection}_chunks.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _chunk_templates(chunks: list[dict], label: str) -> list[str]:
    """Extract template-based questions from policy chunks."""
    import re
    questions: set[str] = set()

    for chunk in chunks[:10]:   # first 10 chunks is enough
        text     = re.sub(r'^\[.*?\]\n?', '', chunk['text']).strip()
        amounts  = _extract_amounts(text)
        days_l   = _extract_days(text)
        months_l = _extract_months(text)
        roles    = _extract_roles(text)

        for amt in amounts[:3]:
            questions.update([
                f"What is the maximum amount of {amt} under this policy?",
                f"How much can I claim — is it {amt}?",
                f"Under what circumstances is {amt} applicable?",
            ])
        for d in days_l[:3]:
            questions.update([
                f"What must be done within {d}?",
                f"Is {d} the deadline for submission under this policy?",
            ])
        for m in months_l[:2]:
            questions.update([
                f"What happens after {m} under this policy?",
            ])
        for role in roles[:3]:
            questions.update([
                f"What is the role of the {role} under this policy?",
                f"What are the responsibilities of the {role}?",
                f"Can the {role} escalate a matter under this policy?",
            ])

    return list(questions)


def generate_for_policy(short: str, collection: str, label: str) -> list[str]:
    questions: set[str] = set()

    # 1. Seeds
    seeds = _seeds(short, label)
    questions.update(seeds)

    # 2. Paraphrase variants
    for s in seeds:
        questions.update(_paraphrase(s))

    # 3. Hindi-English variants
    questions.update(_hindi_variants(short, label))

    # 4. Generic policy questions
    policy_short = label.lower().replace(" policy", "").replace(" guide", "").replace(" program", "")
    questions.update(_generic_policy_questions(policy_short, label))

    # 5. Template extraction from chunks
    try:
        chunks = _load_chunks(collection)
        questions.update(_chunk_templates(chunks, label))
    except FileNotFoundError:
        pass

    return sorted(questions)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--policy', help='Short name: wb, dt, posh …')
    parser.add_argument('--force',  action='store_true', help='Overwrite existing files')
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    targets = (
        {args.policy: POLICY_MAP[args.policy]}
        if args.policy
        else POLICY_MAP
    )

    total_ok = 0
    for short, (collection, label, _) in targets.items():
        out_path = os.path.join(OUTPUT_DIR, f'{collection}.json')

        if os.path.exists(out_path) and not args.force:
            data = json.load(open(out_path, encoding='utf-8'))
            print(f"  {short:<8} ✓ already exists — {data['count']} questions")
            total_ok += 1
            continue

        questions = generate_for_policy(short, collection, label)

        result = {
            "policy_name": label,
            "collection":  collection,
            "count":       len(questions),
            "source":      "template",
            "questions":   questions,
        }
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"  {short:<8} ✓ {len(questions)} questions → {collection}.json")
        total_ok += 1

    print(f"\n  Done — {total_ok}/{len(targets)} policies generated")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"\n  Next step: python scripts/build_router_index.py")


if __name__ == "__main__":
    main()
