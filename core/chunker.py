"""
Sentence-aware text chunking shared across all policies.
Each policy passes its own max_chunk_size to tune granularity.
"""

import re
from core.parser import MIN_CHUNK, join_wrapped_lines

_SENT_BOUNDARY = re.compile(r'(?<=[.!?])\s+(?=[A-Z"\'•\-])')
_SECTION_SPLIT = re.compile(
    r'(?=^(?:\d+[\.\)]\s+[A-Z]|[A-Z][A-Z\s\-/&:]{4,}:?$))',
    re.MULTILINE,
)


def _split_at_sentences(text: str, max_len: int) -> list[str]:
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
                sentences = _SENT_BOUNDARY.split(para)
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


def chunk_text(text: str, max_chunk: int = 1000, overlap: int = 150) -> list[str]:
    """
    1. Fix PDF line-wrapping
    2. Split at section headers
    3. Within each section split at sentence boundaries if > max_chunk
    4. Merge tiny fragments into previous chunk
    5. Add trailing overlap from each chunk into the next to preserve boundary context
    """
    text = join_wrapped_lines(text)

    parts = _SECTION_SPLIT.split(text)
    raw_chunks: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) <= max_chunk:
            raw_chunks.append(part)
        else:
            raw_chunks.extend(_split_at_sentences(part, max_chunk))

    merged: list[str] = []
    for chunk in raw_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if len(chunk) < MIN_CHUNK and merged:
            merged[-1] = merged[-1] + '\n' + chunk
        else:
            merged.append(chunk)

    base = [c for c in merged if len(c.strip()) >= MIN_CHUNK]

    if overlap <= 0 or len(base) <= 1:
        return base

    # Prepend the tail of the previous chunk to each subsequent chunk
    overlapped: list[str] = [base[0]]
    for i in range(1, len(base)):
        tail = base[i - 1][-overlap:].strip()
        overlapped.append((tail + '\n' + base[i]).strip())

    return overlapped
