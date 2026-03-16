"""
utils/retriever.py
------------------
Retrieves semantically relevant chunks from the VectorStore using Top-K search.
"""

import logging
from typing import Any

from config import config
from utils.embedder import Embedder
from utils.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves chunks from a VectorStore using a query string (Top-K nearest neighbours).
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: Embedder,
        top_k: int | None = None,
    ) -> None:
        """
        Args:
            vector_store: Populated VectorStore instance.
            embedder:     Embedder used to encode the query.
            top_k:        Default number of results to return.
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.top_k = top_k or config.TOP_K

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def retrieve_top_k(
        self, query: str, k: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Return the k most semantically similar chunks.

        Args:
            query: The search query.
            k:     Override number of results (falls back to self.top_k).

        Returns:
            List of chunk dicts with an added 'score' key (L2 distance).
        """
        k = k or self.top_k
        query_emb = self.embedder.embed_query(query)
        results = self.vector_store.search(query_emb, k=k)
        logger.debug("Top-K=%d retrieved for query '%s…'", len(results), query[:50])
        return results
