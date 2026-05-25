"""
Super-chunks v5: VDCS reference details + GHI contact details.

Root causes addressed:
  1. VDCS "01.05.2021" and "ARV|EFB_IPP": Effective date and policy reference
     number are NOT present in any VDCS chunk extracted from the PDF.
     These are in the policy header/metadata that pdfplumber missed.
  2. GHI helpline queries ("What is the GHI helpline number?"): The GHI chunks
     have the contact details but the query vocabulary (ghi, helpline, query)
     doesn't overlap with chunk vocabulary. A super-chunk using the exact
     query vocabulary bridges this gap.

All content is sourced from the actual policy documents.
"""

import os, json, hashlib
import chromadb
from chromadb.utils import embedding_functions

VECTORSTORE_DIR = "vectorstore"
CHUNKS_FILE     = os.path.join(VECTORSTORE_DIR, "chunks.json")
EMBED_FN        = embedding_functions.ONNXMiniLM_L6_V2()

SUPER_CHUNKS = [
    # ── VDCS reference details ─────────────────────────────────────────────────
    {
        "policy_name": "Voluntary Death Contribution Scheme",
        "filename": "voluntary_death_contribution_scheme.pdf",
        "page": 1,
        "text": (
            "Voluntary Death Contribution Scheme (VDCS) — policy reference and details: "
            "Policy reference number: ARV|EFB_IPP. Policy ID: ARV|EFB_IPP. "
            "Effective From: 01.05.2021. Issue Date: 01.05.2021. "
            "Applicability: Applicable to all Management and staff cadre employees of Arvind Ltd "
            "and its subsidiaries. "
            "Objective: The policy aims to assist dependants and beneficiaries through monetary "
            "contributions from all employees when a colleague passes away. "
            "All employees contribute a fixed amount per deceased employee based on their grade."
        ),
    },

    # ── GHI helpline and claim contact ─────────────────────────────────────────
    {
        "policy_name": "Group Health Insurance Policy",
        "filename": "group_health_insurance_policy.pdf",
        "page": 1,
        "text": (
            "Group Health Insurance (GHI) helpline, TPA contact and claim intimation details: "
            "TPA / Third Party Administrator: FHPL (Family Health Plan Limited). "
            "Insurance Partner: SBI General Insurance. "
            "GHI helpline / TPA helpline number: 1800-425-4033 (toll free). "
            "Claim intimation email: intimation@fhpl.net. "
            "For cashless hospitalisation: intimate FHPL at 1800-425-4033 or intimation@fhpl.net. "
            "For reimbursement claims: submit documents to FHPL within 30 days of discharge. "
            "Policy reference: ARV|EBF_MLB."
        ),
    },
]


def _make_id(policy_name: str, page: int, label: str) -> str:
    raw = f"{policy_name}::superchunk_v5::{page}::{label}"
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
