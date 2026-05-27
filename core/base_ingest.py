"""
Generic ingest function used by all policies.
Supports 5 modes: prose, tables, slides, ocr, faq
"""

import os
import sys
import hashlib
import json
import re

import fitz
import chromadb
from chromadb.utils import embedding_functions

from core.parser  import clean_text
from core.chunker import chunk_text

MIN_TEXT_CHARS = 150  # below this, try OCR fallback


def _fitz_table_to_text(table) -> str:
    lines = []
    for row in table.extract():
        cells = [str(c).strip().replace('\n', ' ') if c else '' for c in row]
        if any(cells):
            lines.append(' | '.join(cells))
    return '\n'.join(lines)


def _is_boilerplate_table(table_text: str) -> bool:
    return bool(re.search(
        r'HR Policy.*Classification|Classification.*Internal|Issue Date.*Policy Number',
        table_text, re.IGNORECASE
    ))


def _ocr_page(page) -> str:
    """OCR a fitz page. Returns empty string if pytesseract not installed."""
    try:
        import pytesseract
        from PIL import Image
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return pytesseract.image_to_string(img)
    except ImportError:
        return ""
    except Exception:
        return ""


def _word_sets(prose_pages: list) -> list:
    return [(pnum, set(text.lower().split())) for pnum, text in prose_pages]


def _approx_page(chunk_text_: str, prose_pages: list, page_word_sets: list) -> int:
    chunk_words = set(chunk_text_.lower().split())
    best_page, best_overlap = prose_pages[0][0], -1
    for pnum, words in page_word_sets:
        overlap = len(chunk_words & words)
        if overlap > best_overlap:
            best_overlap, best_page = overlap, pnum
    return best_page


def _add_header(text: str, policy_name: str, doc_type: str) -> str:
    """Prepend a context header so the embedding captures document identity."""
    return f"[{policy_name} | {doc_type}]\n{text}"


def build(
    pdf_path: str,
    policy_name: str,
    collection: str,
    vectorstore_dir: str,
    max_chunk: int,
    skip_pages: set,
    mode: str = "prose",          # prose | tables | slides | ocr | faq
    faq_text_path: str = "",      # used when mode="faq"
    extra_clean_fn=None,          # optional callable(raw_str)->str
    doc_type: str = "Policy",     # Policy | Insurance | Guide | Program
):
    """
    Build and store chunks for a policy.

    modes:
      prose  — PyMuPDF text extraction, single-page skip, word-set page attribution
      tables — prose + fitz table extraction per page
      slides — each page is one chunk (slide deck / page-per-section format)
      ocr    — like slides but falls back to pytesseract for image-heavy pages
      faq    — reads plain text from faq_text_path, no PDF needed
    """
    print(f"Ingesting: {policy_name}", flush=True)
    chunks_cache = os.path.join(vectorstore_dir, f'{collection}_chunks.json')
    os.makedirs(vectorstore_dir, exist_ok=True)

    all_chunks: list[dict] = []
    seen: set[str] = set()

    # ── FAQ mode ──────────────────────────────────────────────────────────────
    if mode == "faq":
        if not os.path.exists(faq_text_path):
            print(f"ERROR: FAQ file not found at {faq_text_path}")
            sys.exit(1)
        with open(faq_text_path, encoding='utf-8') as f:
            raw = f.read()
        for i, text in enumerate(chunk_text(raw, max_chunk)):
            h = hashlib.md5(text.encode()).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            all_chunks.append({
                'text':        _add_header(text, policy_name, doc_type),
                'policy_name': policy_name,
                'filename':    os.path.basename(faq_text_path),
                'page':        i + 1,
                'chunk_type':  'faq',
                'doc_type':    doc_type,
            })

    # ── PDF modes ─────────────────────────────────────────────────────────────
    else:
        if not os.path.exists(pdf_path):
            print(f"ERROR: PDF not found at {pdf_path}")
            sys.exit(1)
        print(f"Source: {pdf_path}", flush=True)

        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"Total pages: {total_pages}", flush=True)

        prose_pages: list[tuple[int, str]] = []
        table_chunks: list[dict] = []

        for page_num, page in enumerate(doc, start=1):
            if page_num in skip_pages:
                print(f"  Skipping page {page_num}", flush=True)
                continue

            raw  = page.get_text()
            text = extra_clean_fn(raw) if extra_clean_fn else clean_text(raw)

            # OCR fallback for image-heavy pages
            if mode == "ocr" and len(text) < MIN_TEXT_CHARS:
                ocr_text = _ocr_page(page)
                if ocr_text and len(ocr_text.strip()) > MIN_TEXT_CHARS:
                    text = clean_text(ocr_text)
                    print(f"  Page {page_num}: OCR ({len(text)} chars)", flush=True)
                else:
                    print(f"  Page {page_num}: skipped (no text, OCR empty)", flush=True)
                    continue
            elif len(text) < 80:
                print(f"  Page {page_num}: skipped (too short)", flush=True)
                continue

            # Table extraction
            if mode == "tables":
                for tbl in page.find_tables().tables:
                    tbl_text = _fitz_table_to_text(tbl)
                    if len(tbl_text.strip()) < 80 or _is_boilerplate_table(tbl_text):
                        continue
                    h = hashlib.md5(tbl_text.encode()).hexdigest()
                    if h in seen:
                        continue
                    seen.add(h)
                    table_chunks.append({
                        'text':        f"[TABLE — {policy_name} | {doc_type}, Page {page_num}]\n{tbl_text}",
                        'policy_name': policy_name,
                        'filename':    os.path.basename(pdf_path),
                        'page':        page_num,
                        'chunk_type':  'table',
                        'doc_type':    doc_type,
                    })

            # Slide / OCR — each page is its own chunk
            if mode in ("slides", "ocr"):
                h = hashlib.md5(text.encode()).hexdigest()
                if h not in seen:
                    seen.add(h)
                    all_chunks.append({
                        'text':        _add_header(text, policy_name, doc_type),
                        'policy_name': policy_name,
                        'filename':    os.path.basename(pdf_path),
                        'page':        page_num,
                        'chunk_type':  'slide',
                        'doc_type':    doc_type,
                    })
                    print(f"  Page {page_num}: {len(text)} chars", flush=True)
            else:
                if text:
                    prose_pages.append((page_num, text))
                    print(f"  Page {page_num}: {len(text)} chars", flush=True)

        doc.close()

        # Prose chunking (prose + tables modes)
        if mode in ("prose", "tables") and prose_pages:
            page_word_sets = _word_sets(prose_pages)
            full_prose = '\n'.join(t for _, t in prose_pages)
            for text in chunk_text(full_prose, max_chunk):
                h = hashlib.md5(text.encode()).hexdigest()
                if h in seen:
                    continue
                seen.add(h)
                prose_pages_ref = prose_pages  # capture for closure
                all_chunks.append({
                    'text':        _add_header(text, policy_name, doc_type),
                    'policy_name': policy_name,
                    'filename':    os.path.basename(pdf_path),
                    'page':        _approx_page(text, prose_pages_ref, page_word_sets),
                    'chunk_type':  'prose',
                    'doc_type':    doc_type,
                })
            all_chunks = table_chunks + all_chunks

    print(f"\nChunks: {len(all_chunks)} total", flush=True)
    if not all_chunks:
        print("WARNING: No chunks produced. Check skip_pages and PDF content.")
        return

    # ── Embed + store ─────────────────────────────────────────────────────────
    print("Loading ONNX embeddings...", flush=True)
    ef     = embedding_functions.ONNXMiniLM_L6_V2()
    client = chromadb.PersistentClient(path=vectorstore_dir)

    try:
        client.delete_collection(collection)
    except Exception:
        pass

    coll = client.create_collection(
        collection,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    ids       = [f"{collection}_{i}" for i in range(len(all_chunks))]
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
        coll.add(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  Stored {end}/{len(all_chunks)}", flush=True)

    with open(chunks_cache, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"Chunks cache -> {chunks_cache}")
    print(f"Done. {len(all_chunks)} chunks in '{collection}'.")
