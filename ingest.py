"""
Structure-Aware Hybrid Chunking for Arvind HR Policies — v3.

Improvements over previous versions:
  1. ALL 17 policies have correct human-readable policy names
  2. Document-level prose extraction — no mid-sentence page-boundary cuts
  3. PDF line-joining: consecutive non-sentence-ending lines are joined before splitting
  4. Sentence-aware splitting — chunks end at sentence boundaries
  5. Minimum 150-char chunks — eliminates meaningless single-line fragments
  6. Tables extracted per-page (atomic, with accurate page numbers)
"""

import os, re, hashlib, json
import pdfplumber
import chromadb
from chromadb.utils import embedding_functions
from docx import Document

_HERE           = os.path.dirname(os.path.abspath(__file__))
POLICIES_SRC    = os.path.join(_HERE, "policies")
VECTORSTORE_DIR = os.path.join(_HERE, "vectorstore")
MAX_PROSE_CHUNK = 1400
MIN_CHUNK       = 150   # ignore tiny fragments

# Per-policy chunk sizes — tuned to each policy's content type:
#   Small chunks  -> precise clause/rate retrieval (rate tables, POSH sections)
#   Large chunks  -> preserve full Q&A pairs or multi-step procedures
POLICY_CHUNK_SIZES: dict[str, int] = {
    # Rate/table-heavy: small chunks isolate each grade row or rate clause
    "Domestic Travel Policy":               700,
    "Local Conveyance Policy":              700,
    "Group Health Insurance Policy":        800,
    "Group Personal Accident Insurance Scheme": 800,
    "Joining Policy":                       800,
    "Employee Expense Reimbursement Policy":900,
    # Large policy with many sections: small chunks = precise section retrieval
    "POSH Policy (Prevention of Sexual Harassment)": 700,
    # Referral: small chunks so bonus table gets its own chunk
    "Pankh Employee Referral":              600,
    # F&F: notice period + tuition clauses need their own chunks
    "Exit & Full & Final Settlement Policy":900,
    # Q&A / FAQ format: large chunks keep question + answer together
    "Employee Assistance Program (EAP)":   2000,
    # Procedural: keep full procedure in one chunk
    "Grievance Mechanism Policy 2025":     1600,
    "Whistleblower Policy":                1600,
    "Domestic Travel Expense Settlement Procedure": 1600,
    # Small policies: large chunks fine (few chunks anyway)
    "Group Term Life Insurance":           1400,
    "Voluntary Death Contribution Scheme": 1400,
    "Gender Policy 2025":                  1400,
    "Talent Mobility Policy":              1400,   # page-per-section overrides this
    "MediBuddy Health & Wellness (User Manual)": 1400,  # page-per-section overrides
}

# Policies that use a SLIDE / PAGE-PER-SECTION format (not continuous prose)
# For these, each page is kept as its own chunk rather than joining all pages.
PAGE_PER_SECTION_POLICIES = {
    "Talent Mobility Policy",
    "MediBuddy Health & Wellness (User Manual)",
}

# Canonical policy name lookup — keys are substrings of the lowercase filename stem.
# Longest-key-first matching ensures specificity (e.g. "group health insurance" before "health").
POLICY_NAMES = {
    "local-conveyance":        "Local Conveyance Policy",
    "domestic-travel":         "Domestic Travel Policy",
    "group health insurance":  "Group Health Insurance Policy",
    "personal accident":       "Group Personal Accident Insurance Scheme",
    "employee expense":        "Employee Expense Reimbursement Policy",
    "travel settlement":       "Domestic Travel Expense Settlement Procedure",
    "voluntary death":         "Voluntary Death Contribution Scheme",
    "full & final":            "Exit & Full & Final Settlement Policy",
    "term life":               "Group Term Life Insurance",
    "grievance":               "Grievance Mechanism Policy 2025",
    "whistleblower":           "Whistleblower Policy",
    "medibuddy":               "MediBuddy Health & Wellness (User Manual)",
    "pankh":                   "Pankh Employee Referral",
    "talent":                  "Talent Mobility Policy",
    "joining":                 "Joining Policy",
    "gender":                  "Gender Policy 2025",
    "1to1":                    "Employee Assistance Program (EAP)",
    "posh":                    "POSH Policy (Prevention of Sexual Harassment)",
}

# Regex: top-level section headers only (keeps sub-items like 5.1 or a. in parent chunk)
SECTION_HEADER_RE = re.compile(
    r'^(?:'
    r'\d+[\.\)]\s+[A-Z]'           # "1. Title"  or  "2) Title"
    r'|[A-Z][A-Z\s\-/]{4,}:?$'    # ALL CAPS TITLE (5+ chars)
    r'|(?:ANNEXURE|SCHEDULE|APPENDIX)\s'
    r')',
    re.MULTILINE,
)

# Lines / patterns to strip from extracted page text
BOILERPLATE_RE = re.compile(
    r'HR Policy\s+Classification'
    r'|Classification:\s+Internal'
    r'|Issue Date:.*Policy Number:'
    r'|CLASSIFICATION:\s+Internal'
    r'|This document is confidential.*?internal circulation only'
    r'|www\.arvind\.com'
    r'|P\s*a\s*g\s*e\s*\d+\s*[|]\s*\d+'   # "P a g e 1 | 2"
    r'|^\s*\d+\s*$'                         # bare page numbers on their own line
    r'|WHISTLEBLOWER POLICY\s*[|]\s*Confidential'  # WB footer every page
    r'|^Confidential\s*$'                   # POSH/WB cover page
    r'|^HR Policy\s+(?:Anti-Money Laundering|Grievance Mechanism|Group Health Insurance Policy|SOP)'
                                            # mislabeled/repeated page headers
    r'|Private\s+&\s*Confidential Only for Internal Circulation'  # POSH footer
    r'|^Domestic Travel Policy\s*$'         # DTP repeated page header
    , re.IGNORECASE | re.MULTILINE
)

# Table boilerplate check
_TABLE_BP = re.compile(
    r'HR Policy\s+Classification|Classification:\s+Internal|Issue Date:.*Policy Number:',
    re.IGNORECASE
)


def get_policy_name(filename: str) -> str:
    stem = os.path.splitext(filename)[0].lower()
    # Match longest key first (to prefer specific over generic)
    for key in sorted(POLICY_NAMES, key=len, reverse=True):
        if key in stem:
            return POLICY_NAMES[key]
    return os.path.splitext(filename)[0]   # fallback: raw stem


def is_boilerplate_table(rows: list) -> bool:
    flat = " ".join(str(cell) for row in rows for cell in row if cell)
    return bool(_TABLE_BP.search(flat))


def table_to_text(rows: list) -> str:
    lines = []
    for row in rows:
        cells = [str(c).strip().replace('\n', ' ') if c else '' for c in row]
        if any(cells):
            lines.append(' | '.join(cells))
    return '\n'.join(lines)


# ── PDF line-joining ──────────────────────────────────────────────────────────
# PDFs word-wrap text: a paragraph is split across many lines each ending
# without punctuation. We join those continuation lines before chunking.
_SENTENCE_END = re.compile(r'[.!?]["\']?\s*$')
_BULLET_LINE   = re.compile(r'^\s*[•\-–—●\*]\s+|^\s*\d+[.)]\s+|^[a-z]\.\s+', re.MULTILINE)
_ALL_CAPS_HEADER = re.compile(r'^[A-Z][A-Z\s\-/&:]{4,}$')


def _join_wrapped_lines(raw_text: str) -> str:
    """
    Join PDF word-wrapped lines into proper paragraphs.
    A line is a continuation (not a new paragraph) if:
      - The previous line did NOT end with sentence-ending punctuation
      - The current line does NOT start with a bullet, number, or ALL-CAPS header
    """
    lines = raw_text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            result.append('')
            i += 1
            continue

        # Accumulate continuation lines into this paragraph
        para = line
        while i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if not next_line:
                break   # blank line = paragraph break
            # Stop accumulating if previous line ended a sentence
            if _SENTENCE_END.search(para):
                break
            # Stop if next line is a structural element (header/bullet)
            if _BULLET_LINE.match(lines[i + 1]) or _ALL_CAPS_HEADER.match(next_line):
                break
            para = para.rstrip() + ' ' + next_line
            i += 1
        result.append(para)
        i += 1
    return '\n'.join(result)


def _clean_page_text(raw: str) -> str:
    """Strip boilerplate patterns and normalise whitespace."""
    # Remove boilerplate lines
    lines = [ln for ln in raw.split('\n') if not BOILERPLATE_RE.search(ln)]
    text = '\n'.join(lines)
    # Collapse 3+ blank lines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── Sentence-aware splitting ──────────────────────────────────────────────────

def _split_at_sentences(text: str, max_len: int) -> list[str]:
    """
    Split text into chunks ≤ max_len, always at sentence boundaries.
    Never cuts mid-sentence.
    """
    # Split at sentence-ending punctuation followed by whitespace + capital/bullet
    SENT_BOUNDARY = re.compile(r'(?<=[.!?])\s+(?=[A-Z"\'•\-])')

    paras = re.split(r'\n{2,}', text)
    chunks = []
    current = ''

    for para in paras:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 <= max_len:
            current = (current + '\n\n' + para).strip() if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) <= max_len:
                current = para
            else:
                # Para too long — split at sentence boundaries
                sentences = SENT_BOUNDARY.split(para)
                sub = ''
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(sub) + len(sent) + 1 <= max_len:
                        sub = (sub + ' ' + sent).strip() if sub else sent
                    else:
                        if sub:
                            chunks.append(sub)
                        sub = sent
                current = sub

    if current.strip():
        chunks.append(current.strip())
    return chunks


def split_prose_into_chunks(text: str, max_chunk: int = MAX_PROSE_CHUNK) -> list[str]:
    """
    1. Join PDF word-wrapped lines into full sentences/paragraphs
    2. Split at section headers (ALL-CAPS / numbered)
    3. Within each section, split at sentence boundaries if > MAX_PROSE_CHUNK
    4. Merge tiny fragments (< MIN_CHUNK) into previous chunk
    """
    # Step 1: fix PDF line wrapping
    text = _join_wrapped_lines(text)

    # Step 2: split at section headers
    parts = re.split(
        r'(?=^(?:\d+[\.\)]\s+[A-Z]|[A-Z][A-Z\s\-/&:]{4,}:?$))',
        text, flags=re.MULTILINE
    )

    raw_chunks: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) <= max_chunk:
            raw_chunks.append(part)
        else:
            raw_chunks.extend(_split_at_sentences(part, max_chunk))

    # Step 4: merge tiny trailing fragments
    merged: list[str] = []
    for chunk in raw_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if len(chunk) < MIN_CHUNK and merged:
            merged[-1] = merged[-1] + '\n' + chunk
        else:
            merged.append(chunk)

    return [c for c in merged if len(c.strip()) >= MIN_CHUNK]


# ── PDF extractor ─────────────────────────────────────────────────────────────

def extract_pdf_chunks(filepath: str, policy_name: str, filename: str) -> list[dict]:
    """
    Tables: per-page, atomic (with accurate page numbers).
    Prose:
      - Normal policies: all pages concatenated, then split logically.
      - PAGE_PER_SECTION policies (slide decks): each page chunked independently.
    """
    page_per_section = policy_name in PAGE_PER_SECTION_POLICIES
    table_chunks: list[dict] = []
    prose_parts: list[tuple[int, str]] = []   # (page_num, cleaned_text)
    seen_hashes: set[str] = set()

    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):

            # ── Tables (per-page) ──────────────────────────────────────
            # Extract page prose first so we can prefix tables with context
            page_raw = page.extract_text() or ''
            page_prose_lines = [
                ln.strip() for ln in _clean_page_text(page_raw).split('\n')
                if ln.strip() and len(ln.strip()) > 25
            ]
            page_context = ' '.join(page_prose_lines[-4:]) if page_prose_lines else ''

            for table in (page.extract_tables() or []):
                if not table or is_boilerplate_table(table):
                    continue
                text = table_to_text(table)
                if len(text.strip()) < MIN_CHUNK:
                    continue
                h = hashlib.md5(text.encode()).hexdigest()
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                full_text = (
                    f'[TABLE — {policy_name}, Page {page_num}]\n'
                    f'{page_context}\n{text}' if page_context else
                    f'[TABLE — {policy_name}, Page {page_num}]\n{text}'
                )
                table_chunks.append({
                    'text': full_text,
                    'policy_name': policy_name,
                    'filename': filename,
                    'page': page_num,
                    'chunk_type': 'table',
                    'section_title': '',
                })

            # ── Prose (collect for document-level split) ───────────────
            raw = page.extract_text() or ''
            cleaned = _clean_page_text(raw)
            if cleaned:
                prose_parts.append((page_num, cleaned))

    # ── Prose processing ──────────────────────────────────────────────────
    if not prose_parts:
        return table_chunks

    # Slide-format: each page is its own independent chunk
    if page_per_section:
        slide_chunks: list[dict] = []
        for pnum, text in prose_parts:
            text = text.strip()
            if len(text) < MIN_CHUNK:
                continue
            h = hashlib.md5(text.encode()).hexdigest()
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            first_line = text.split('\n')[0].strip()
            section_title = first_line if SECTION_HEADER_RE.match(first_line) else ''
            slide_chunks.append({
                'text': text,
                'policy_name': policy_name,
                'filename': filename,
                'page': pnum,
                'chunk_type': 'prose',
                'section_title': section_title,
            })
        return table_chunks + slide_chunks

    full_prose = '\n'.join(text for _, text in prose_parts)

    # Build page-offset index for attribution
    page_offsets: list[tuple[int, int, int]] = []
    offset = 0
    for pnum, text in prose_parts:
        page_offsets.append((offset, offset + len(text), pnum))
        offset += len(text) + 1   # +1 for the '\n' joining separator

    def approx_page(chunk_text: str) -> int:
        needle = chunk_text[:80].strip()
        pos = full_prose.find(needle)
        if pos < 0:
            return prose_parts[0][0]
        for start, end, pnum in page_offsets:
            if start <= pos < end:
                return pnum
        return prose_parts[-1][0]

    prose_chunks: list[dict] = []
    policy_max_chunk = POLICY_CHUNK_SIZES.get(policy_name, MAX_PROSE_CHUNK)
    for chunk_text in split_prose_into_chunks(full_prose, max_chunk=policy_max_chunk):
        h = hashlib.md5(chunk_text.encode()).hexdigest()
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        first_line = chunk_text.split('\n')[0].strip()
        section_title = first_line if SECTION_HEADER_RE.match(first_line) else ''
        has_numbers = bool(re.search(
            r'₹\s*\d+|\d+\s*(?:per|/)\s*(?:km|day|month|week)|Rs\.?\s*\d+',
            chunk_text, re.IGNORECASE
        ))
        prose_chunks.append({
            'text': chunk_text,
            'policy_name': policy_name,
            'filename': filename,
            'page': approx_page(chunk_text),
            'chunk_type': 'table_data' if has_numbers else 'prose',
            'section_title': section_title,
        })

    return table_chunks + prose_chunks


# ── DOCX extractor ────────────────────────────────────────────────────────────

def extract_docx_chunks(filepath: str, policy_name: str, filename: str) -> list[dict]:
    doc = Document(filepath)
    chunks: list[dict] = []
    seen_hashes: set[str] = set()

    for table in doc.tables:
        rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        if is_boilerplate_table(rows):
            continue
        text = table_to_text(rows)
        if len(text.strip()) < MIN_CHUNK:
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


# ── Main ──────────────────────────────────────────────────────────────────────

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

    all_chunks: list[dict] = []
    for filename in sorted(os.listdir(POLICIES_SRC)):
        filepath = os.path.join(POLICIES_SRC, filename)
        if not os.path.isfile(filepath):
            continue
        policy_name = get_policy_name(filename)
        ext = os.path.splitext(filename)[1].lower()

        print(f"\n  {filename} -> {policy_name}", flush=True)
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

        tables = sum(1 for c in chunks if c['chunk_type'] == 'table')
        prose  = sum(1 for c in chunks if c['chunk_type'] != 'table')
        print(f"    -> {len(chunks)} chunks ({tables} tables, {prose} prose)", flush=True)
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

    chunks_file = os.path.join(VECTORSTORE_DIR, 'chunks.json')
    with open(chunks_file, 'w') as f:
        json.dump([{
            'text':        c['text'],
            'policy_name': c['policy_name'],
            'page':        c['page'],
            'filename':    c['filename'],
            'chunk_type':  c['chunk_type'],
        } for c in all_chunks], f)
    print(f"Saved chunks manifest -> {chunks_file}", flush=True)
    print(f"\nDone. {len(all_chunks)} chunks in vectorstore.", flush=True)


if __name__ == "__main__":
    main()
