"""
utils/local_llm.py
------------------
Local LLM interface using Ollama for RAGnition.

Primary model:  mistral
Fallback model: llama3.1:8b

Functions:
    generate_response(prompt, model)  — generate text from a local Ollama model
    generate_streaming(prompt, model) — generate with streaming (yields tokens)
    check_ollama_running()            — returns True if Ollama daemon is reachable
    check_model_installed(model)      — returns True if the given model is pulled
    get_system_status()               — returns a dict with ollama + model status
"""

import logging
import subprocess
from typing import Generator, Optional

logger = logging.getLogger(__name__)

PRIMARY_MODEL = "mistral"
FALLBACK_MODEL = "llama3.1:8b"


# ──────────────────────────────────────────────────────────────────────────────
# Core generation
# ──────────────────────────────────────────────────────────────────────────────

def generate_response(prompt: str, model: str = PRIMARY_MODEL) -> str:
    """
    Generate a response using a local Ollama model.

    Tries the requested model first; if that fails, falls back to FALLBACK_MODEL.
    If both fail, raises RuntimeError.

    Args:
        prompt: The full prompt string to send to the model.
        model:  Ollama model tag to use (default: mistral).

    Returns:
        Generated text as a string.
    """
    import ollama  # local import so the app won't crash if ollama isn't installed

    # Primary attempt
    try:
        response = ollama.generate(model=model, prompt=prompt)
        return response["response"]
    except Exception as primary_exc:
        logger.warning(
            "Primary model '%s' failed (%s). Trying fallback '%s' …",
            model,
            primary_exc,
            FALLBACK_MODEL,
        )

    # Fallback attempt (only if primary ≠ fallback)
    if model != FALLBACK_MODEL:
        try:
            response = ollama.generate(model=FALLBACK_MODEL, prompt=prompt)
            return response["response"]
        except Exception as fallback_exc:
            logger.error("Fallback model '%s' also failed: %s", FALLBACK_MODEL, fallback_exc)
            raise RuntimeError(
                f"Both models failed.\n"
                f"  Primary  ({model}): {primary_exc}\n"
                f"  Fallback ({FALLBACK_MODEL}): {fallback_exc}\n\n"
                f"Make sure Ollama is running and the model is pulled:\n"
                f"  ollama pull {PRIMARY_MODEL}"
            ) from fallback_exc
    else:
        raise RuntimeError(
            f"Model '{model}' failed and it is already the fallback.\n"
            f"Make sure Ollama is running and the model is pulled:\n"
            f"  ollama pull {PRIMARY_MODEL}"
        ) from primary_exc


def generate_streaming(prompt: str, model: str = PRIMARY_MODEL) -> Generator[str, None, None]:
    """
    Generate a streaming response using a local Ollama model.

    Yields tokens as they arrive. Falls back to FALLBACK_MODEL on error.

    Args:
        prompt: The full prompt string.
        model:  Ollama model tag (default: mistral).

    Yields:
        Token strings as they stream from the model.
    """
    import ollama

    def _stream_model(m: str) -> Generator[str, None, None]:
        stream = ollama.chat(
            model=m,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in stream:
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield token

    try:
        yield from _stream_model(model)
    except Exception as primary_exc:
        logger.warning(
            "Streaming with primary model '%s' failed (%s). Trying fallback '%s' …",
            model, primary_exc, FALLBACK_MODEL,
        )
        if model != FALLBACK_MODEL:
            try:
                yield from _stream_model(FALLBACK_MODEL)
            except Exception as fallback_exc:
                raise RuntimeError(
                    f"Both models failed during streaming.\n"
                    f"  Primary  ({model}): {primary_exc}\n"
                    f"  Fallback ({FALLBACK_MODEL}): {fallback_exc}"
                ) from fallback_exc
        else:
            raise RuntimeError(
                f"Streaming model '{model}' failed and is already the fallback."
            ) from primary_exc


# ──────────────────────────────────────────────────────────────────────────────
# Status helpers
# ──────────────────────────────────────────────────────────────────────────────

def check_ollama_running() -> bool:
    """Return True if the Ollama daemon is reachable."""
    try:
        import ollama
        ollama.list()  # lightweight health-check call
        return True
    except Exception:
        return False


def check_model_installed(model: str = PRIMARY_MODEL) -> bool:
    """
    Return True if *model* is available locally in Ollama.
    """
    try:
        import ollama
        models_response = ollama.list()
        available = []
        for m in models_response.models:
            name = getattr(m, 'model', None) or getattr(m, 'name', '')
            available.append(name)
        return any(model in name for name in available)
    except ImportError:
        pass
    except Exception:
        pass

    # Subprocess fallback
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return model in result.stdout
    except Exception:
        return False


def get_system_status() -> dict:
    """
    Return a status dict for display in the Streamlit sidebar.

    Keys:
        ollama_running   (bool)
        primary_model_ok (bool)
        primary_model    (str)
        fallback_model   (str)
    """
    running = check_ollama_running()
    model_ok = check_model_installed(PRIMARY_MODEL) if running else False
    return {
        "ollama_running": running,
        "primary_model_ok": model_ok,
        "primary_model": PRIMARY_MODEL,
        "fallback_model": FALLBACK_MODEL,
    }
