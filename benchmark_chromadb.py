"""
ChromaDB Retrieval Benchmark — normalised evaluator.
Fixes benchmark bugs identified in deep analysis:
  1. Hyphenation: "two-wheeler" == "two wheeler"
  2. Parenthetical numbers: "3 months" matches "3 (three) months"
  3. Currency format: "50 per hour" matches "Rs. 50/- per hour"
  4. "Multiple Policies" source: skip source check, count fact hit only
  5. Slash vs "or":  "3rd ac/chair car" == "3rd ac or chair car"
"""

import json, re, time, chromadb
from chromadb.utils import embedding_functions

TOP_K  = 6
MULTI_POLICY_SOURCES = {"multiple policies", "multiple"}

# ── Text normalisation ────────────────────────────────────────────────────────

def normalise(text: str) -> str:
    t = text.lower()
    # Currency: "Rs. 50/-" → "50", "₹6,000" → "6000"
    t = re.sub(r'rs\.?\s*', '', t)
    t = re.sub(r'₹\s*', '', t)
    t = re.sub(r'/-', '', t)
    t = re.sub(r',', '', t)          # "6,000" → "6000"
    # Parenthetical words after numbers: "3 (three) months" → "3  months"
    t = re.sub(r'\([\w\s]+\)', ' ', t)
    # Hyphens → space: "two-wheeler" → "two wheeler"
    t = t.replace('-', ' ')
    # Slash → " or ": "3rd ac/chair car" → "3rd ac or chair car"
    t = t.replace('/', ' or ')
    # Collapse whitespace
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def fact_present(fact: str, combined_normalised: str) -> bool:
    return normalise(fact) in combined_normalised


# ── ChromaDB setup ────────────────────────────────────────────────────────────

print("Loading ChromaDB + ONNX embeddings...", flush=True)
ef     = embedding_functions.ONNXMiniLM_L6_V2()
client = chromadb.PersistentClient(path="vectorstore")
col    = client.get_collection("arvind_policies", embedding_function=ef)
print(f"Collection: {col.count()} chunks\n", flush=True)

with open("test_suite.json") as f:
    tests = json.load(f)
print(f"Running normalised benchmark on {len(tests)} test cases...\n", flush=True)

# ── Benchmark loop ────────────────────────────────────────────────────────────

source_hits = fact_hits = both_hits = total = 0
cat_stats   = {}          # category → [total, both_hit]
fail_examples = []        # first 3 failures per category for diagnosis

start = time.time()

for i, tc in enumerate(tests):
    query       = tc["query"]
    expected    = tc["source"].lower().strip()
    key_facts   = tc.get("keyFacts", [])
    category    = tc.get("category", "Unknown")
    multi_src   = expected in MULTI_POLICY_SOURCES

    results = col.query(
        query_texts=[query], n_results=TOP_K,
        include=["documents", "metadatas"]
    )
    docs  = results["documents"][0]
    metas = results["metadatas"][0]

    retrieved_sources = [m.get("policy_name", "").lower() for m in metas]
    combined_norm     = normalise(" ".join(docs))

    # Source hit
    if multi_src:
        source_hit = True          # skip source check for multi-policy Qs
    else:
        source_hit = any(
            expected in s or s in expected
            for s in retrieved_sources
        )

    # Fact hit (normalised)
    fact_hit = all(fact_present(f, combined_norm) for f in key_facts) if key_facts else True

    source_hits += source_hit
    fact_hits   += fact_hit
    both        = source_hit and fact_hit
    both_hits   += both
    total       += 1

    if category not in cat_stats:
        cat_stats[category] = [0, 0, []]
    cat_stats[category][0] += 1
    cat_stats[category][1] += both
    if not both and len(cat_stats[category][2]) < 2:
        cat_stats[category][2].append({
            "q": query,
            "facts": key_facts,
            "src_hit": source_hit,
            "fact_hit": fact_hit,
            "retrieved": combined_norm[:300],
        })

    if (i + 1) % 1000 == 0:
        print(f"  {i+1}/{len(tests)} | Source {source_hits/(i+1)*100:.1f}% | "
              f"Facts {fact_hits/(i+1)*100:.1f}% | Overall {both_hits/(i+1)*100:.1f}%",
              flush=True)

elapsed = time.time() - start

# ── Results ───────────────────────────────────────────────────────────────────

print(f"\n{'='*60}")
print(f"  NORMALISED BENCHMARK — {total} test cases")
print(f"{'='*60}")
print(f"  Source accuracy:   {source_hits/total*100:.1f}%  (raw was 98.0%)")
print(f"  Fact accuracy:     {fact_hits/total*100:.1f}%  (raw was 75.1%)")
print(f"  Overall accuracy:  {both_hits/total*100:.1f}%  (raw was 73.9%)")
print(f"  Speed: {elapsed/total*1000:.1f}ms/query | {elapsed:.0f}s total\n")

perfect   = [(c, s) for c, s in cat_stats.items() if s[1]==s[0]]
imperfect = [(c, s) for c, s in cat_stats.items() if s[1]<s[0]]

print(f"  ✅ Perfect categories ({len(perfect)}):")
for cat, (t, h, _) in sorted(perfect, key=lambda x: -x[1][0]):
    print(f"    {cat:<40} 100.0%  ({h}/{t})")

print(f"\n  ⚠️  Imperfect categories ({len(imperfect)}) — sorted by score:")
for cat, (t, h, examples) in sorted(imperfect, key=lambda x: x[1][1]/x[1][0]):
    pct = h/t*100
    print(f"\n    {cat:<40} {pct:5.1f}%  ({h}/{t})")
    for ex in examples:
        missing = [f for f in ex['facts'] if not fact_present(f, ex['retrieved'])]
        print(f"      Q: {ex['q'][:80]}")
        print(f"      Missing facts: {missing}")
        print(f"      Src hit: {ex['src_hit']}  |  context: {ex['retrieved'][:120]}...")

print(f"\n{'='*60}")
