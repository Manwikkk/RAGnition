"""
utils/mock_test_generator.py
-----------------------------
Generates structured mock exam papers using the QuestionEngine.
"""

import logging
import math
from typing import Any

from utils.question_engine import QuestionEngine, Difficulty

logger = logging.getLogger(__name__)

DEFAULT_MARKS_PER_TYPE: dict[str, int] = {
    "MCQ":        1,
    "True/False": 1,
    "Short":      3,
    "Long":       5,
    "Case-based": 10,
}


def _format_options(options: Any) -> list[str]:
    """
    Normalise options to a list of formatted strings like "A. Option text".
    Handles both dict {A: text, ...} and list ["A. text", ...].
    """
    if isinstance(options, dict):
        return [f"{k}. {v}" for k, v in sorted(options.items())]
    if isinstance(options, list):
        return [str(o) for o in options]
    return []


def _get_answer(q: dict) -> str:
    """Return the answer field, supporting both MCQ (correct_answer) and other (answer)."""
    return str(q.get("correct_answer") or q.get("answer") or "N/A")


class MockTestGenerator:
    """Assembles a complete exam paper by orchestrating the QuestionEngine."""

    def __init__(self, question_engine: QuestionEngine) -> None:
        self.engine = question_engine

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate(
        self,
        context: str,
        total_marks: int = 50,
        distribution: dict[str, dict[str, int]] | None = None,
        difficulty: Difficulty = "Medium",
        title: str = "Mock Examination Paper",
    ) -> dict[str, Any]:
        if distribution is None:
            distribution = self._auto_distribute(total_marks)

        sections: list[dict[str, Any]] = []
        actual_total = 0

        for q_type, spec in distribution.items():
            count      = spec.get("count", 1)
            marks_each = spec.get("marks_each", DEFAULT_MARKS_PER_TYPE.get(q_type, 1))

            logger.info("Generating %d %s question(s) …", count, q_type)
            try:
                questions = self.engine.generate(
                    context=context,
                    question_type=q_type,
                    difficulty=difficulty,
                    num_questions=count,
                )
            except Exception as exc:
                logger.error("Failed to generate %s questions: %s", q_type, exc)
                questions = []

            section_total  = marks_each * len(questions)
            actual_total  += section_total
            sections.append({
                "type":        q_type,
                "marks_each":  marks_each,
                "total_marks": section_total,
                "questions":   questions,
            })

        exam: dict[str, Any] = {
            "title":       title,
            "total_marks": actual_total,
            "sections":    sections,
        }
        logger.info("Mock test generated — %d total marks.", actual_total)
        return exam

    def format_as_text(self, exam: dict[str, Any]) -> str:
        """Convert an exam dict into a human-readable plain-text string."""
        lines: list[str] = []
        sep   = "=" * 70

        lines.extend([sep, exam["title"].center(70),
                       f"Total Marks: {exam['total_marks']}".center(70), sep, ""])

        section_letter = "A"
        for section in exam["sections"]:
            q_type     = section["type"]
            marks_each = section["marks_each"]
            sec_total  = section["total_marks"]

            lines.append(
                f"SECTION {section_letter} — {q_type.upper()} "
                f"[{marks_each} mark(s) each | Section total: {sec_total}]"
            )
            lines.append("-" * 70)

            for i, q in enumerate(section["questions"], start=1):
                lines.append(f"Q{i}. {q.get('question', '')}")
                for opt_line in _format_options(q.get("options")):
                    lines.append(f"      {opt_line}")
                lines.append("")

            lines.append("")
            section_letter = chr(ord(section_letter) + 1)

        return "\n".join(lines)

    def format_answer_key(self, exam: dict[str, Any]) -> str:
        """Return a formatted answer key for the exam."""
        lines         = ["ANSWER KEY", "=" * 70, ""]
        section_letter = "A"

        for section in exam["sections"]:
            lines.append(f"SECTION {section_letter} — {section['type']}")
            for i, q in enumerate(section["questions"], start=1):
                answer = _get_answer(q)
                lines.append(f"Q{i}. Answer: {answer}")
                exp = q.get("explanation", "")
                if exp:
                    lines.append(f"    Explanation: {exp}")
                lines.append("")
            section_letter = chr(ord(section_letter) + 1)

        return "\n".join(lines)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _auto_distribute(total_marks: int) -> dict[str, dict[str, int]]:
        mcq_count   = max(1, math.floor(total_marks * 0.40 / 1))
        short_count = max(1, math.floor(total_marks * 0.30 / 3))
        long_count  = max(1, math.floor(total_marks * 0.20 / 5))
        case_count  = max(1, math.floor(total_marks * 0.10 / 10))
        return {
            "MCQ":        {"count": mcq_count,   "marks_each": 1},
            "Short":      {"count": short_count, "marks_each": 3},
            "Long":       {"count": long_count,  "marks_each": 5},
            "Case-based": {"count": case_count,  "marks_each": 10},
        }
