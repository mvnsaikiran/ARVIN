"""
PDF text + table extraction utilities shared across all policies.
"""

import re
import hashlib
import pdfplumber

MIN_CHUNK = 150

_SENTENCE_END   = re.compile(r'[.!?]["\']?\s*$')
_BULLET_LINE    = re.compile(r'^\s*[•\-–—●*]\s+|^\s*\d+[.)]\s+|^[a-z]\.\s+', re.MULTILINE)
_ALL_CAPS_HEADER = re.compile(r'^[A-Z][A-Z\s\-/&:]{4,}$')
_BOILERPLATE    = re.compile(
    r'HR Policy\s+Classification'
    r'|Classification:\s+Internal'
    r'|Issue Date:.*Policy Number:'
    r'|CLASSIFICATION:\s+Internal'
    r'|www\.arvind\.com'
    r'|P\s*a\s*g\s*e\s*\d+\s*[|]\s*\d+'
    r'|^\s*\d+\s*$'
    r'|^Confidential\s*$'
    r'|Private\s+&\s*Confidential Only for Internal Circulation'
    r'|WHISTLEBLOWER POLICY\s*[|]\s*Confidential',
    re.IGNORECASE | re.MULTILINE,
)


def clean_text(raw: str) -> str:
    lines = [ln for ln in raw.split('\n') if not _BOILERPLATE.search(ln)]
    text = '\n'.join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def join_wrapped_lines(raw: str) -> str:
    """Rejoin PDF word-wrapped lines into proper paragraphs."""
    lines = raw.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            result.append('')
            i += 1
            continue
        para = line
        while i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if not next_line:
                break
            if _SENTENCE_END.search(para):
                break
            if _BULLET_LINE.match(lines[i + 1]) or _ALL_CAPS_HEADER.match(next_line):
                break
            para = para.rstrip() + ' ' + next_line
            i += 1
        result.append(para)
        i += 1
    return '\n'.join(result)


def table_to_text(rows: list) -> str:
    lines = []
    for row in rows:
        cells = [str(c).strip().replace('\n', ' ') if c else '' for c in row]
        if any(cells):
            lines.append(' | '.join(cells))
    return '\n'.join(lines)


def is_boilerplate_table(rows: list) -> bool:
    flat = ' '.join(str(cell) for row in rows for cell in row if cell)
    return bool(re.search(
        r'HR Policy\s+Classification|Classification:\s+Internal|Issue Date:.*Policy Number:',
        flat, re.IGNORECASE
    ))


def extract_pdf(filepath: str, policy_name: str, filename: str,
                page_per_section: bool = False) -> list[dict]:
    """
    Extract chunks from a PDF.
    Returns list of dicts: {text, policy_name, filename, page, chunk_type}
    """
    table_chunks = []
    prose_parts = []          # (page_num, cleaned_text)
    seen_hashes: set[str] = set()

    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            raw = page.extract_text() or ''

            # Tables — extract per page, atomic
            page_lines = [
                ln.strip() for ln in clean_text(raw).split('\n')
                if ln.strip() and len(ln.strip()) > 20
            ]
            page_context = ' '.join(page_lines[-3:]) if page_lines else ''

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
                full = (
                    f'[TABLE — {policy_name}, Page {page_num}]\n{page_context}\n{text}'
                    if page_context else
                    f'[TABLE — {policy_name}, Page {page_num}]\n{text}'
                )
                table_chunks.append({
                    'text': full,
                    'policy_name': policy_name,
                    'filename': filename,
                    'page': page_num,
                    'chunk_type': 'table',
                })

            cleaned = clean_text(raw)
            if cleaned:
                prose_parts.append((page_num, cleaned))

    if not prose_parts:
        return table_chunks

    # Slide/page-per-section format (e.g. MediBuddy, Talent Mobility)
    if page_per_section:
        slide_chunks = []
        for pnum, text in prose_parts:
            text = text.strip()
            if len(text) < MIN_CHUNK:
                continue
            h = hashlib.md5(text.encode()).hexdigest()
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            slide_chunks.append({
                'text': text,
                'policy_name': policy_name,
                'filename': filename,
                'page': pnum,
                'chunk_type': 'prose',
            })
        return table_chunks + slide_chunks

    # Normal prose: concatenate all pages, then split logically
    full_prose = '\n'.join(text for _, text in prose_parts)

    # Build page offset map for approximate page attribution
    page_offsets = []
    offset = 0
    for pnum, text in prose_parts:
        page_offsets.append((offset, offset + len(text), pnum))
        offset += len(text) + 1

    def approx_page(chunk_text: str) -> int:
        needle = chunk_text[:80].strip()
        pos = full_prose.find(needle)
        if pos < 0:
            return prose_parts[0][0]
        for start, end, pnum in page_offsets:
            if start <= pos < end:
                return pnum
        return prose_parts[-1][0]

    return table_chunks  # prose chunks are returned by the policy's own chunker
