"""
utils/embedder.py
-----------------
Local sentence-transformers embedder (all-MiniLM-L6-v2).

Produces L2-normalised float32 numpy arrays suitable for FAISS IndexFlatL2.
The model is downloaded on first use and cached locally by sentence-transformers.
"""

import logging
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from config import config

logger = logging.getLogger(__name__)


class Embedder:
    """Wraps a SentenceTransformer model for batch text embedding."""

    def __init__(
        self,
        model_name: str | None = None,
        cache_dir: str | Path | None = None,
        batch_size: int | None = None,
    ) -> None:
        """
        Args:
            model_name: HuggingFace model id (default: config.EMBEDDING_MODEL).
            cache_dir:  Optional local cache directory for the model.
            batch_size: Encoding batch size (default: config.EMBEDDING_BATCH_SIZE).
        """
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.cache_dir = str(cache_dir or config.MODELS_DIR)
        self.batch_size = batch_size or config.EMBEDDING_BATCH_SIZE

        logger.info("Loading embedding model '%s' …", self.model_name)
        self._model = SentenceTransformer(
            self.model_name,
            cache_folder=self.cache_dir,
        )
        logger.info("Embedding model loaded. Dimension: %d", self.dimension)

    # ──────────────────────────────────────────────────────────────────────────
    # Properties
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def dimension(self) -> int:
        """Output embedding dimension."""
        return int(self._model.get_sentence_embedding_dimension())

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """
        Embed a list of texts in batches.

        Args:
            texts: Raw text strings to embed.

        Returns:
            Float32 numpy array of shape (len(texts), dimension).
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        embeddings = self._model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=len(texts) > 64,
            normalize_embeddings=True,   # L2 normalise for cosine similarity
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32)

    def embed_chunks(self, chunks: list[dict[str, Any]]) -> np.ndarray:
        """
        Embed the 'text' field from a list of chunk dicts.

        Args:
            chunks: List of dicts with at least a 'text' key.

        Returns:
            Float32 numpy array of shape (len(chunks), dimension).
        """
        texts = [c["text"] for c in chunks]
        return self.embed_texts(texts)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single query string.

        Args:
            query: The search query.

        Returns:
            Float32 numpy array of shape (1, dimension).
        """
        return self.embed_texts([query])
