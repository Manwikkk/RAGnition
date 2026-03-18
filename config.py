"""
config.py
---------
Central configuration for RAGnition.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """Application-wide configuration."""

    # ── Paths ────────────────────────────────────────────────────────────────
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).parent)
    DATA_DIR: Path = field(default_factory=lambda: Path(__file__).parent / "data" / "raw_pdfs")
    VECTOR_STORE_DIR: Path = field(default_factory=lambda: Path(__file__).parent / "vector_store")
    MODELS_DIR: Path = field(default_factory=lambda: Path(__file__).parent / "models")

    FAISS_INDEX_PATH: Path = field(
        default_factory=lambda: Path(__file__).parent / "vector_store" / "faiss.index"
    )
    METADATA_PATH: Path = field(
        default_factory=lambda: Path(__file__).parent / "vector_store" / "metadata.pkl"
    )

    # ── PDF / Chunking ───────────────────────────────────────────────────────
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 80

    # ── Embeddings ───────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_DIMENSION: int = 768

    # ── Retrieval ────────────────────────────────────────────────────────────
    TOP_K: int = 3

    # ── LLM (Groq — cloud inference) ─────────────────────────────────────────
    GROQ_PRIMARY_MODEL: str = "llama-3.1-8b-instant"
    GROQ_FALLBACK_MODEL: str = "llama-3.3-70b-versatile"


# Singleton instance used throughout the app
config = Config()
