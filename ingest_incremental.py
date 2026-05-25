"""
Incremental ingestion — adds NEW policy files to existing ChromaDB collection.
Does NOT delete or rebuild existing chunks. Appends to chunks.json.
"""

import os, re, hashlib, json
import pdfplumber
import chromadb
from chromadb.utils import embedding_functions

POLICIES_SRC    = "policies"
VECTORSTORE_DIR = "vectorstore"
CHUNKS_FILE     = os.path.join(VECTORSTORE_DIR, "chunks.json")
MAX_PROSE_CHUNK = 1400
PROSE_OVERLAP   = 200
MIN_CHUNK       = 30

# Map filename fragment → policy_name for NEW policies only
NEW_POLICY_NAMES = {
    "group_term_life_insurance":         "Group Term Life Insurance",
    "pankh_employee_referral":           "Pankh Employee Referral",
    "travel_settlement_procedure":       "Domestic Travel Expense Settlement Procedure",
    "voluntary_death_contribution":      "Voluntary Death Contribution Scheme",
}

# Only process these files (leave existing policies untouched)
NEW_FILES = list(NEW_POLICY_NAMES.keys())

BOILERPLATE_PATTERNS = [
    r'HR Policy\s+Classification',
    r'Classification:\s+Internal',
    r'Issue Date:.*Policy Number:',
    r'CLASSIFICATION:\s+Internal',
    r'www\.arvind\.com\s*$',
]
BOILERPLATE_RE = re.compile('|'.join(BOILERPLATE_PATTERNS), re.IGNORECASE | re.MULTILINE)

SECTION_HEADER_RE = re.compile(
    r'^(?:\d+(?:\.\d+)*[\.\)]\s+[A-Z]|[A-Z][A-Z\s\-/]{4,}:?$|(?:ANNEXURE|SCHEDULE|APPENDIX)\s)',
    re.MULTILINE,
)


def get_policy_name(filename: str) -> str | None:
    lower = filename.lower()
    for key, name in NEW_POLICY_NAMES.items():
        if key in lower:
            return name
    return None


def is_boilerplate_table(rows):
    flat = " ".join(str(cell) for row in rows for cell in row if cell)
    return bool(BOILERPLATE_RE.search(flat))


def table_to_text(rows):
    lines = []
    for row in rows:
        cells = [str(c).strip().replace('\n', ' ') if c else '' for c in row]
        if any(cells):
            lines.append(' | '.join(cells))
    return '\n'.join(lines)


def split_prose_into_chunks(text: str) -> list[str]:
    parts = re.split(r'(?=^(?:\d+[\.\)]\s+[A-Z]|[A-Z][A-Z\s\-/]{4,}:?$))', text, flags=re.MULTILINE)
    chunks = []
    for part in parts:
        part = part.strip()
        if not part or len(part) < MIN_CHUNK:
            continue
        if len(part) <= MAX_PROSE_CHUNK:
            chunks.append(part)
        else:
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
            tables = page.extract_tables() or []
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

            raw = page.extract_text() or ''
            lines = [l for l in raw.split('\n') if not BOILERPLATE_RE.search(l)]
            text = '\n'.join(lines).strip()
            if not text:
                continue
            for chunk_text in split_prose_into_chunks(text):
                h = hashlib.md5(chunk_text.encode()).hexdigest()
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
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


def main():
    print("Loading existing chunks.json...", flush=True)
    with open(CHUNKS_FILE) as f:
        existing_chunks = json.load(f)
    start_id = len(existing_chunks)
    print(f"  Existing chunks: {start_id} (next ID = chunk_{start_id})", flush=True)

    print("\nLoading ChromaDB...", flush=True)
    ef = embedding_functions.ONNXMiniLM_L6_V2()
    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    col = client.get_collection("arvind_policies", embedding_function=ef)
    print(f"  ChromaDB count before: {col.count()}", flush=True)

    new_chunks = []
    for filename in sorted(os.listdir(POLICIES_SRC)):
        policy_name = get_policy_name(filename)
        if policy_name is None:
            continue
        filepath = os.path.join(POLICIES_SRC, filename)
        if not os.path.isfile(filepath):
            continue
        ext = os.path.splitext(filename)[1].lower()
        if ext != '.pdf':
            print(f"  Skipping non-PDF: {filename}", flush=True)
            continue

        print(f"\n  {filename} → {policy_name}", flush=True)
        try:
            chunks = extract_pdf_chunks(filepath, policy_name, filename)
        except Exception as e:
            print(f"    ERROR: {e}", flush=True)
            continue

        tables = sum(1 for c in chunks if c['chunk_type'] == 'table')
        prose  = sum(1 for c in chunks if c['chunk_type'] != 'table')
        print(f"    → {len(chunks)} chunks ({tables} tables, {prose} prose)", flush=True)
        new_chunks.extend(chunks)

    if not new_chunks:
        print("\nNo new chunks extracted. Check filename matching.", flush=True)
        return

    print(f"\nTotal new chunks: {len(new_chunks)} — embedding and storing...", flush=True)

    ids       = [f"chunk_{start_id + i}" for i in range(len(new_chunks))]
    texts     = [c['text'] for c in new_chunks]
    metadatas = [{
        'policy_name':   c['policy_name'],
        'filename':      c['filename'],
        'page':          c['page'],
        'chunk_type':    c['chunk_type'],
        'section_title': c['section_title'],
    } for c in new_chunks]

    batch = 100
    for start in range(0, len(new_chunks), batch):
        end = min(start + batch, len(new_chunks))
        col.add(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  Stored {end}/{len(new_chunks)}", flush=True)

    print(f"  ChromaDB count after: {col.count()}", flush=True)

    # Append to chunks.json
    updated = existing_chunks + new_chunks
    with open(CHUNKS_FILE, 'w') as f:
        json.dump([{
            'text':        c['text'],
            'policy_name': c['policy_name'],
            'page':        c.get('page', 1),
            'filename':    c.get('filename', ''),
            'chunk_type':  c.get('chunk_type', 'prose'),
        } for c in updated], f)
    print(f"\nUpdated chunks.json: {len(existing_chunks)} → {len(updated)} chunks", flush=True)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
