"""
utils/embedder.py
-----------------
Instruction-based embedder using BAAI/bge-base-en-v1.5.

BGE models require two instruction prefixes:
  - Documents: "Represent this document for retrieval: <text>"
  - Queries:   "Represent this question for searching relevant documents: <query>"

Produces L2-normalised float32 numpy arrays suitable for FAISS IndexFlatL2.
"""

import logging
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from config import config

logger = logging.getLogger(__name__)

# Instruction prefixes for BGE models
_DOC_PREFIX   = "Represent this document for retrieval: "
_QUERY_PREFIX = "Represent this question for searching relevant documents: "


class Embedder:
    """Wraps BAAI/bge-base-en-v1.5 for instruction-based batch embedding."""

    def __init__(
        self,
        model_name: str | None = None,
        cache_dir: str | Path | None = None,
        batch_size: int | None = None,
    ) -> None:
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.cache_dir  = str(cache_dir or config.MODELS_DIR)
        self.batch_size = batch_size or config.EMBEDDING_BATCH_SIZE

        logger.info("Loading embedding model '%s' …", self.model_name)
        self._model = SentenceTransformer(
            self.model_name,
            cache_folder=self.cache_dir,
        )
        logger.info("Embedding model loaded. Dimension: %d", self.dimension)

    # ── Properties ─────────────────────────────────────────────────────────────

    @property
    def dimension(self) -> int:
        return int(self._model.get_sentence_embedding_dimension())

    # ── Private helpers ────────────────────────────────────────────────────────

    def _encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)
        embeddings = self._model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=len(texts) > 32,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32)

    # ── Public API ─────────────────────────────────────────────────────────────

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Embed raw texts without any prefix (use embed_chunks / embed_query instead)."""
        return self._encode(texts)

    def embed_chunks(self, chunks: list[dict[str, Any]]) -> np.ndarray:
        """
        Embed chunk dicts using the BGE document instruction prefix.

        Args:
            chunks: List of dicts with at least a 'text' key.

        Returns:
            Float32 array of shape (N, dimension).
        """
        texts = [_DOC_PREFIX + c["text"] for c in chunks]
        return self._encode(texts)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a search query using the BGE query instruction prefix.

        Args:
            query: The user query string.

        Returns:
            Float32 array of shape (1, dimension).
        """
        return self._encode([_QUERY_PREFIX + query])
