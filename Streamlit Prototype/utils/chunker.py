"""
utils/chunker.py
----------------
Recursive character-level text chunker with metadata propagation.

Uses LangChain's RecursiveCharacterTextSplitter as the splitting engine
(pure text-processing, no LLM calls required).
"""

import logging
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import config

logger = logging.getLogger(__name__)


class Chunker:
    """
    Splits page-level documents into overlapping text chunks.

    Chunk size and overlap are controlled by config.CHUNK_SIZE and
    config.CHUNK_OVERLAP (measured in characters, approximating tokens at
    ~4 chars/token for typical English text).
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        """
        Args:
            chunk_size:    Max characters per chunk (default: config.CHUNK_SIZE).
            chunk_overlap: Overlap between consecutive chunks (default: config.CHUNK_OVERLAP).
        """
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            # Natural split order: paragraphs → sentences → words → chars
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
            is_separator_regex=False,
        )
        logger.info(
            "Chunker initialised — size=%d, overlap=%d",
            self.chunk_size,
            self.chunk_overlap,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def chunk_documents(
        self, documents: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Split a list of page-level documents into chunks.

        Args:
            documents: Output of PDFLoader — list of {text, page, source}.

        Returns:
            List of chunk dicts: {text, page, source, chunk_id}
        """
        chunks: list[dict[str, Any]] = []
        chunk_id = 0

        for doc in documents:
            raw_text: str = doc.get("text", "").strip()
            if not raw_text:
                continue

            splits = self._splitter.split_text(raw_text)

            for split in splits:
                split = split.strip()
                if not split:
                    continue
                chunks.append(
                    {
                        "text": split,
                        "page": doc.get("page"),
                        "source": doc.get("source"),
                        "chunk_id": chunk_id,
                    }
                )
                chunk_id += 1

        logger.info(
            "Produced %d chunks from %d documents.", len(chunks), len(documents)
        )
        return chunks

    def chunk_text(self, text: str, metadata: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Convenience: chunk a raw string with optional metadata.

        Args:
            text:     Raw text to split.
            metadata: Optional dict merged into each chunk.

        Returns:
            List of chunk dicts.
        """
        metadata = metadata or {}
        splits = self._splitter.split_text(text)
        return [
            {"text": s.strip(), "chunk_id": i, **metadata}
            for i, s in enumerate(splits)
            if s.strip()
        ]
