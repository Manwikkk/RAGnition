"""
utils/vector_store.py
---------------------
FAISS-backed vector store with disk persistence.

Index type: IndexFlatL2 (exact nearest-neighbour with L2 distance).
Metadata (text + page + source + chunk_id) is stored in a parallel list
and saved alongside the index as a pickle file.
"""

import logging
import pickle
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from config import config

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Stores and retrieves chunk embeddings using FAISS.

    Attributes:
        index:    The underlying FAISS index.
        metadata: Parallel list of chunk metadata dicts.
    """

    def __init__(
        self,
        dimension: int | None = None,
        index_path: str | Path | None = None,
        metadata_path: str | Path | None = None,
    ) -> None:
        """
        Args:
            dimension:     Embedding dimension.  Uses config value when None.
            index_path:    Path to save/load FAISS index.
            metadata_path: Path to save/load metadata pickle.
        """
        self.dimension = dimension or config.EMBEDDING_DIMENSION
        self.index_path = Path(index_path or config.FAISS_INDEX_PATH)
        self.metadata_path = Path(metadata_path or config.METADATA_PATH)

        self.index: faiss.Index = faiss.IndexFlatL2(self.dimension)
        self.metadata: list[dict[str, Any]] = []

    # ──────────────────────────────────────────────────────────────────────────
    # Indexing
    # ──────────────────────────────────────────────────────────────────────────

    def add(self, embeddings: np.ndarray, chunks: list[dict[str, Any]]) -> None:
        """
        Add embeddings and their corresponding chunk dicts to the store.

        Args:
            embeddings: Float32 array of shape (N, dimension).
            chunks:     List of N chunk dicts with text + metadata.
        """
        if embeddings.shape[0] != len(chunks):
            raise ValueError(
                f"Embeddings count ({embeddings.shape[0]}) != chunks count ({len(chunks)})"
            )
        embeddings = np.array(embeddings, dtype=np.float32)
        self.index.add(embeddings)
        self.metadata.extend(chunks)
        logger.info("Added %d vectors. Total: %d", len(chunks), self.index.ntotal)

    def clear(self) -> None:
        """Reset the index and metadata."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        logger.info("Vector store cleared.")

    # ──────────────────────────────────────────────────────────────────────────
    # Search
    # ──────────────────────────────────────────────────────────────────────────

    def search(
        self, query_embedding: np.ndarray, k: int
    ) -> list[dict[str, Any]]:
        """
        Return the top-k nearest chunks for a query embedding.

        Args:
            query_embedding: Float32 array of shape (1, dimension) or (dimension,).
            k:               Number of results to return.

        Returns:
            List of result dicts: {text, page, source, chunk_id, score}
            where score is the L2 distance (lower = more similar).
        """
        if self.index.ntotal == 0:
            logger.warning("Vector store is empty — no results returned.")
            return []

        query_embedding = np.array(query_embedding, dtype=np.float32)
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)

        results: list[dict[str, Any]] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            result = dict(self.metadata[idx])
            result["score"] = float(dist)
            results.append(result)
        return results

    def get_all_embeddings(self) -> np.ndarray:
        """
        Reconstruct all stored embeddings from the FAISS index.

        Returns:
            Float32 array of shape (ntotal, dimension).
        """
        if self.index.ntotal == 0:
            return np.empty((0, self.dimension), dtype=np.float32)
        # IndexFlatL2 supports reconstruct_n
        embeddings = np.zeros((self.index.ntotal, self.dimension), dtype=np.float32)
        for i in range(self.index.ntotal):
            self.index.reconstruct(i, embeddings[i])
        return embeddings

    # ──────────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist FAISS index and metadata to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)
        logger.info(
            "Vector store saved — index: %s, metadata: %s",
            self.index_path,
            self.metadata_path,
        )

    def load(self) -> bool:
        """
        Load FAISS index and metadata from disk.

        Returns:
            True if loaded successfully, False if files don't exist.
        """
        if not self.index_path.exists() or not self.metadata_path.exists():
            logger.info("No saved vector store found at %s", self.index_path)
            return False
        self.index = faiss.read_index(str(self.index_path))
        with open(self.metadata_path, "rb") as f:
            self.metadata = pickle.load(f)
        logger.info(
            "Vector store loaded — %d vectors from %s",
            self.index.ntotal,
            self.index_path,
        )
        return True

    # ──────────────────────────────────────────────────────────────────────────
    # Properties
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def total_vectors(self) -> int:
        """Number of vectors currently stored."""
        return self.index.ntotal
