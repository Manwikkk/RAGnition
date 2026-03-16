"""
utils/mock_test_generator.py
-----------------------------
Generates structured mock exam papers using the QuestionEngine.

Input:  total marks, section distribution (question type → marks per question),
        context from the vector store.
Output: A fully structured exam dict + formatted text for display/export.
"""

import logging
import math
from typing import Any

from utils.question_engine import QuestionEngine, Difficulty

logger = logging.getLogger(__name__)


# Default mark allocation per question type
DEFAULT_MARKS_PER_TYPE: dict[str, int] = {
    "MCQ":        1,
    "True/False": 1,
    "Short":      3,
    "Long":       5,
    "Case-based": 10,
}


class MockTestGenerator:
    """
    Assembles a complete exam paper by orchestrating the QuestionEngine.

    Example distribution (for a 30-mark paper):
        {
          "MCQ":   {"count": 10, "marks_each": 1},
          "Short": {"count": 4,  "marks_each": 3},
          "Long":  {"count": 1,  "marks_each": 8},
        }
    """

    def __init__(self, question_engine: QuestionEngine) -> None:
        """
        Args:
            question_engine: Initialised QuestionEngine.
        """
        self.engine = question_engine

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def generate(
        self,
        context: str,
        total_marks: int = 50,
        distribution: dict[str, dict[str, int]] | None = None,
        difficulty: Difficulty = "Medium",
        title: str = "Mock Examination Paper",
    ) -> dict[str, Any]:
        """
        Generate a complete exam paper.

        Args:
            context:      Retrieved context string (joined chunks).
            total_marks:  Target total marks for the paper.
            distribution: Override question distribution.
                          Keys are question types; values are dicts with
                          ``count`` and ``marks_each``.
            difficulty:   Default difficulty for all sections.
            title:        Exam paper title.

        Returns:
            Exam dict::

                {
                  "title":        str,
                  "total_marks":  int,
                  "sections": [
                    {
                      "type":         str,
                      "marks_each":   int,
                      "total_marks":  int,
                      "questions":    [question_dict, ...]
                    },
                    ...
                  ]
                }
        """
        if distribution is None:
            distribution = self._auto_distribute(total_marks)

        sections: list[dict[str, Any]] = []
        actual_total = 0

        for q_type, spec in distribution.items():
            count = spec.get("count", 1)
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

            section_total = marks_each * len(questions)
            actual_total += section_total

            sections.append(
                {
                    "type": q_type,
                    "marks_each": marks_each,
                    "total_marks": section_total,
                    "questions": questions,
                }
            )

        exam: dict[str, Any] = {
            "title": title,
            "total_marks": actual_total,
            "sections": sections,
        }
        logger.info("Mock test generated — %d total marks.", actual_total)
        return exam

    def format_as_text(self, exam: dict[str, Any]) -> str:
        """
        Convert an exam dict into a human-readable formatted string.

        Args:
            exam: Output of ``generate()``.

        Returns:
            Nicely formatted exam paper as a plain-text string.
        """
        lines: list[str] = []
        sep = "=" * 70

        lines.append(sep)
        lines.append(exam["title"].center(70))
        lines.append(f"Total Marks: {exam['total_marks']}".center(70))
        lines.append(sep)
        lines.append("")

        section_letter = "A"
        for section in exam["sections"]:
            q_type = section["type"]
            marks_each = section["marks_each"]
            sec_total = section["total_marks"]

            lines.append(
                f"SECTION {section_letter} — {q_type.upper()} "
                f"[{marks_each} mark(s) each | Section total: {sec_total}]"
            )
            lines.append("-" * 70)

            for i, q in enumerate(section["questions"], start=1):
                lines.append(f"Q{i}. {q.get('question', '')}")
                options = q.get("options")
                if options:
                    for opt in options:
                        lines.append(f"      {opt}")
                lines.append("")

            lines.append("")
            section_letter = chr(ord(section_letter) + 1)

        return "\n".join(lines)

    def format_answer_key(self, exam: dict[str, Any]) -> str:
        """
        Return a formatted answer key for the exam.

        Args:
            exam: Output of ``generate()``.

        Returns:
            Answer key as a plain-text string.
        """
        lines: list[str] = ["ANSWER KEY", "=" * 70, ""]
        section_letter = "A"

        for section in exam["sections"]:
            lines.append(f"SECTION {section_letter} — {section['type']}")
            for i, q in enumerate(section["questions"], start=1):
                lines.append(f"Q{i}. Answer: {q.get('answer', 'N/A')}")
                exp = q.get("explanation", "")
                if exp:
                    lines.append(f"    Explanation: {exp}")
                lines.append("")
            section_letter = chr(ord(section_letter) + 1)

        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _auto_distribute(total_marks: int) -> dict[str, dict[str, int]]:
        """
        Create a sensible default distribution for a given total marks.

        Allocation:
          - 40% MCQ  (1 mark each)
          - 30% Short (3 marks each)
          - 20% Long  (5 marks each)
          - 10% Case  (10 marks each)
        """
        mcq_count   = max(1, math.floor(total_marks * 0.40 / 1))
        short_count = max(1, math.floor(total_marks * 0.30 / 3))
        long_count  = max(1, math.floor(total_marks * 0.20 / 5))
        case_count  = max(1, math.floor(total_marks * 0.10 / 10))

        return {
            "MCQ":   {"count": mcq_count,   "marks_each": 1},
            "Short": {"count": short_count, "marks_each": 3},
            "Long":  {"count": long_count,  "marks_each": 5},
            "Case-based": {"count": case_count, "marks_each": 10},
        }
