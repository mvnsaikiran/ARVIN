"""
Ingest the Whistleblower Policy into its own ChromaDB collection.

Run once (or re-run to rebuild):
    python -m policies.whistleblower.ingest
"""

import os
import sys
import hashlib
import json

import chromadb
from chromadb.utils import embedding_functions

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.parser  import extract_pdf, clean_text
from core.chunker import chunk_text
from policies.whistleblower.config import (
    PDF_PATH, POLICY_NAME, COLLECTION, MAX_CHUNK
)

_HERE           = os.path.dirname(os.path.abspath(__file__))
VECTORSTORE_DIR = os.path.join(_HERE, '..', '..', 'vectorstore')
CHUNKS_CACHE    = os.path.join(VECTORSTORE_DIR, f'{COLLECTION}_chunks.json')


def build():
    print(f"Ingesting: {POLICY_NAME}", flush=True)
    print(f"Source:    {PDF_PATH}", flush=True)

    if not os.path.exists(PDF_PATH):
        print(f"ERROR: PDF not found at {PDF_PATH}")
        sys.exit(1)

    os.makedirs(VECTORSTORE_DIR, exist_ok=True)

    # 1. Extract table chunks from PDF
    table_chunks = extract_pdf(PDF_PATH, POLICY_NAME, os.path.basename(PDF_PATH))

    # 2. Extract + chunk prose manually (full document join → smart split)
    import pdfplumber
    prose_pages = []
    with pdfplumber.open(PDF_PATH) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            raw = page.extract_text() or ''
            cleaned = clean_text(raw)
            if cleaned:
                prose_pages.append((page_num, cleaned))

    full_prose = '\n'.join(text for _, text in prose_pages)

    # Build page offset map for attribution
    page_offsets = []
    offset = 0
    for pnum, text in prose_pages:
        page_offsets.append((offset, offset + len(text), pnum))
        offset += len(text) + 1

    def approx_page(chunk_text_: str) -> int:
        needle = chunk_text_[:80].strip()
        pos = full_prose.find(needle)
        if pos < 0:
            return prose_pages[0][0] if prose_pages else 1
        for start, end, pnum in page_offsets:
            if start <= pos < end:
                return pnum
        return prose_pages[-1][0] if prose_pages else 1

    seen = {hashlib.md5(c['text'].encode()).hexdigest() for c in table_chunks}
    prose_chunks = []
    for text in chunk_text(full_prose, MAX_CHUNK):
        h = hashlib.md5(text.encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        prose_chunks.append({
            'text':        text,
            'policy_name': POLICY_NAME,
            'filename':    os.path.basename(PDF_PATH),
            'page':        approx_page(text),
            'chunk_type':  'prose',
        })

    all_chunks = table_chunks + prose_chunks
    print(f"Chunks: {len(table_chunks)} table + {len(prose_chunks)} prose = {len(all_chunks)} total")

    # 3. Embed + store in ChromaDB
    print("Loading ONNX embeddings (local, first run downloads ~50MB)...", flush=True)
    ef = embedding_functions.ONNXMiniLM_L6_V2()

    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)

    # Drop + recreate for clean rebuild
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass

    collection = client.create_collection(
        COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    ids       = [f"{COLLECTION}_{i}" for i in range(len(all_chunks))]
    texts     = [c['text'] for c in all_chunks]
    metadatas = [{
        'policy_name': c['policy_name'],
        'filename':    c['filename'],
        'page':        c['page'],
        'chunk_type':  c['chunk_type'],
    } for c in all_chunks]

    batch = 50
    for start in range(0, len(all_chunks), batch):
        end = min(start + batch, len(all_chunks))
        collection.add(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  Stored {end}/{len(all_chunks)}", flush=True)

    # 4. Save chunks cache for BM25
    with open(CHUNKS_CACHE, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f"Chunks cache saved -> {CHUNKS_CACHE}")
    print(f"\nDone. {len(all_chunks)} chunks in collection '{COLLECTION}'.")


if __name__ == '__main__':
    build()
