"""
utils/pdf_loader.py
-------------------
PDF text extraction using PyMuPDF (fitz).

Each document is returned as a list of page-level dicts with:
  - text:   raw page text
  - page:   1-based page number
  - source: filename of the PDF
"""

import logging
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFLoader:
    """Loads one or more PDF files and returns structured page-level documents."""

    def __init__(self, min_page_chars: int = 20) -> None:
        """
        Args:
            min_page_chars: Pages with fewer characters than this are skipped
                            (covers blank / image-only pages).
        """
        self.min_page_chars = min_page_chars

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def load(self, pdf_path: str | Path) -> list[dict[str, Any]]:
        """
        Extract text from a single PDF file.

        Args:
            pdf_path: Absolute or relative path to the PDF.

        Returns:
            List of page dicts: [{text, page, source}, ...]
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        documents: list[dict[str, Any]] = []
        source_name = pdf_path.name

        try:
            with fitz.open(str(pdf_path)) as doc:
                for idx, page in enumerate(doc, start=1):
                    text = page.get_text("text").strip()
                    if len(text) < self.min_page_chars:
                        logger.debug("Skipping page %d of '%s' (too short).", idx, source_name)
                        continue
                    documents.append(
                        {
                            "text": text,
                            "page": idx,
                            "source": source_name,
                        }
                    )
        except Exception as exc:
            logger.error("Failed to load '%s': %s", pdf_path, exc)
            raise

        logger.info("Loaded %d pages from '%s'.", len(documents), source_name)
        return documents

    def load_many(self, pdf_paths: list[str | Path]) -> list[dict[str, Any]]:
        """
        Load multiple PDFs.

        Args:
            pdf_paths: List of PDF file paths.

        Returns:
            Flat list of all page dicts across all PDFs.
        """
        all_docs: list[dict[str, Any]] = []
        for path in pdf_paths:
            try:
                all_docs.extend(self.load(path))
            except Exception as exc:
                logger.warning("Skipping '%s' due to error: %s", path, exc)
        logger.info("Total pages loaded: %d from %d files.", len(all_docs), len(pdf_paths))
        return all_docs

    def load_directory(self, directory: str | Path) -> list[dict[str, Any]]:
        """
        Load all PDFs from a directory.

        Args:
            directory: Directory path to scan for *.pdf files.

        Returns:
            Flat list of page dicts from all PDFs found.
        """
        directory = Path(directory)
        pdf_paths = sorted(directory.glob("*.pdf"))
        if not pdf_paths:
            logger.warning("No PDF files found in '%s'.", directory)
            return []
        return self.load_many(pdf_paths)
