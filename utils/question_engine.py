"""
utils/question_engine.py
------------------------
LLM-powered question generation using Groq API.

Supports:
  - Question types:  MCQ | Short | Long | True/False | Case-based
  - Difficulty:      Easy | Medium | Hard

Long and Case-based questions always produce detailed, professional answers.
All outputs are strictly formatted JSON.
"""

import json
import logging
import re
from typing import Any, Literal

from utils.groq_llm import generate_response
from config import config

logger = logging.getLogger(__name__)

QuestionType = Literal["MCQ", "Short", "Long", "True/False", "Case-based"]
Difficulty = Literal["Easy", "Medium", "Hard"]

# Answer depth guidance per question type
_ANSWER_DEPTH: dict[str, str] = {
    "MCQ":        "State only the correct option letter and option text.",
    "True/False": "State True or False, then one sentence explaining why.",
    "Short":      "Write a clear, concise answer of 3-5 sentences.",
    "Long":       (
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


class QuestionEngine:
    """
    Generates exam questions from retrieved context using Groq API.
    """

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
        prompt = self._build_prompt(context, question_type, difficulty, num_questions)

        try:
            raw_text = generate_response(prompt, model=config.GROQ_PRIMARY_MODEL)
            questions = self._parse_response(raw_text, question_type)
            return questions[:num_questions]
        except Exception as exc:
            logger.error("Question generation failed: %s", exc)
            raise

    def _build_prompt(
        self,
        context: str,
        question_type: QuestionType,
        difficulty: Difficulty,
        num_questions: int,
    ) -> str:
        options_note = (
            '"options": ["A. ...", "B. ...", "C. ...", "D. ..."]'
            if question_type == "MCQ"
            else (
                '"options": ["True", "False"]'
                if question_type == "True/False"
                else '"options": null'
            )
        )
        answer_depth = _ANSWER_DEPTH.get(question_type, "Provide a clear, complete answer.")

        return f"""You are an expert exam question creator. Return ONLY a valid JSON array — no explanation, no markdown fences.

Task: Generate exactly {num_questions} exam question(s) of type "{question_type}" at {difficulty} difficulty.

Context (use ONLY this information):
{context}

CRITICAL ANSWER REQUIREMENT for "{question_type}" questions:
{answer_depth}

Output Format — return ONLY a valid JSON array:
[
  {{
    "question":    "<the exam question>",
    "options":     {options_note},
    "answer":      "<answer following the depth requirement above>",
    "explanation": "<thorough explanation referencing specific parts of the context, minimum 2 sentences>",
    "difficulty":  "{difficulty}"
  }}
]

Rules:
- For MCQ: provide exactly 4 options (A-D), only one correct.
- For True/False: options must be ["True", "False"].
- For Short/Long/Case-based: options must be null.
- The "answer" field for Long and Case-based MUST be at least 150 words. Never use one line.
- The "explanation" field must always have at least 2 sentences.
- Do NOT add any text outside the JSON array.
- Output must start with [ and end with ]
"""

    def _parse_response(self, raw_text: str, question_type: str) -> list[dict[str, Any]]:
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_text).strip().rstrip("```").strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                logger.error("Could not parse JSON from response:\n%s", raw_text[:500])
                raise ValueError("LLM returned non-JSON content.")

        if isinstance(parsed, dict):
            parsed = [parsed]

        validated = []
        for item in parsed:
            try:
                validated.append({
                    "question":    str(item.get("question", "")),
                    "options":     item.get("options"),
                    "answer":      str(item.get("answer", "")),
                    "explanation": str(item.get("explanation", "")),
                    "difficulty":  str(item.get("difficulty", "")),
                })
            except (KeyError, TypeError) as exc:
                logger.warning("Skipping malformed question: %s", exc)

        return validated
