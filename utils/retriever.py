"""
utils/retriever.py
------------------
Hybrid Retriever: FAISS vector search + BM25 keyword search.

Combination formula:
    final_score = 0.7 * vector_similarity + 0.3 * bm25_norm

where vector_similarity is converted from L2 distance (closer = higher score)
and bm25_norm is the BM25 score normalised to [0, 1].
"""

import logging
from typing import Any

import numpy as np

from config import config
from utils.embedder import Embedder
from utils.vector_store import VectorStore

logger = logging.getLogger(__name__)


def _normalise(arr: np.ndarray) -> np.ndarray:
    """Min-max normalise an array to [0, 1]. Handles zero-range edge case."""
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-9:
        return np.ones_like(arr)
    return (arr - mn) / (mx - mn)


class Retriever:
    """
    Hybrid retriever combining FAISS dense search and BM25 sparse search.

    Usage:
        retriever = Retriever(vector_store, embedder)
        results   = retriever.retrieve_top_k(query, k=3)
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: Embedder,
        top_k: int | None = None,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
    ) -> None:
        self.vector_store   = vector_store
        self.embedder       = embedder
        self.top_k          = top_k or config.TOP_K
        self.vector_weight  = vector_weight
        self.bm25_weight    = bm25_weight

    # ── Internal: BM25 ─────────────────────────────────────────────────────────

    def _bm25_scores(self, query: str, docs: list[dict[str, Any]]) -> np.ndarray:
        """Compute BM25 scores for *all* stored chunks, lazily importing rank_bm25."""
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            logger.warning("rank-bm25 not installed — using vector-only retrieval.")
            return np.ones(len(docs), dtype=np.float32)

        tokenized_corpus = [d["text"].lower().split() for d in docs]
        tokenized_query  = query.lower().split()
        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)
        return np.array(scores, dtype=np.float32)

    # ── Public API ─────────────────────────────────────────────────────────────

    def retrieve_top_k(
        self, query: str, k: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Return the top-k most relevant chunks using hybrid FAISS + BM25 scoring.

        Args:
            query: Natural-language search query.
            k:     Number of results to return (default: self.top_k).

        Returns:
            List of chunk dicts with 'score' set to the hybrid similarity score.
        """
        k   = k or self.top_k
        all_docs = self.vector_store.metadata
        n   = len(all_docs)

        if n == 0:
            return []

        # ── Step 1: Dense vector retrieval ────────────────────────────────────
        # Retrieve more candidates than k so BM25 can re-rank them
        candidate_k = min(n, max(k * 5, 20))
        query_emb   = self.embedder.embed_query(query)
        vector_hits = self.vector_store.search(query_emb, k=candidate_k)

        if not vector_hits:
            return []

        # Map chunk_id → FAISS L2 distance
        hit_ids     = [h.get("chunk_id", i) for i, h in enumerate(vector_hits)]
        l2_dists    = np.array([h["score"] for h in vector_hits], dtype=np.float32)

        # Convert L2 distance to similarity: lower L2 = higher similarity
        # similarity = 1 / (1 + distance)
        vector_sims = 1.0 / (1.0 + l2_dists)
        vector_norm = _normalise(vector_sims)

        # ── Step 2: BM25 over *only* the candidate chunks ─────────────────────
        candidate_docs = [self.vector_store.metadata[cid]
                          if cid < n else vector_hits[i]
                          for i, cid in enumerate(hit_ids)]
        bm25_raw  = self._bm25_scores(query, candidate_docs)
        bm25_norm = _normalise(bm25_raw)

        # ── Step 3: Combine scores ─────────────────────────────────────────────
        hybrid = self.vector_weight * vector_norm + self.bm25_weight * bm25_norm

        # Sort descending by hybrid score and return top-k
        ranked_idx = np.argsort(-hybrid)[:k]

        results = []
        for idx in ranked_idx:
            chunk = dict(vector_hits[idx])
            chunk["score"]        = float(hybrid[idx])
            chunk["vector_score"] = float(vector_norm[idx])
            chunk["bm25_score"]   = float(bm25_norm[idx])
            results.append(chunk)

        logger.debug(
            "Hybrid retrieval: top-%d chunks from %d candidates for '%s…'",
            len(results), candidate_k, query[:50]
        )
        return results
