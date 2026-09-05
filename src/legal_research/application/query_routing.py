"""Rule-first, bounded query routing before retrieval; no LLM planning in P5."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class QueryRoute(StrEnum):
    EXACT_REFERENCE = "exact_reference"
    SEMANTIC_QUESTION = "semantic_question"
    MULTI_PART_QUESTION = "multi_part_question"


@dataclass(frozen=True, slots=True)
class QueryPlan:
    route: QueryRoute
    queries: tuple[str, ...]


class RuleFirstQueryRouter:
    """Recognise supported dotted source sections and bounded English multi-part questions."""

    _SECTION = re.compile(r"^(?:section\s+)?\d+(?:\.\d+){0,3}$", re.IGNORECASE)

    def route(self, question: str) -> QueryPlan:
        normalized = question.strip()
        if not normalized:
            raise ValueError("question must not be empty")
        if self._SECTION.fullmatch(normalized):
            return QueryPlan(QueryRoute.EXACT_REFERENCE, (normalized,))
        parts = tuple(
            part.strip(" ?")
            for part in re.split(r"\?\s+|\s+and\s+", normalized)
            if part.strip(" ?")
        )
        if len(parts) in {2, 3} and all(len(part.split()) >= 3 for part in parts):
            return QueryPlan(QueryRoute.MULTI_PART_QUESTION, parts)
        return QueryPlan(QueryRoute.SEMANTIC_QUESTION, (normalized,))
