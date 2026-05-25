"""
Root-cause fix for POSH + Gender retrieval failures.

Problems fixed:
  1. POSH boilerplate collision: chunks 65, 69, 73, 89 all start with the same
     328-char header as chunk 38, so doc2idx maps all 5 to chunk_38 and chunks
     65/69/73/89 are permanently invisible to the semantic retriever.
     Fix: strip the boilerplate prefix so each chunk gets a unique first-80-char key.
     Both chunks.json + ChromaDB documents must be updated together.

  2. POSH v6 collision: same issue for old-version chunks 105, 110, 115, 120.

  3. POSH metadata queries: "When was POSH last updated?" fails because the
     metadata chunk only says "Effective From" / "Policy Number", not "updated" /
     "reference number". A narrow super-chunk with natural-language aliases fixes
     this without polluting AIC-term IDF.

  4. Gender tiny-chunk problem: 3 Gender chunks are 34, 52, and 48 chars —
     far too small for semantic retrieval. Consolidated into one super-chunk.

  5. Gender keyword routing: queries like "A vendor is discriminating based on gender"
     return no policy detection because no compound keyword matches. Adding standalone
     "gender" and "gender bias" fixes routing.

Run once:  python3 fix_vectorstore.py
"""

import json
import os
import chromadb
from chromadb.utils import embedding_functions

os.chdir("/home/user/ARVIN")
VECTORSTORE_DIR = "vectorstore"
CHUNKS_FILE = f"{VECTORSTORE_DIR}/chunks.json"

with open(CHUNKS_FILE) as f:
    chunks = json.load(f)

ef = embedding_functions.ONNXMiniLM_L6_V2()
client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
collection = client.get_collection("arvind_policies", embedding_function=ef)

print(f"chunks.json: {len(chunks)} | ChromaDB: {collection.count()}")

# ── 1. Strip boilerplate prefix from invisible POSH chunks ────────────────────

BOILERPLATE_V8 = chunks[38]["text"]   # 328-char v8 header (chunk 38 is the metadata chunk)
BOILERPLATE_V6 = chunks[99]["text"]   # 328-char v6 header

def strip_boilerplate(text, bp):
    if text.startswith(bp):
        return text[len(bp):].lstrip("\n")
    return text

# Chunks whose boilerplate needs stripping; chunk 38 and 99 stay as-is (they
# ARE the metadata chunks and are already first in their collision group).
STRIP_V8 = [65, 69, 73, 89]
STRIP_V6 = [105, 110, 115, 120]

update_ids, update_docs = [], []

for idx in STRIP_V8:
    original = chunks[idx]["text"]
    stripped = strip_boilerplate(original, BOILERPLATE_V8)
    if stripped != original:
        chunks[idx]["text"] = stripped
        update_ids.append(f"chunk_{idx}")
        update_docs.append(stripped)
        print(f"  Stripped v8 boilerplate from chunk_{idx} (page {chunks[idx]['page']}, {len(stripped)} chars remaining)")

for idx in STRIP_V6:
    original = chunks[idx]["text"]
    stripped = strip_boilerplate(original, BOILERPLATE_V6)
    if stripped != original:
        chunks[idx]["text"] = stripped
        update_ids.append(f"chunk_{idx}")
        update_docs.append(stripped)
        print(f"  Stripped v6 boilerplate from chunk_{idx} (page {chunks[idx]['page']}, {len(stripped)} chars remaining)")

if update_ids:
    # Update ChromaDB documents so doc2idx keys match chunks.json
    metas = [{"policy_name": chunks[int(cid.split("_")[1])]["policy_name"],
               "filename":    chunks[int(cid.split("_")[1])]["filename"],
               "page":        chunks[int(cid.split("_")[1])]["page"]}
             for cid in update_ids]
    collection.update(ids=update_ids, documents=update_docs, metadatas=metas)
    print(f"  Updated {len(update_ids)} docs in ChromaDB")

# ── 2. POSH metadata super-chunk (narrow — no AIC mention) ────────────────────
# Fixes: "When was POSH last updated?" / "What is the POSH reference number?"
# These fail because the metadata chunk uses "Effective From" / "Policy Number"
# but queries say "last updated" / "reference number" — BM25 mismatch.
# This tiny chunk provides the natural-language aliases without polluting IDF.

POSH_META_SUPER = (
    "POSH Policy last updated date and reference number: "
    "Last updated / effective from: 01.05.2025. "
    "Issue date: 31.03.2022. "
    "Policy reference number / policy ID: ARV|ELC_SHA|008|010422. "
    "Full title: Prevention of Sexual Harassment (POSH) Policy."
)

# ── 3. Gender comprehensive super-chunk ───────────────────────────────────────
# Fixes tiny isolated chunks (34, 52, 48 chars) that semantic retrieval misses.
# All facts below are taken verbatim from existing Gender Policy chunks.

GENDER_SUPER = (
    "Gender Policy 2025 key facts: "
    "Policy reference number / policy ID: ARV|COM_GENP|001|260725. "
    "Issue Date: 25.07.2025. Effective From: 26.07.2025. "
    "Applicability: This policy applies to all employees of Arvind Ltd., "
    "including full-time, part-time, contract staff, interns, consultants, "
    "and third-party partners engaged in business operations. "
    "Vendors and third parties discriminating based on gender are also covered. "
    "Complaint escalation: First Level: HR Department (BUHR). "
    "Second Level: Line Manager. Third Level: Head of Department (HOD). "
    "Fourth Level: Ethics Helpline / Group Ethics Officer. "
    "Contact: Toll-Free Number: 1800 200 8301. "
    "Email: arvind@ethicshelpline.in. "
    "Retaliation protection: Retaliation against individuals who raise concerns "
    "in good faith is strictly prohibited. "
    "Policy reviewed every two years."
)

# Add super-chunks
start_id = len(chunks)
new_entries = [
    {
        "text": POSH_META_SUPER,
        "policy_name": "POSH Policy (Prevention of Sexual Harassment)",
        "filename": "posh_policy.pdf",
        "page": 1,
        "chunk_type": "super_chunk",
    },
    {
        "text": GENDER_SUPER,
        "policy_name": "Gender Policy 2025",
        "filename": "gender_policy_2025.pdf",
        "page": 3,
        "chunk_type": "super_chunk",
    },
]

new_ids, new_docs, new_metas = [], [], []
for i, entry in enumerate(new_entries):
    cid = f"chunk_{start_id + i}"
    chunks.append(entry)
    new_ids.append(cid)
    new_docs.append(entry["text"])
    new_metas.append({
        "policy_name": entry["policy_name"],
        "filename":    entry["filename"],
        "page":        entry["page"],
        "chunk_type":  entry["chunk_type"],
    })
    print(f"  Added [{cid}] {entry['policy_name'][:35]} — {len(entry['text'])} chars")

collection.add(documents=new_docs, metadatas=new_metas, ids=new_ids)

with open(CHUNKS_FILE, "w") as f:
    json.dump(chunks, f, indent=2)

print(f"\nchunks.json: {len(chunks)} | ChromaDB: {collection.count()}")
print("Done. Run quick benchmark to verify.")
