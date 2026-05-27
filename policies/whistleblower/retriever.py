"""
Retriever for the Whistleblower Policy.
Hybrid: BM25 + ChromaDB semantic → RRF merge → Ollama answer.
"""

import os
import sys
import re
import json

import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.llm import ask
from policies.whistleblower.config import COLLECTION, SYSTEM_PROMPT, POLICY_NAME, TOP_K, SEM_WEIGHT

_HERE           = os.path.dirname(os.path.abspath(__file__))
VECTORSTORE_DIR = os.path.join(_HERE, '..', '..', 'vectorstore')
CHUNKS_CACHE    = os.path.join(VECTORSTORE_DIR, f'{COLLECTION}_chunks.json')

SEM_K   = 20   # semantic candidates
BM25_K  = 20   # BM25 candidates
RRF_K   = 60   # RRF constant

_STOPWORDS = frozenset(
    "what is the does a an of to in for how why can you tell me about "
    "say do any as with by at or and that this are if not all be will "
    "was from on it its i am we my their your policy hr arvind company "
    "employee employees which under covered according confirm".split()
)


def _tokenise(text: str) -> list[str]:
    t = text.lower()
    t = re.sub(r'[^\w\s]', ' ', t)
    return [w for w in t.split() if w]


class WhistleblowerRetriever:
    _instance = None

    def __init__(self):
        self._ef       = None
        self._chroma   = None
        self._bm25     = None
        self._chunks   = None
        self._loaded   = False

    def _load(self):
        if self._loaded:
            return
        if not os.path.exists(CHUNKS_CACHE):
            raise RuntimeError(
                f"Chunks cache not found. Run ingestion first:\n"
                f"  python -m policies.whistleblower.ingest"
            )
        with open(CHUNKS_CACHE, encoding='utf-8') as f:
            self._chunks = json.load(f)

        self._ef     = embedding_functions.ONNXMiniLM_L6_V2()
        client       = chromadb.PersistentClient(path=VECTORSTORE_DIR)
        self._chroma = client.get_collection(COLLECTION, embedding_function=self._ef)

        tokenised    = [_tokenise(c['text']) for c in self._chunks]
        self._bm25   = BM25Okapi(tokenised)
        self._loaded = True

    def retrieve(self, query: str) -> list[dict]:
        self._load()

        # Semantic search
        count = self._chroma.count()
        sem_k = min(SEM_K, count)
        sem_result = self._chroma.query(
            query_texts=[query],
            n_results=sem_k,
            include=["documents", "metadatas", "distances"],
        )
        sem_docs  = sem_result["documents"][0]
        sem_dists = sem_result["distances"][0]

        sem_rank: dict[int, float] = {}
        for doc, dist in zip(sem_docs, sem_dists):
            for i, c in enumerate(self._chunks):
                if c['text'][:80] == doc[:80]:
                    sem_rank[i] = 1.0 - float(dist)
                    break

        # BM25 search
        tokens   = _tokenise(query)
        scores   = self._bm25.get_scores(tokens)
        bm25_top = sorted(
            ((i, s) for i, s in enumerate(scores) if s > 0),
            key=lambda x: -x[1],
        )[:BM25_K]
        bm25_rank = {i: s for i, s in bm25_top}

        # RRF merge
        sem_ranked  = sorted(sem_rank.items(),  key=lambda x: -x[1])
        bm25_ranked = sorted(bm25_rank.items(), key=lambda x: -x[1])
        sem_rk  = {idx: r + 1 for r, (idx, _) in enumerate(sem_ranked)}
        bm25_rk = {idx: r + 1 for r, (idx, _) in enumerate(bm25_ranked)}

        all_idx = set(sem_rank) | set(bm25_rank)
        rrf = {
            idx: SEM_WEIGHT / (RRF_K + sem_rk.get(idx, RRF_K * 10))
                + 1.0 / (RRF_K + bm25_rk.get(idx, RRF_K * 10))
            for idx in all_idx
        }

        top = sorted(rrf.items(), key=lambda x: -x[1])[:TOP_K]
        return [
            {
                "text":        self._chunks[i]["text"],
                "policy_name": self._chunks[i]["policy_name"],
                "page":        self._chunks[i]["page"],
                "score":       round(s, 5),
            }
            for i, s in top
        ]


# Module-level singleton
_retriever = WhistleblowerRetriever()


def answer(query: str, chat_history: list[dict] = None) -> dict:
    """
    Retrieve relevant chunks and generate an answer.
    Returns: {text, sources, policy}
    """
    chunks = _retriever.retrieve(query)

    if not chunks:
        return {
            "text": (
                "This specific detail is not covered in the Whistleblower Policy. "
                "Please contact your Business HR."
            ),
            "sources": [],
            "policy": POLICY_NAME,
        }

    context = "\n\n---\n\n".join(
        f"[Page {c['page']}]\n{c['text']}" for c in chunks
    )

    history_text = ""
    if chat_history:
        turns = [
            f"{t['role'].upper()}: {t['content']}"
            for t in chat_history[-4:]   # last 4 turns only
        ]
        history_text = "CONVERSATION HISTORY:\n" + "\n".join(turns) + "\n\n"

    user_message = (
        f"{history_text}"
        f"POLICY CONTEXT:\n{context}\n\n"
        f"EMPLOYEE QUESTION:\n{query}"
    )

    response_text = ask(SYSTEM_PROMPT, user_message)

    sources = []
    seen = set()
    for c in chunks:
        key = (c["policy_name"], c["page"])
        if key not in seen:
            seen.add(key)
            sources.append({"policy": c["policy_name"], "page": c["page"]})

    return {
        "text":    response_text,
        "sources": sources,
        "policy":  POLICY_NAME,
    }
