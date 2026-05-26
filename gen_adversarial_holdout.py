"""
Method 2 — Adversarial paraphrase generation.

Uses Claude (Haiku for cost efficiency) with an adversarial prompt to generate
new questions from actual policy chunks — but forcing DIFFERENT vocabulary than
the source policy text. This surfaces vocabulary gaps that the tuned keywords
and super-chunks may not cover.

Output: adversarial_holdout.json  (list of {query, key_facts, policy, chunk_id})
"""

import os, json, re, time, sys
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

CHUNKS_FILE = "vectorstore/chunks.json"
OUTPUT_FILE = "adversarial_holdout.json"
MODEL       = "gemini-1.5-flash"   # cheap + fast; different vocabulary from Claude
# How many policy chunks to sample per policy (to keep cost low)
CHUNKS_PER_POLICY = 4
# Questions per chunk
QS_PER_CHUNK = 3

ADVERSARIAL_PROMPT = """\
You are an Arvind Limited employee unfamiliar with HR jargon. You have just joined the company.

Read this policy excerpt and write exactly {n} questions a confused new joiner might ask.

STRICT RULES:
1. Do NOT use the exact words from the policy text (e.g. if policy says "reimbursement", say "money back" or "get paid back")
2. Use everyday plain English (e.g. "ceiling" not "limit", "monthly money" not "CTC", "time off" not "leave")
3. Ask about edge cases or "what if" scenarios (e.g. "what if I take my spouse on the trip?")
4. At least one question must have an informal phrasing or mild typo (e.g. "reimbursmnt", "can i", "wats the")
5. Each question must be answerable from the policy excerpt — include the KEY FACT that the answer should contain

Respond ONLY with a JSON array. Each element: {{"q": "<question>", "fact": "<key fact the answer must contain>"}}

Policy excerpt:
{chunk_text}
"""


def load_chunks() -> list[dict]:
    with open(CHUNKS_FILE) as f:
        return json.load(f)


def sample_chunks(chunks: list[dict]) -> list[dict]:
    """Sample a few chunks per policy, skipping super-chunks that were hand-crafted."""
    by_policy: dict[str, list[dict]] = {}
    for c in chunks:
        pol = c.get("policy_name", "Unknown")
        # Skip super-chunks injected by inject_superchunks_*.py (they already match queries)
        if c.get("chunk_type") == "prose" and "superchunk" not in c.get("id", ""):
            by_policy.setdefault(pol, []).append(c)
        elif c.get("chunk_type") != "prose":
            by_policy.setdefault(pol, []).append(c)

    sampled = []
    import random
    random.seed(42)
    for pol, pol_chunks in sorted(by_policy.items()):
        # prefer chunks with substantial text
        rich = [c for c in pol_chunks if len(c.get("text", "")) > 200]
        pool = rich if len(rich) >= CHUNKS_PER_POLICY else pol_chunks
        chosen = random.sample(pool, min(CHUNKS_PER_POLICY, len(pool)))
        sampled.extend(chosen)

    print(f"Sampled {len(sampled)} chunks across {len(by_policy)} policies")
    return sampled


def generate_questions(model, chunk: dict) -> list[dict]:
    """Call Gemini to generate adversarial questions for one chunk."""
    prompt = ADVERSARIAL_PROMPT.format(n=QS_PER_CHUNK, chunk_text=chunk["text"][:1200])
    try:
        resp = model.generate_content(prompt)
        raw  = resp.text.strip()
        # Extract JSON array from response (may have preamble text)
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            print(f"    [WARN] no JSON array in response for chunk {chunk.get('id')}")
            return []
        items = json.loads(match.group())
        return [
            {
                "query":    item["q"],
                "key_facts": [item["fact"]],
                "policy":   chunk["policy_name"],
                "chunk_id": chunk.get("id", ""),
                "page":     chunk.get("page", 0),
            }
            for item in items
            if "q" in item and "fact" in item
        ]
    except Exception as e:
        print(f"    [ERROR] chunk {chunk.get('id')}: {e}")
        return []


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL)

    chunks  = load_chunks()
    sampled = sample_chunks(chunks)

    results = []
    t0 = time.time()

    for i, chunk in enumerate(sampled):
        pol = chunk["policy_name"]
        cid = chunk.get("id", "?")
        print(f"  [{i+1:3d}/{len(sampled)}] {pol[:45]:<45} chunk={cid}", end=" ... ", flush=True)
        qs = generate_questions(model, chunk)
        print(f"{len(qs)} questions")
        results.extend(qs)
        # small delay to avoid rate-limit bursts
        time.sleep(0.3)

    elapsed = time.time() - t0
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nGenerated {len(results)} adversarial questions in {elapsed:.0f}s")
    print(f"Saved → {OUTPUT_FILE}")

    # Quick policy breakdown
    from collections import Counter
    counts = Counter(r["policy"] for r in results)
    for pol, cnt in sorted(counts.items()):
        print(f"  {pol:<55} {cnt}")


if __name__ == "__main__":
    main()
