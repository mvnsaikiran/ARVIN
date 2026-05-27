"""
Build a ChromaDB router index from synthetic anchor questions.

Run AFTER generate_synthetic_anchors.py:
    python scripts/build_router_index.py

Creates collection "arvin_router_index" in vectorstore/.
Each document is a synthetic question; metadata contains the policy label.
"""
import os, sys, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from chromadb.utils import embedding_functions

REPO          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR      = os.path.join(REPO, 'data', 'synthetic_anchors')
VS_DIR        = os.path.join(REPO, 'vectorstore')
COLLECTION    = "arvin_router_index"
BATCH_SIZE    = 100   # ChromaDB add batch size


def main():
    files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith('.json'))
    if not files:
        print("No synthetic anchor files found.")
        print("Run:  python scripts/generate_synthetic_anchors.py")
        return

    ef     = embedding_functions.ONNXMiniLM_L6_V2()
    client = chromadb.PersistentClient(path=VS_DIR)

    # Drop and rebuild for a clean index
    try:
        client.delete_collection(COLLECTION)
        print(f"  Deleted old '{COLLECTION}'")
    except Exception:
        pass

    col = client.create_collection(
        COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    print(f"  Created '{COLLECTION}'")

    grand_total = 0
    for fname in files:
        fpath = os.path.join(DATA_DIR, fname)
        with open(fpath, encoding='utf-8') as f:
            data = json.load(f)

        policy_name = data["policy_name"]
        collection  = data["collection"]
        questions   = data["questions"]

        # Batch-add to avoid memory spikes on large lists
        for i in range(0, len(questions), BATCH_SIZE):
            batch_qs   = questions[i:i + BATCH_SIZE]
            batch_ids  = [f"{collection}_{i + j}" for j in range(len(batch_qs))]
            batch_meta = [{"policy": policy_name}] * len(batch_qs)
            col.add(documents=batch_qs, ids=batch_ids, metadatas=batch_meta)

        print(f"  {policy_name:<50} {len(questions):>3} questions")
        grand_total += len(questions)

    print(f"\n  ─────────────────────────────────────────────────────")
    print(f"  Total questions indexed : {grand_total}")
    print(f"  Collection count        : {col.count()}")
    print(f"  Vectorstore path        : {VS_DIR}")
    print(f"\n  Router index ready. Restart ARVIN to activate.")


if __name__ == "__main__":
    main()
