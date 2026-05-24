"""
ChromaDB Retrieval Accuracy Benchmark — no Gemini key needed.
Tests: does ChromaDB return chunks containing the right policy + key facts?
"""

import json, re, sys, time
import chromadb
from chromadb.utils import embedding_functions

VECTORSTORE_DIR = "vectorstore"
TOP_K = 6
SAMPLE = None  # None = run all test cases

# ── Load test suite from TypeScript file ─────────────────────────────────────

def load_test_suite(path="src/data/fullTestSuite.ts", limit=None):
    with open(path, encoding="utf-8") as f:
        content = f.read()

    cases = []
    # Extract each test object block
    blocks = re.findall(r'\{[^{}]*"id":\s*"TC\d+"[^{}]*\}', content, re.DOTALL)
    for block in blocks:
        try:
            def get(field):
                m = re.search(rf'"{field}":\s*`([^`]*)`', block)
                if m: return m.group(1).strip()
                m = re.search(rf'"{field}":\s*"([^"]*)"', block)
                if m: return m.group(1).strip()
                return ""

            def get_list(field):
                m = re.search(rf'"{field}":\s*\[([^\]]*)\]', block, re.DOTALL)
                if not m: return []
                items = re.findall(r'"([^"]+)"', m.group(1))
                return items

            tc = {
                "id": get("id"),
                "query": get("query"),
                "exactAnswer": get("exactAnswer"),
                "keyFacts": get_list("keyFacts"),
                "source": get("source"),
                "page": get("page"),
                "category": get("category"),
            }
            if tc["id"] and tc["query"]:
                cases.append(tc)
        except Exception:
            continue
        if limit and len(cases) >= limit:
            break
    return cases

# ── ChromaDB setup ────────────────────────────────────────────────────────────

print("Loading ChromaDB + ONNX embeddings...", flush=True)
ef = embedding_functions.ONNXMiniLM_L6_V2()
client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
collection = client.get_collection("arvind_policies", embedding_function=ef)
print(f"Collection loaded: {collection.count()} chunks\n", flush=True)

# ── Benchmark ─────────────────────────────────────────────────────────────────

print("Loading test suite...", flush=True)
tests = load_test_suite(limit=SAMPLE)
print(f"Loaded {len(tests)} test cases\n", flush=True)

source_hits = 0
fact_hits = 0
both_hits = 0
total = 0
category_stats = {}

start = time.time()

for i, tc in enumerate(tests):
    query = tc["query"]
    expected_source = tc["source"].lower().strip()
    key_facts = [f.lower() for f in tc["keyFacts"]]
    category = tc["category"] or "Unknown"

    # ChromaDB retrieval
    results = collection.query(
        query_texts=[query],
        n_results=TOP_K,
        include=["documents", "metadatas"],
    )
    docs = results["documents"][0]
    metas = results["metadatas"][0]

    # Check source match
    retrieved_sources = [m.get("policy_name", "").lower() for m in metas]
    source_hit = any(expected_source in s or s in expected_source for s in retrieved_sources)

    # Check key facts in retrieved context
    combined_text = " ".join(docs).lower()
    fact_hit = all(f in combined_text for f in key_facts) if key_facts else True

    source_hits += int(source_hit)
    fact_hits += int(fact_hit)
    both_hits += int(source_hit and fact_hit)
    total += 1

    # Category tracking
    if category not in category_stats:
        category_stats[category] = {"total": 0, "both": 0}
    category_stats[category]["total"] += 1
    category_stats[category]["both"] += int(source_hit and fact_hit)

    if (i + 1) % 500 == 0:
        elapsed = time.time() - start
        print(f"  {i+1}/{len(tests)} | Source: {source_hits/(i+1)*100:.1f}% | Facts: {fact_hits/(i+1)*100:.1f}% | Both: {both_hits/(i+1)*100:.1f}% | {elapsed:.0f}s", flush=True)

elapsed = time.time() - start

# ── Results ───────────────────────────────────────────────────────────────────

print(f"\n{'='*55}")
print(f"  CHROMADB RETRIEVAL BENCHMARK — {total} test cases")
print(f"{'='*55}")
print(f"  Source accuracy  (correct policy retrieved): {source_hits/total*100:.1f}%")
print(f"  Fact accuracy    (key facts in context):     {fact_hits/total*100:.1f}%")
print(f"  Overall accuracy (source + facts both hit):  {both_hits/total*100:.1f}%")
print(f"  Time: {elapsed:.1f}s ({elapsed/total*1000:.0f}ms per query)\n")

print("  By category:")
for cat, stats in sorted(category_stats.items(), key=lambda x: -x[1]["both"]/max(x[1]["total"],1)):
    pct = stats["both"] / stats["total"] * 100
    print(f"    {cat:<35} {pct:5.1f}%  ({stats['both']}/{stats['total']})")

print(f"{'='*55}")
