"""
Generate 50 varied synthetic questions per policy using the Groq LLM.
Output: data/synthetic_anchors/{collection}.json

Usage:
    python scripts/generate_synthetic_anchors.py           # all 18 policies
    python scripts/generate_synthetic_anchors.py --policy dt   # single policy
    python scripts/generate_synthetic_anchors.py --force       # overwrite existing
"""
import os, sys, json, re, time, argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR  = os.path.join(REPO, 'data', 'synthetic_anchors')
VS_DIR      = os.path.join(REPO, 'vectorstore')

QUESTIONS_PER_POLICY = 50
MAX_CHUNKS           = 15     # sample up to 15 chunks to stay in token budget

GEN_SYSTEM = (
    "You are an HR documentation expert. "
    "Your ONLY task is to output a valid JSON array of question strings."
)

# Map: short → (collection, policy_name)
from eval.offline_accuracy import POLICY_MAP


def _load_chunks(collection: str) -> list[dict]:
    path = os.path.join(VS_DIR, f'{collection}_chunks.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _sample_chunks(chunks: list[dict], n: int) -> list[dict]:
    """Even-stride sample so all sections of the document are represented."""
    if len(chunks) <= n:
        return chunks
    step = len(chunks) / n
    return [chunks[int(i * step)] for i in range(n)]


def _generate(policy_name: str, chunks: list[dict]) -> list[str]:
    sample      = _sample_chunks(chunks, MAX_CHUNKS)
    policy_text = "\n\n---\n\n".join(
        f"[Page {c.get('page', '?')}]\n{c['text']}" for c in sample
    )

    prompt = f"""You are an HR expert at Arvind Limited. Below are excerpts from the "{policy_name}".

Generate EXACTLY {QUESTIONS_PER_POLICY} questions that Arvind employees might realistically ask.

Include a balanced mix (10 of each type):
1. HOW-TO: "How do I...", "What are the steps to...", "How should I..."
2. ELIGIBILITY: "Am I eligible for...", "Who can apply for...", "Who qualifies for..."
3. SCENARIO: "What happens if...", "What if I don't...", "In case of..."
4. FACTUAL: short questions asking about specific amounts, days, limits, contacts, rates
5. CASUAL/VAGUE: short informal questions like employees actually type — include 2-3 Hinglish
   phrases (e.g. "paise kab milenge?", "form kaise bharna hai?", "mujhe kya milega?")

Rules:
- Every question must be answerable from the policy excerpts below
- No two questions should be near-identical — vary phrasing significantly
- Cover ALL major topics/sections visible in the excerpts
- Keep questions realistic — avoid corporate jargon employees wouldn't use

Policy excerpts:
{policy_text}

IMPORTANT: Return ONLY a valid JSON array of exactly {QUESTIONS_PER_POLICY} strings.
No markdown fences, no explanations, no numbering outside the JSON:
["question 1", "question 2", ..., "question {QUESTIONS_PER_POLICY}"]"""

    from core.llm import ask as llm_ask
    raw = llm_ask(GEN_SYSTEM, prompt)

    # Strip markdown code blocks if model adds them
    raw = re.sub(r'```(?:json)?\s*', '', raw).strip()

    # Extract the JSON array
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array in response:\n{raw[:300]}")

    questions = json.loads(match.group(0))
    if not isinstance(questions, list):
        raise ValueError(f"Expected list, got {type(questions)}")

    return [str(q).strip() for q in questions if str(q).strip()]


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
    for short, (collection, policy_name, _) in targets.items():
        out_path = os.path.join(OUTPUT_DIR, f'{collection}.json')

        if os.path.exists(out_path) and not args.force:
            data = json.load(open(out_path, encoding='utf-8'))
            print(f"  {short:<8} ✓ already exists — {len(data['questions'])} questions")
            total_ok += 1
            continue

        print(f"  {short:<8} loading chunks …", end='', flush=True)
        try:
            chunks = _load_chunks(collection)
        except FileNotFoundError:
            print(f" ✗ chunks not found for {collection}")
            continue

        print(f" {len(chunks)} chunks → generating {QUESTIONS_PER_POLICY} Qs …", end='', flush=True)

        try:
            questions = _generate(policy_name, chunks)
            result = {
                "policy_name": policy_name,
                "collection":  collection,
                "count":       len(questions),
                "questions":   questions,
            }
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f" ✓ {len(questions)} questions saved")
            total_ok += 1
        except Exception as e:
            print(f" ✗ {e}")

        time.sleep(3)   # stay within Groq free-tier rate limits

    print(f"\n  Done — {total_ok}/{len(targets)} policies generated")
    print(f"  Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
