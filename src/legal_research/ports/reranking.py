"""Provider-neutral contracts for bounded query-passage reranking."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class RerankerFailureKind(StrEnum):
    """Safe categories for failures at the cross-encoder boundary."""

    UNAVAILABLE = "unavailable"
    LOAD_FAILURE = "load_failure"
    TIMEOUT = "timeout"
    INVALID_OUTPUT = "invalid_output"
    TRANSPORT_ERROR = "transport_error"


class RerankerError(Exception):
    """A provider-neutral reranking failure without raw library details."""

    def __init__(self, kind: RerankerFailureKind) -> None:
        self.kind = kind
        super().__init__(kind.value)


@dataclass(frozen=True, slots=True)
class RerankRequest:
    """One non-empty query and at least one non-empty candidate passage."""

    query: str
    passages: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not self.query.strip()
            or not self.passages
            or any(not item.strip() for item in self.passages)
        ):
            raise ValueError("Rerank requests require a non-blank query and passages.")


@dataclass(frozen=True, slots=True)
class RerankResponse:
    """One finite relevance score per input passage in original order."""

    scores: tuple[float, ...]
    model_id: str
    revision: str


class RerankerProvider(Protocol):
    """A narrow asynchronous cross-encoder scoring boundary."""

    async def rerank(self, request: RerankRequest) -> RerankResponse:
        """Score all query-passage pairs with one configured reranker."""

        ...
