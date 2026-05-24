"""
Structure-Aware Hybrid Chunking for Arvind HR Policies.

Strategy:
  1. Extract tables as atomic chunks (never split mid-table)
  2. Skip repeated boilerplate header tables (Classification/HR Policy header)
  3. Split prose at section headers first, then paragraph boundaries
  4. Overlap only on prose chunks, not tables
  5. Rich metadata: section_title, chunk_type, has_numbers
"""

import os, re, hashlib
import pdfplumber
import chromadb
from chromadb.utils import embedding_functions
from docx import Document

POLICIES_DIR = "vectorstore"
POLICIES_SRC = "policies"
VECTORSTORE_DIR = "vectorstore"
MAX_PROSE_CHUNK = 1400
PROSE_OVERLAP   = 200
MIN_CHUNK       = 30

POLICY_NAMES = {
    "localconveyance": "Local Conveyance Policy",
    "domestictravel":  "Domestic Travel Policy",
    "genderpolicy":    "Gender Policy 2025",
    "grievance":       "Grievance Mechanism Policy 2025",
    "posh":            "POSH Policy (Prevention of Sexual Harassment)",
    "talentmobility":  "Talent Mobility Policy",
    "whistleblower":   "Whistleblower Policy",
    "joining":         "Joining Policy",
}

# Regex for section headers (numbered or ALL-CAPS)
SECTION_HEADER_RE = re.compile(
    r'^(?:'
    r'\d+(?:\.\d+)*[\.\)]\s+[A-Z]'      # 1. or 1.1. or 1)
    r'|[A-Z][A-Z\s\-/]{4,}:?$'          # ALL CAPS TITLE
    r'|(?:ANNEXURE|SCHEDULE|APPENDIX)\s' # Annexures
    r')',
    re.MULTILINE,
)

# Header tables repeated on every page — skip these
BOILERPLATE_PATTERNS = [
    r'HR Policy\s+Classification',
    r'Classification:\s+Internal',
    r'Issue Date:.*Policy Number:',
    r'CLASSIFICATION:\s+Internal',
]
BOILERPLATE_RE = re.compile('|'.join(BOILERPLATE_PATTERNS), re.IGNORECASE)


def get_policy_name(filename: str) -> str:
    lower = filename.lower()
    for key, name in POLICY_NAMES.items():
        if key in lower:
            return name
    return os.path.splitext(filename)[0]


def is_boilerplate_table(rows: list) -> bool:
    """Return True if this table is the repeated HR Policy header."""
    flat = " ".join(str(cell) for row in rows for cell in row if cell)
    return bool(BOILERPLATE_RE.search(flat))


def table_to_text(rows: list) -> str:
    """Convert table rows to clean pipe-delimited text."""
    lines = []
    for row in rows:
        cells = [str(c).strip().replace('\n', ' ') if c else '' for c in row]
        if any(cells):
            lines.append(' | '.join(cells))
    return '\n'.join(lines)


def split_prose_into_chunks(text: str) -> list[str]:
    """
    Split prose text at section headers first, then paragraphs,
    keeping chunks under MAX_PROSE_CHUNK with PROSE_OVERLAP.
    """
    # Split only at TOP-LEVEL section boundaries (not sub-items like 5.1. or a.)
    # This keeps list items (5.1, 5.2 … or a., b., …) together in their parent section chunk
    parts = re.split(r'(?=^(?:\d+[\.\)]\s+[A-Z]|[A-Z][A-Z\s\-/]{4,}:?$))', text, flags=re.MULTILINE)
    chunks = []
    for part in parts:
        part = part.strip()
        if not part or len(part) < MIN_CHUNK:
            continue
        if len(part) <= MAX_PROSE_CHUNK:
            chunks.append(part)
        else:
            # Split long sections at paragraph boundaries
            paragraphs = re.split(r'\n{2,}', part)
            current = ''
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                if len(current) + len(para) + 2 <= MAX_PROSE_CHUNK:
                    current = (current + '\n\n' + para).strip()
                else:
                    if current:
                        chunks.append(current)
                    # Overlap: keep last PROSE_OVERLAP chars of previous chunk
                    overlap = current[-PROSE_OVERLAP:] if len(current) > PROSE_OVERLAP else current
                    current = (overlap + '\n\n' + para).strip() if overlap else para
            if current and len(current) >= MIN_CHUNK:
                chunks.append(current)
    return chunks


def extract_pdf_chunks(filepath: str, policy_name: str, filename: str) -> list[dict]:
    chunks = []
    seen_hashes = set()

    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # ── Tables first (atomic chunks) ──────────────────────────
            tables = page.extract_tables() or []
            table_bboxes = []
            for table in tables:
                if not table or is_boilerplate_table(table):
                    continue
                text = table_to_text(table)
                if len(text) < MIN_CHUNK:
                    continue
                h = hashlib.md5(text.encode()).hexdigest()
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                chunks.append({
                    'text': f'[TABLE — {policy_name}, Page {page_num}]\n{text}',
                    'policy_name': policy_name,
                    'filename': filename,
                    'page': page_num,
                    'chunk_type': 'table',
                    'section_title': '',
                })

            # ── Prose text ────────────────────────────────────────────
            raw = page.extract_text() or ''
            # Remove boilerplate lines
            lines = [l for l in raw.split('\n')
                     if not BOILERPLATE_RE.search(l)]
            text = '\n'.join(lines).strip()
            if not text:
                continue

            for chunk_text in split_prose_into_chunks(text):
                h = hashlib.md5(chunk_text.encode()).hexdigest()
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                # Detect section title from first line
                first_line = chunk_text.split('\n')[0].strip()
                section_title = first_line if SECTION_HEADER_RE.match(first_line) else ''
                has_numbers = bool(re.search(r'₹\s*\d+|\d+\s*(?:per|/)\s*(?:km|day|month)', chunk_text, re.IGNORECASE))
                chunks.append({
                    'text': chunk_text,
                    'policy_name': policy_name,
                    'filename': filename,
                    'page': page_num,
                    'chunk_type': 'table_data' if has_numbers else 'prose',
                    'section_title': section_title,
                })

    return chunks


def extract_docx_chunks(filepath: str, policy_name: str, filename: str) -> list[dict]:
    doc = Document(filepath)
    chunks = []
    seen_hashes = set()

    # Tables first
    for table in doc.tables:
        rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        if is_boilerplate_table(rows):
            continue
        text = table_to_text(rows)
        if len(text) < MIN_CHUNK:
            continue
        h = hashlib.md5(text.encode()).hexdigest()
        if h not in seen_hashes:
            seen_hashes.add(h)
            chunks.append({
                'text': f'[TABLE — {policy_name}]\n{text}',
                'policy_name': policy_name,
                'filename': filename,
                'page': 1,
                'chunk_type': 'table',
                'section_title': '',
            })

    # Prose paragraphs
    full_text = '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
    for chunk_text in split_prose_into_chunks(full_text):
        h = hashlib.md5(chunk_text.encode()).hexdigest()
        if h not in seen_hashes:
            seen_hashes.add(h)
            first_line = chunk_text.split('\n')[0].strip()
            section_title = first_line if SECTION_HEADER_RE.match(first_line) else ''
            chunks.append({
                'text': chunk_text,
                'policy_name': policy_name,
                'filename': filename,
                'page': 1,
                'chunk_type': 'prose',
                'section_title': section_title,
            })

    return chunks


def main():
    print("Loading ChromaDB ONNX embeddings...", flush=True)
    ef = embedding_functions.ONNXMiniLM_L6_V2()

    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    try:
        client.delete_collection("arvind_policies")
    except Exception:
        pass
    collection = client.create_collection(
        "arvind_policies",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    all_chunks = []
    for filename in sorted(os.listdir(POLICIES_SRC)):
        filepath = os.path.join(POLICIES_SRC, filename)
        if not os.path.isfile(filepath):
            continue
        policy_name = get_policy_name(filename)
        ext = os.path.splitext(filename)[1].lower()

        print(f"\n  {filename} → {policy_name}", flush=True)
        try:
            if ext == '.pdf':
                chunks = extract_pdf_chunks(filepath, policy_name, filename)
            elif ext in ('.docx', '.doc'):
                chunks = extract_docx_chunks(filepath, policy_name, filename)
            else:
                print(f"    Skipping {ext}", flush=True)
                continue
        except Exception as e:
            print(f"    ERROR: {e}", flush=True)
            continue

        tables  = sum(1 for c in chunks if c['chunk_type'] == 'table')
        prose   = sum(1 for c in chunks if c['chunk_type'] != 'table')
        print(f"    → {len(chunks)} chunks ({tables} tables, {prose} prose)", flush=True)
        all_chunks.extend(chunks)

    print(f"\nTotal: {len(all_chunks)} chunks — embedding and storing...", flush=True)

    ids       = [f"chunk_{i}" for i in range(len(all_chunks))]
    texts     = [c['text'] for c in all_chunks]
    metadatas = [{
        'policy_name':   c['policy_name'],
        'filename':      c['filename'],
        'page':          c['page'],
        'chunk_type':    c['chunk_type'],
        'section_title': c['section_title'],
    } for c in all_chunks]

    batch = 100
    for start in range(0, len(all_chunks), batch):
        end = min(start + batch, len(all_chunks))
        collection.add(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  Stored {end}/{len(all_chunks)}", flush=True)

    # Save chunks manifest for BM25 hybrid retrieval
    chunks_file = os.path.join(VECTORSTORE_DIR, 'chunks.json')
    import json as _json
    with open(chunks_file, 'w') as f:
        _json.dump([{
            'text':        c['text'],
            'policy_name': c['policy_name'],
            'page':        c['page'],
            'filename':    c['filename'],
            'chunk_type':  c['chunk_type'],
        } for c in all_chunks], f)
    print(f"Saved chunks manifest → {chunks_file}", flush=True)

    print(f"\nDone. {len(all_chunks)} chunks in vectorstore.", flush=True)


if __name__ == "__main__":
    main()
