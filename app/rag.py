from __future__ import annotations

import math
import os
import re
from collections import Counter

class TFIDFVectorStore:
    def __init__(self) -> None:
        self._documents: list[dict] = []
        self._idf_cache: dict[str, float] = {}
        self._idf_doc_count = 0

    def add_document(self, doc_id: str, chunks: list[str]) -> None:
        for chunk in chunks:
            if not chunk or not chunk.strip():
                continue
            tokens = self._tokenize(chunk)
            if not tokens:
                continue
            self._documents.append({
                "doc_id": doc_id,
                "chunk": chunk,
                "tokens": tokens,
                "tf": Counter(tokens),
            })
        self._idf_cache = {}
        self._idf_doc_count = 0

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self._documents:
            return []
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        if self._idf_doc_count != len(self._documents):
            self._rebuild_idf()
        query_tfidf = self._compute_tfidf(query_tokens)
        scored: list[tuple[float, int]] = []
        for idx, doc in enumerate(self._documents):
            score = self._cosine_similarity(query_tfidf, self._compute_tfidf(doc["tokens"]))
            if score > 0:
                scored.append((score, idx))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "chunk": self._documents[idx]["chunk"],
                "doc_id": self._documents[idx]["doc_id"],
                "score": round(score, 4),
            }
            for score, idx in scored[:top_k]
        ]

    @property
    def document_count(self) -> int:
        return len(self._documents)

    def _tokenize(self, text: str) -> list[str]:
        stop_words = {
            "the", "a", "an", "and", "or", "to", "of", "for", "in", "on",
            "with", "is", "are", "i", "we", "you", "it", "this", "that",
            "my", "our", "from", "as", "at", "by", "be", "can", "need",
            "please", "has", "have", "been", "was", "were", "do", "does",
            "did", "will", "would", "should", "could", "may", "might",
            "shall", "not", "no", "but", "if", "so", "than", "too",
            "very", "just", "about", "after", "before", "between", "into",
            "through", "during", "out", "off", "over", "under", "again",
            "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "each", "every", "both", "few", "more",
            "most", "other", "some", "such", "only", "own", "same", "up",
            "down",
        }
        return [
            token for token in re.findall(r"[a-z0-9]+", text.lower())
            if token not in stop_words and len(token) > 1
        ]

    def _rebuild_idf(self) -> None:
        count = len(self._documents)
        freq: Counter = Counter()
        for doc in self._documents:
            for token in set(doc["tokens"]):
                freq[token] += 1
        self._idf_cache = {
            token: math.log((count + 1) / (value + 1)) + 1
            for token, value in freq.items()
        }
        self._idf_doc_count = count

    def _compute_tfidf(self, tokens: list[str]) -> dict[str, float]:
        if not tokens:
            return {}
        total = len(tokens)
        return {
            token: (value / total) * self._idf_cache.get(token, 1.0)
            for token, value in Counter(tokens).items()
        }

    def _cosine_similarity(self, a: dict[str, float], b: dict[str, float]) -> float:
        keys = set(a) & set(b)
        if not keys:
            return 0.0
        dot = sum(a[key] * b[key] for key in keys)
        mag_a = math.sqrt(sum(value * value for value in a.values()))
        mag_b = math.sqrt(sum(value * value for value in b.values()))
        if not mag_a or not mag_b:
            return 0.0
        return dot / (mag_a * mag_b)

def vector_backend_status() -> dict:
    try:
        import chromadb  # type: ignore
    except Exception:
        return {
            "backend": "tfidf",
            "available": True,
            "persistent": False,
            "note": "ChromaDB is optional. Install requirements-advanced.txt to enable it.",
        }
    return {
        "backend": "chromadb",
        "available": True,
        "persistent": True,
        "directory": os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma"),
        "version": getattr(chromadb, "__version__", "installed"),
    }
