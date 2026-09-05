"""Conservative deterministic extraction of a legal question from a fact pattern."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FocusedQuery:
    original: str
    retrieval_query: str
    applied: bool


class FactPatternQueryFocuser:
    """Use the final interrogative sentence only when it is clearly a long fact pattern."""

    _SENTENCE_BOUNDARY = re.compile(r"(?<=[.!])\s+")

    def focus(self, question: str) -> FocusedQuery:
        original = question.strip()
        if not original:
            raise ValueError("question must not be empty")
        sentences = tuple(
            part.strip() for part in self._SENTENCE_BOUNDARY.split(original) if part.strip()
        )
        questions = tuple(sentence for sentence in sentences if sentence.endswith("?"))
        final = questions[-1] if questions else ""
        if len(original.split()) >= 40 and len(questions) == 1 and len(final.split()) >= 4:
            return FocusedQuery(original, final, True)
        return FocusedQuery(original, original, False)
