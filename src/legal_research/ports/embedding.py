"""Provider-neutral contracts for dense text embedding capability."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class EmbeddingFailureKind(StrEnum):
    """Safe categories for failures at the embedding boundary."""

    UNAVAILABLE = "unavailable"
    LOAD_FAILURE = "load_failure"
    TIMEOUT = "timeout"
    INVALID_OUTPUT = "invalid_output"
    TRANSPORT_ERROR = "transport_error"


class EmbeddingError(Exception):
    """A provider-neutral embedding failure that never carries raw SDK text."""

    def __init__(self, kind: EmbeddingFailureKind) -> None:
        self.kind = kind
        super().__init__(kind.value)


@dataclass(frozen=True, slots=True)
class EmbeddingRequest:
    """A non-empty batch of text inputs for one configured embedding model."""

    texts: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.texts or any(not text.strip() for text in self.texts):
            raise ValueError("Embedding requests require at least one non-blank text.")


@dataclass(frozen=True, slots=True)
class EmbeddingResponse:
    """Validated dense vectors and the fixed model identity that produced them."""

    vectors: tuple[tuple[float, ...], ...]
    model_id: str
    revision: str
    dimension: int


class EmbeddingProvider(Protocol):
    """A narrow asynchronous boundary for configured dense embeddings."""

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Embed one batch using the provider's fixed model configuration."""

        ...
