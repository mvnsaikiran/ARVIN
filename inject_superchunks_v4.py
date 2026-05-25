"""
Super-chunks v4: Joining Policy 700km rates + Talent Mobility MAB grade table.

Root causes addressed:
  1. Joining Policy 700km/tax failures: the real chunk (158) has zero BM25 score
     because queries say "relocation journey / 700km" but the chunk says
     "transportation of personal packers / 700 kms" — pure vocabulary gap.
     This super-chunk bridges that gap.
  2. TM MAB failures: the real chunk (151) has the data but "MAB" abbreviation
     is not in its tokens (it says "Mobility Adjustment Benefit"). Adding a
     super-chunk with "MAB" makes BM25 score it correctly.

All text is sourced from the actual policy documents.
"""

import os, json, hashlib
import chromadb
from chromadb.utils import embedding_functions

VECTORSTORE_DIR = "vectorstore"
CHUNKS_FILE     = os.path.join(VECTORSTORE_DIR, "chunks.json")
EMBED_FN        = embedding_functions.ONNXMiniLM_L6_V2()

SUPER_CHUNKS = [
    # ── Joining Policy — transport reimbursement rate by distance ──────────────
    {
        "policy_name": "Joining Policy",
        "filename": "joining_policy.pdf",
        "page": 1,
        "text": (
            "Joining Policy — relocation transport reimbursement rate by distance: "
            "If the distance between employee's current location and location of posting "
            "is less than 700 km (under 700km, within 700km, less than 700 kms): "
            "maximum limit is Rs. 50 per km OR actuals whichever is lesser. "
            "If the distance is more than 700 km (over 700km, above 700km, exceeds 700kms): "
            "maximum limit is Rs. 60 per km OR actuals whichever is lesser. "
            "Income tax shall be grossed up for the employee based on his tax bracket. "
            "The company shall directly make payment to the transporter / service provider. "
            "Food allowance during relocation journey: maximum Rs. 200 per meal. "
            "Car transportation via packers & movers: Rs. 10.0 per km total distance reimbursed."
        ),
    },

    # ── Talent Mobility — MAB (Mobility Adjustment Benefit) by grade ──────────
    {
        "policy_name": "Talent Mobility Policy",
        "filename": "talent_mobility_policy.pdf",
        "page": 7,
        "text": (
            "Talent Mobility Policy — MAB (Mobility Adjustment Benefit) and "
            "SIA (Settling-In Assistance) amounts by grade: "
            "MAB is a monthly allowance paid for 12 months, merged into CTC on job rotation completion. "
            "SIA is a one-time lump sum for household setup applicable only when relocating more than 20 kms. "
            "Grade E1: Annual MAB = 3,91,000 | Monthly MAB = 32,583 | SIA = 10,000. "
            "Grade E2: Annual MAB = 5,49,000 | Monthly MAB = 45,750 | SIA = 10,000. "
            "Grade M1: Annual MAB = 8,52,000 | Monthly MAB = 71,000 | SIA = 15,000. "
            "Grade M2: Annual MAB = 13,00,000 | Monthly MAB = 1,08,333 | SIA = 20,000. "
            "Grade M3: Annual MAB = 19,00,000 | Monthly MAB = 1,58,333 | SIA = 30,000. "
            "Grade M3H1: Annual MAB = 26,00,000 | Monthly MAB = 2,16,667 | SIA = 45,000. "
            "Mobility costs less than attrition and delivers more than retention."
        ),
    },
]


def _make_id(policy_name: str, page: int, label: str) -> str:
    raw = f"{policy_name}::superchunk_v4::{page}::{label}"
    return "chunk_" + hashlib.md5(raw.encode()).hexdigest()[:12]


def main():
    print("Loading chunks.json …")
    with open(CHUNKS_FILE) as f:
        chunks = json.load(f)
    print(f"  Existing chunks: {len(chunks)}")

    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    col    = client.get_collection("arvind_policies", embedding_function=EMBED_FN)
    print(f"  ChromaDB docs: {col.count()}")

    existing_ids = set(col.get(include=[])["ids"])

    new_docs, new_meta, new_ids, new_chunks_json = [], [], [], []

    for i, sc in enumerate(SUPER_CHUNKS):
        cid = _make_id(sc["policy_name"], sc["page"], str(i))
        # Use sequential chunk index for the stored id
        idx = len(chunks) + len(new_chunks_json)
        chunk_id = f"chunk_{idx}"
        if cid in existing_ids or chunk_id in existing_ids:
            print(f"  Skipped (already exists): {chunk_id}")
            continue
        new_docs.append(sc["text"])
        new_meta.append({"policy_name": sc["policy_name"], "page": sc["page"], "chunk_id": chunk_id})
        new_ids.append(chunk_id)
        new_chunks_json.append({
            "id":          chunk_id,
            "policy_name": sc["policy_name"],
            "page":        sc["page"],
            "text":        sc["text"],
            "filename":    sc["filename"],
            "chunk_type":  "prose",
        })
        print(f"  Queued [{chunk_id}] {sc['policy_name']} — {len(sc['text'])} chars")

    if not new_docs:
        print("Nothing to add.")
        return

    print(f"\nAdding {len(new_docs)} super-chunks to ChromaDB …")
    col.add(documents=new_docs, metadatas=new_meta, ids=new_ids)
    print(f"  ChromaDB docs after: {col.count()}")

    chunks.extend(new_chunks_json)
    with open(CHUNKS_FILE, "w") as f:
        json.dump(chunks, f, indent=2)
    print(f"  chunks.json updated: {len(chunks)} total chunks")
    print("\nDone.")


if __name__ == "__main__":
    main()
