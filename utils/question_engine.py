"""
utils/question_engine.py
------------------------
LLM-powered question generation using Groq API.

MCQ format (STRICT):
  - Exactly 4 options with keys A, B, C, D (dict, not list)
  - "correct_answer" field holds ONLY the single letter: "A" | "B" | "C" | "D"
  - Post-generation validation rejects any response that violates this

Other types: Short | Long | True/False | Case-based
"""

import json
import logging
import re
from typing import Any, Literal

from utils.groq_llm import generate_response
from config import config

logger = logging.getLogger(__name__)

QuestionType = Literal["MCQ", "Short", "Long", "True/False", "Case-based"]
Difficulty   = Literal["Easy", "Medium", "Hard"]

_VALID_LETTERS = {"A", "B", "C", "D"}

# Answer depth guidance per question type
_ANSWER_DEPTH: dict[str, str] = {
    "MCQ":        'State ONLY the single correct option letter, e.g. "A".',
    "True/False": "State True or False, then one sentence explaining why.",
    "Short":      "Write a clear, concise answer of 3-5 sentences.",
    "Long": (
        "Write a comprehensive, academically structured answer of at least 150 words. "
        "Include: a definition or introduction, key concepts with explanations, examples "
        "where relevant, and a concluding sentence. Do NOT give a one-line answer."
    ),
    "Case-based": (
        "Write a detailed analytical answer of at least 150 words. "
        "Apply the concepts from the context to the case scenario. "
        "Include: analysis, reasoning, relevant theory, and a justified conclusion. "
        "Do NOT give a one-sentence answer."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Prompt builders
# ─────────────────────────────────────────────────────────────────────────────

_MCQ_PROMPT = """\
You are an expert exam question creator. Return ONLY a valid JSON array — no markdown, no explanation.

Task: Generate exactly {n} MCQ question(s) at {difficulty} difficulty level.

Context (use ONLY this information):
{context}

STRICT MCQ RULES (violating any rule = invalid response):
1. Each question MUST have EXACTLY 4 options with keys A, B, C, D.
2. ONLY ONE option is correct — never two or more.
3. The 3 wrong options must be plausible but clearly incorrect.
4. "correct_answer" MUST be a SINGLE letter: "A", "B", "C", or "D" — nothing else.
5. Do NOT write "A. text" inside the option value — just the text itself.
6. Do NOT reveal the answer inside the option text.

Output — return ONLY a JSON array:
[
  {{
    "question":       "<the exam question>",
    "options":        {{"A": "<option A>", "B": "<option B>", "C": "<option C>", "D": "<option D>"}},
    "correct_answer": "A",
    "explanation":    "<why the correct answer is right and why the others are wrong — minimum 2 sentences>"
  }}
]

Output must start with [ and end with ]. No extra text.
"""

_OTHER_PROMPT = """\
You are an expert exam question creator. Return ONLY a valid JSON array — no markdown, no explanation.

Task: Generate exactly {n} "{q_type}" question(s) at {difficulty} difficulty.

Context (use ONLY this information):
{context}

CRITICAL ANSWER REQUIREMENT for "{q_type}" questions:
{answer_depth}

Output — return ONLY a JSON array:
[
  {{
    "question":    "<the exam question>",
    "options":     {options_note},
    "answer":      "<answer following the depth requirement above>",
    "explanation": "<thorough explanation referencing specific parts of the context — minimum 2 sentences>",
    "difficulty":  "{difficulty}"
  }}
]

Rules:
- For True/False: options must be ["True", "False"].
- For Short/Long/Case-based: options must be null.
- The "answer" field for Long and Case-based MUST be at least 150 words.
- Do NOT add any text outside the JSON array.
"""


# ─────────────────────────────────────────────────────────────────────────────
# QuestionEngine
# ─────────────────────────────────────────────────────────────────────────────

class QuestionEngine:
    """Generates exam questions from retrieved context using Groq API."""

    MAX_RETRIES = 2  # how many times to retry on validation failure

    def __init__(self) -> None:
        logger.info(
            "QuestionEngine ready — model: %s (fallback: %s)",
            config.GROQ_PRIMARY_MODEL,
            config.GROQ_FALLBACK_MODEL,
        )

    def generate(
        self,
        context: str,
        question_type: QuestionType = "MCQ",
        difficulty: Difficulty = "Medium",
        num_questions: int = 1,
    ) -> list[dict[str, Any]]:
        num_questions = max(1, min(num_questions, 10))

        for attempt in range(1, self.MAX_RETRIES + 2):
            prompt = self._build_prompt(context, question_type, difficulty, num_questions)
            try:
                raw_text  = generate_response(prompt, model=config.GROQ_PRIMARY_MODEL)
                questions = self._parse_response(raw_text, question_type)
                valid     = self._validate(questions, question_type)

                if valid or attempt > self.MAX_RETRIES:
                    return valid[:num_questions] if valid else questions[:num_questions]

                logger.warning(
                    "Attempt %d/%d: %d/%d questions passed MCQ validation — retrying.",
                    attempt, self.MAX_RETRIES, len(valid), len(questions)
                )
            except Exception as exc:
                if attempt > self.MAX_RETRIES:
                    raise
                logger.warning("Attempt %d failed (%s) — retrying.", attempt, exc)

        return []

    # ── Prompt building ────────────────────────────────────────────────────────

    def _build_prompt(
        self,
        context: str,
        question_type: QuestionType,
        difficulty: Difficulty,
        num_questions: int,
    ) -> str:
        if question_type == "MCQ":
            return _MCQ_PROMPT.format(
                n=num_questions, difficulty=difficulty, context=context
            )

        options_note = (
            '["True", "False"]' if question_type == "True/False" else "null"
        )
        return _OTHER_PROMPT.format(
            n=num_questions,
            q_type=question_type,
            difficulty=difficulty,
            context=context,
            answer_depth=_ANSWER_DEPTH.get(question_type, "Provide a clear, complete answer."),
            options_note=options_note,
        )

    # ── Parsing ───────────────────────────────────────────────────────────────

    def _parse_response(self, raw_text: str, question_type: str) -> list[dict[str, Any]]:
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_text).strip().rstrip("```").strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                logger.error("Could not parse JSON:\n%s", raw_text[:500])
                raise ValueError("LLM returned non-JSON content.")

        if isinstance(parsed, dict):
            parsed = [parsed]

        validated = []
        for item in parsed:
            try:
                if question_type == "MCQ":
                    # Normalise: accept both dict and list options
                    raw_opts      = item.get("options") or {}
                    correct_raw   = str(item.get("correct_answer") or item.get("answer", "")).strip().upper()
                    correct_letter = correct_raw[0] if correct_raw else ""

                    # If options came back as a list ["A. ...", "B. ..."] → convert to dict
                    if isinstance(raw_opts, list):
                        opt_dict = {}
                        for opt in raw_opts:
                            text = str(opt).strip()
                            if len(text) >= 2 and text[0].upper() in _VALID_LETTERS and text[1] in (".", ":"):
                                opt_dict[text[0].upper()] = text[2:].strip()
                            else:
                                # Best effort: assign sequentially
                                next_key = ["A","B","C","D"][len(opt_dict)] if len(opt_dict) < 4 else None
                                if next_key:
                                    opt_dict[next_key] = text
                        raw_opts = opt_dict

                    validated.append({
                        "question":       str(item.get("question", "")),
                        "options":        raw_opts,          # dict {A:, B:, C:, D:}
                        "correct_answer": correct_letter,
                        "explanation":    str(item.get("explanation", "")),
                        "difficulty":     difficulty if (difficulty := item.get("difficulty", "")) else "",
                    })
                else:
                    validated.append({
                        "question":    str(item.get("question", "")),
                        "options":     item.get("options"),   # list or None
                        "answer":      str(item.get("answer", "")),
                        "explanation": str(item.get("explanation", "")),
                        "difficulty":  str(item.get("difficulty", "")),
                    })
            except (KeyError, TypeError, IndexError) as exc:
                logger.warning("Skipping malformed question: %s", exc)

        return validated

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate(self, questions: list[dict], question_type: str) -> list[dict]:
        """For MCQ: keep only questions with valid correct_answer and 4 options."""
        if question_type != "MCQ":
            return questions  # other types don't need strict letter validation

        valid = []
        for q in questions:
            opts   = q.get("options") or {}
            letter = q.get("correct_answer", "").strip().upper()

            if (
                isinstance(opts, dict)
                and set(opts.keys()) >= {"A", "B", "C", "D"}
                and letter in _VALID_LETTERS
            ):
                valid.append(q)
            else:
                logger.warning(
                    "MCQ validation failed — correct_answer='%s', opts_keys=%s",
                    letter, list(opts.keys()) if isinstance(opts, dict) else type(opts).__name__
                )
        return valid
