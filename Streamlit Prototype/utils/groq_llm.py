"""
utils/groq_llm.py
-----------------
Groq API interface for RAGnition.

Loads GROQ_API_KEY from the project .env file automatically.
Primary model:  llama3-8b-8192
Fallback model: mixtral-8x7b-32768

Functions:
    generate_response(prompt, model)   — single-shot generation
    generate_streaming(prompt, model)  — streaming generation (yields tokens)
    get_system_status()                — returns dict with API key / model status
"""

import logging
import os
from pathlib import Path
from typing import Generator

# Auto-load .env from the project root so GROQ_API_KEY is always available
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # dotenv optional — falls back to system environment

logger = logging.getLogger(__name__)

PRIMARY_MODEL  = "llama-3.1-8b-instant"
FALLBACK_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an AI document assistant.

You help users work with their uploaded documents.

You can:
- answer questions
- summarize
- explain concepts
- extract information
- rewrite content
- generate exam questions
- create notes
- analyze sections

Rules:
1. Always use the provided document context when relevant.
2. Follow the user's instruction exactly.
3. Do not repeat the raw document text unless explicitly asked.
4. Provide clear, professional answers.
5. Do not show reasoning steps, prompt templates, or analysis.
6. If the user asks to summarize, provide a concise summary.
7. If the user asks questions, answer using the document context."""


def _get_client():
    """Create and return a Groq client using GROQ_API_KEY from environment."""
    from groq import Groq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY environment variable is not set.\n"
            "Set it with: set GROQ_API_KEY=your_api_key  (Windows)\n"
            "             export GROQ_API_KEY=your_api_key  (Mac/Linux)"
        )
    return Groq(api_key=api_key)


# ──────────────────────────────────────────────────────────────────────────────
# Core generation
# ──────────────────────────────────────────────────────────────────────────────

def generate_response(prompt: str, model: str = PRIMARY_MODEL) -> str:
    """
    Generate a single-shot response via Groq API.

    Args:
        prompt: User prompt (should include context + question).
        model:  Groq model tag (default: llama3-8b-8192).

    Returns:
        Generated text as a string.
    """
    client = _get_client()
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.3,
        )
        return completion.choices[0].message.content
    except Exception as primary_exc:
        logger.warning(
            "Primary model '%s' failed (%s). Trying fallback '%s' …",
            model, primary_exc, FALLBACK_MODEL,
        )
        if model != FALLBACK_MODEL:
            try:
                completion = client.chat.completions.create(
                    model=FALLBACK_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": prompt},
                    ],
                    temperature=0.3,
                )
                return completion.choices[0].message.content
            except Exception as fallback_exc:
                raise RuntimeError(
                    f"Both Groq models failed.\n"
                    f"  Primary  ({model}): {primary_exc}\n"
                    f"  Fallback ({FALLBACK_MODEL}): {fallback_exc}"
                ) from fallback_exc
        raise RuntimeError(f"Groq model '{model}' failed: {primary_exc}") from primary_exc


def generate_streaming(prompt: str, model: str = PRIMARY_MODEL) -> Generator[str, None, None]:
    """
    Stream a response via Groq API, yielding tokens as they arrive.

    Args:
        prompt: User prompt.
        model:  Groq model tag.

    Yields:
        Token strings as they stream from the API.
    """
    client = _get_client()

    def _stream(m: str) -> Generator[str, None, None]:
        completion = client.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.3,
            stream=True,
        )
        for chunk in completion:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    try:
        yield from _stream(model)
    except Exception as primary_exc:
        logger.warning(
            "Streaming with '%s' failed (%s). Trying fallback '%s' …",
            model, primary_exc, FALLBACK_MODEL,
        )
        if model != FALLBACK_MODEL:
            try:
                yield from _stream(FALLBACK_MODEL)
            except Exception as fallback_exc:
                raise RuntimeError(
                    f"Both Groq models failed during streaming.\n"
                    f"  Primary  ({model}): {primary_exc}\n"
                    f"  Fallback ({FALLBACK_MODEL}): {fallback_exc}"
                ) from fallback_exc
        else:
            raise RuntimeError(
                f"Groq streaming model '{model}' failed: {primary_exc}"
            ) from primary_exc


# ──────────────────────────────────────────────────────────────────────────────
# Status helpers
# ──────────────────────────────────────────────────────────────────────────────

def check_api_key_set() -> bool:
    """Return True if GROQ_API_KEY is present in the environment."""
    return bool(os.getenv("GROQ_API_KEY"))


def get_system_status() -> dict:
    """
    Return a status dict for display in the Streamlit sidebar.

    Keys:
        api_key_set     (bool)
        primary_model   (str)
        fallback_model  (str)
    """
    return {
        "api_key_set":    check_api_key_set(),
        "primary_model":  PRIMARY_MODEL,
        "fallback_model": FALLBACK_MODEL,
    }
