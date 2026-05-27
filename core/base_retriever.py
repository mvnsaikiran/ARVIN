"""
Generic hybrid retriever used by ALL policies.
Each policy creates one instance with its own config values.
"""

import os
import re
import json
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

from core.llm import ask

SEM_K  = 20
BM25_K = 20
RRF_K  = 60


def _tokenise(text: str) -> list[str]:
    t = text.lower()
    t = re.sub(r'[^\w\s]', ' ', t)
    return [w for w in t.split() if w]


class PolicyRetriever:
    def __init__(
        self,
        collection: str,
        system_prompt: str,
        policy_name: str,
        top_k: int,
        sem_weight: float,
        vectorstore_dir: str,
    ):
        self.collection      = collection
        self.system_prompt   = system_prompt
        self.policy_name     = policy_name
        self.top_k           = top_k
        self.sem_weight      = sem_weight
        self.vectorstore_dir = vectorstore_dir
        self._chunks_cache   = os.path.join(vectorstore_dir, f'{collection}_chunks.json')

        self._ef     = None
        self._chroma = None
        self._bm25   = None
        self._chunks = None
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        if not os.path.exists(self._chunks_cache):
            raise RuntimeError(
                f"Chunks cache not found for '{self.collection}'.\n"
                f"Run the ingest script for this policy first."
            )
        with open(self._chunks_cache, encoding='utf-8') as f:
            self._chunks = json.load(f)

        self._ef     = embedding_functions.ONNXMiniLM_L6_V2()
        client       = chromadb.PersistentClient(path=self.vectorstore_dir)
        self._chroma = client.get_collection(self.collection, embedding_function=self._ef)

        tokenised  = [_tokenise(c['text']) for c in self._chunks]
        self._bm25 = BM25Okapi(tokenised)
        self._loaded = True

    def retrieve(self, query: str) -> list[dict]:
        self._load()

        count  = self._chroma.count()
        sem_k  = min(SEM_K, count)
        sem_result = self._chroma.query(
            query_texts=[query],
            n_results=sem_k,
            include=["documents", "metadatas", "distances"],
        )
        sem_docs  = sem_result["documents"][0]
        sem_dists = sem_result["distances"][0]

        sem_hits: dict[int, float] = {}
        for doc, dist in zip(sem_docs, sem_dists):
            for i, c in enumerate(self._chunks):
                if c["text"][:80] == doc[:80]:
                    sem_hits[i] = 1.0 - float(dist)  # cosine similarity 0-1
                    break

        tokens   = _tokenise(query)
        scores   = self._bm25.get_scores(tokens)
        bm25_top = sorted(
            ((i, s) for i, s in enumerate(scores) if s > 0),
            key=lambda x: -x[1],
        )[:BM25_K]
        bm25_hits = {i: s for i, s in bm25_top}

        # RRF rank-based fusion (robust default)
        sem_rk  = {idx: r + 1 for r, (idx, _) in
                   enumerate(sorted(sem_hits.items(), key=lambda x: -x[1]))}
        bm25_rk = {idx: r + 1 for r, (idx, _) in
                   enumerate(sorted(bm25_hits.items(), key=lambda x: -x[1]))}

        all_idx = set(sem_hits) | set(bm25_hits)
        rrf = {
            idx: self.sem_weight / (RRF_K + sem_rk.get(idx, RRF_K * 10))
               + 1.0 / (RRF_K + bm25_rk.get(idx, RRF_K * 10))
            for idx in all_idx
        }

        from core.cross_encoder_reranker import is_available, rerank_with_cross_encoder

        if is_available():
            # Cross-encoder path: expand candidate pool, then rerank with joint attention
            rerank_n   = max(self.top_k * 3, 20)
            candidates = [
                {
                    "text":        self._chunks[i]["text"],
                    "policy_name": self._chunks[i]["policy_name"],
                    "page":        self._chunks[i]["page"],
                    "filename":    self._chunks[i].get("filename", ""),
                    "score":       round(s, 5),
                }
                for i, s in sorted(rrf.items(), key=lambda x: -x[1])[:rerank_n]
            ]
            return rerank_with_cross_encoder(query, candidates, self.top_k)

        # Standard RRF fallback
        top = sorted(rrf.items(), key=lambda x: -x[1])[:self.top_k]
        return [
            {
                "text":        self._chunks[i]["text"],
                "policy_name": self._chunks[i]["policy_name"],
                "page":        self._chunks[i]["page"],
                "filename":    self._chunks[i].get("filename", ""),
                "score":       round(s, 5),
            }
            for i, s in top
        ]

    @staticmethod
    def _check_grounding(answer_text: str, chunks: list[dict]) -> Optional[str]:
        """
        Extract numeric claims from the answer and verify each appears in at
        least one retrieved chunk.  Returns a warning string if any number is
        ungrounded, else None.
        """
        numbers = re.findall(r'\b\d[\d,\.]*\b', answer_text)
        if not numbers:
            return None
        combined_context = " ".join(c["text"] for c in chunks)
        ungrounded = [n for n in numbers if n not in combined_context]
        if ungrounded:
            return (
                f"[ARVIN note: the figure(s) {', '.join(set(ungrounded))} "
                "could not be verified in the policy document. "
                "Please confirm with your Business HR.]"
            )
        return None

    def answer(self, query: str, chat_history: list[dict] = None) -> dict:
        chunks = self.retrieve(query)

        if not chunks:
            return {
                "text": (
                    f"This specific detail is not covered in the {self.policy_name}. "
                    "Please contact your Business HR."
                ),
                "sources": [],
                "policy":  self.policy_name,
            }

        context = "\n\n---\n\n".join(
            f"[Page {c['page']}]\n{c['text']}" for c in chunks
        )

        history_text = ""
        if chat_history:
            turns = [
                f"{t['role'].upper()}: {t['content']}"
                for t in chat_history[-4:]
            ]
            history_text = "CONVERSATION HISTORY:\n" + "\n".join(turns) + "\n\n"

        user_message = (
            f"{history_text}"
            f"POLICY CONTEXT:\n{context}\n\n"
            f"EMPLOYEE QUESTION:\n{query}"
        )

        response_text = ask(self.system_prompt, user_message)

        grounding_warning = self._check_grounding(response_text, chunks)
        if grounding_warning:
            response_text = response_text + "\n\n" + grounding_warning

        sources = []
        seen = set()
        for c in chunks:
            key = (c["policy_name"], c["page"])
            if key not in seen:
                seen.add(key)
                sources.append({
                    "policy":   c["policy_name"],
                    "page":     c["page"],
                    "filename": c.get("filename", ""),
                })

        return {
            "text":    response_text,
            "sources": sources,
            "policy":  self.policy_name,
        }
