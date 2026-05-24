"""
One-time script: parse all policy docs → chunk → embed → store in ChromaDB.
Run: python ingest.py
"""

import os
import pdfplumber
import chromadb
from chromadb.utils import embedding_functions
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

POLICIES_DIR = "policies"
VECTORSTORE_DIR = "vectorstore"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

# Maps filename fragment → friendly policy name
POLICY_NAMES = {
    "localconveyance": "Local Conveyance Policy",
    "domestictravel": "Domestic Travel Policy",
    "genderpolicy": "Gender Policy 2025",
    "grievance": "Grievance Mechanism Policy 2025",
    "posh": "POSH Policy (Prevention of Sexual Harassment)",
    "talentmobility": "Talent Mobility Policy",
    "whistleblower": "Whistleblower Policy",
    "joining": "Joining Policy",
}


def get_policy_name(filename: str) -> str:
    lower = filename.lower()
    for key, name in POLICY_NAMES.items():
        if key in lower:
            return name
    return os.path.splitext(filename)[0]


def extract_pdf_text(filepath: str) -> list[dict]:
    """Extract text page-by-page using pdfplumber (handles tables too)."""
    pages = []
    with pdfplumber.open(filepath) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            # Also extract tables and append as text
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    clean_row = [cell or "" for cell in row]
                    text += "\n" + " | ".join(clean_row)
            if text.strip():
                pages.append({"page": i + 1, "text": text.strip()})
    return pages


def extract_docx_text(filepath: str) -> list[dict]:
    """Extract text from DOCX, treating the whole doc as one page."""
    doc = Document(filepath)
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    # Also extract tables
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                full_text += "\n" + row_text
    return [{"page": 1, "text": full_text.strip()}]


def build_chunks(pages: list[dict], policy_name: str, filename: str) -> list[dict]:
    """Split page texts into overlapping chunks, preserving metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = []
    for page_data in pages:
        splits = splitter.split_text(page_data["text"])
        for j, chunk_text in enumerate(splits):
            if len(chunk_text.strip()) < 50:
                continue
            chunks.append({
                "text": chunk_text.strip(),
                "policy_name": policy_name,
                "filename": filename,
                "page": page_data["page"],
                "chunk_index": j,
            })
    return chunks


def main():
    print("Loading embedding model (ChromaDB ONNX — no internet needed)...")
    ef = embedding_functions.ONNXMiniLM_L6_V2()

    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    # Reset collection on each ingest run
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
    for filename in os.listdir(POLICIES_DIR):
        filepath = os.path.join(POLICIES_DIR, filename)
        policy_name = get_policy_name(filename)
        ext = os.path.splitext(filename)[1].lower()

        print(f"  Processing: {filename} → {policy_name}")
        try:
            if ext == ".pdf":
                pages = extract_pdf_text(filepath)
            elif ext in (".docx", ".doc"):
                pages = extract_docx_text(filepath)
            else:
                print(f"    Skipping unsupported format: {ext}")
                continue
        except Exception as e:
            print(f"    ERROR reading {filename}: {e}")
            continue

        chunks = build_chunks(pages, policy_name, filename)
        print(f"    → {len(pages)} pages, {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"\nTotal chunks: {len(all_chunks)} — storing in ChromaDB (embeddings auto-generated)...")

    texts = [c["text"] for c in all_chunks]
    ids = [f"chunk_{i}" for i in range(len(all_chunks))]
    metadatas = [
        {
            "policy_name": c["policy_name"],
            "filename": c["filename"],
            "page": c["page"],
            "chunk_index": c["chunk_index"],
        }
        for c in all_chunks
    ]

    # Add in batches to avoid memory spikes
    batch_size = 100
    for start in range(0, len(all_chunks), batch_size):
        end = min(start + batch_size, len(all_chunks))
        collection.add(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  Stored {end}/{len(all_chunks)} chunks...")

    print(f"Done. {len(all_chunks)} chunks stored in '{VECTORSTORE_DIR}'.")


if __name__ == "__main__":
    main()
