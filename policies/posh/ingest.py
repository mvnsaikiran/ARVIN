"""
Ingest the POSH Policy into its own ChromaDB collection.

Run once (or re-run to rebuild):
    python -m policies.posh.ingest
"""

import os
import sys
import hashlib
import json

import fitz
import chromadb
from chromadb.utils import embedding_functions

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.parser  import clean_text
from core.chunker import chunk_text
from policies.posh.config import (
    PDF_PATH, POLICY_NAME, COLLECTION, MAX_CHUNK, SKIP_PAGES, DOC_TYPE
)

_HERE           = os.path.dirname(os.path.abspath(__file__))
VECTORSTORE_DIR = os.path.join(_HERE, '..', '..', 'vectorstore')
CHUNKS_CACHE    = os.path.join(VECTORSTORE_DIR, f'{COLLECTION}_chunks.json')

# Boilerplate that repeats on every POSH page — strip it
import re
_POSH_BOILERPLATE = re.compile(
    r'Private\s*&\s*Confidential\s*Only for Internal Circulation'
    r'|HR Policy\s+Classification:\s+Internal'
    r'|Issue Date:.*?Policy Number:.*?(?=\n|$)'
    r'|Policy incorporates the legislation titled.*?2013\.'
    r'|ARV\|ELC_SHA\|[\w|]+'
    r'|Effective From:.*?(?=\n|$)',
    re.IGNORECASE | re.DOTALL
)


def clean_posh(raw: str) -> str:
    text = _POSH_BOILERPLATE.sub('', raw)
    text = clean_text(text)
    # Remove bare page numbers like "Page 1" left over
    text = re.sub(r'(?m)^\s*Page\s+\d+\s*$', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def build():
    print(f"Ingesting: {POLICY_NAME}", flush=True)
    print(f"Source:    {PDF_PATH}", flush=True)

    if not os.path.exists(PDF_PATH):
        print(f"ERROR: PDF not found at {PDF_PATH}")
        sys.exit(1)

    os.makedirs(VECTORSTORE_DIR, exist_ok=True)

    prose_pages = []
    doc = fitz.open(PDF_PATH)
    print(f"Total pages: {len(doc)}", flush=True)

    for page_num, page in enumerate(doc, start=1):
        if page_num in SKIP_PAGES:
            print(f"  Skipping page {page_num} (AIC member directory)", flush=True)
            continue
        raw     = page.get_text()
        cleaned = clean_posh(raw)
        if cleaned and len(cleaned) > 80:
            prose_pages.append((page_num, cleaned))
            print(f"  Page {page_num}: {len(cleaned)} chars", flush=True)
        else:
            print(f"  Page {page_num}: skipped (empty after cleaning)", flush=True)
    doc.close()

    if not prose_pages:
        print("ERROR: No content extracted.")
        sys.exit(1)

    # Build word-set per page for page attribution
    page_word_sets = [(pnum, set(text.lower().split())) for pnum, text in prose_pages]

    full_prose = '\n'.join(text for _, text in prose_pages)

    def approx_page(chunk_text_: str) -> int:
        chunk_words = set(chunk_text_.lower().split())
        best_page, best_overlap = prose_pages[0][0], -1
        for pnum, words in page_word_sets:
            overlap = len(chunk_words & words)
            if overlap > best_overlap:
                best_overlap, best_page = overlap, pnum
        return best_page

    seen = set()
    all_chunks = []
    for text in chunk_text(full_prose, MAX_CHUNK):
        h = hashlib.md5(text.encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        from core.base_ingest import _add_header
        all_chunks.append({
            'text':        _add_header(text, POLICY_NAME, DOC_TYPE),
            'policy_name': POLICY_NAME,
            'filename':    os.path.basename(PDF_PATH),
            'page':        approx_page(text),
            'chunk_type':  'prose',
            'doc_type':    DOC_TYPE,
        })

    print(f"\nChunks: {len(all_chunks)} prose", flush=True)

    print("Loading ONNX embeddings...", flush=True)
    ef     = embedding_functions.ONNXMiniLM_L6_V2()
    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)

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
        'doc_type':    c.get('doc_type', 'Policy'),
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

    with open(CHUNKS_CACHE, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f"Chunks cache saved -> {CHUNKS_CACHE}")
    print(f"\nDone. {len(all_chunks)} chunks in collection '{COLLECTION}'.")


def run():
    build()

if __name__ == '__main__':
    run()
