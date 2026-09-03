"""BGE-M3 dense embedding adapter isolated from sentence-transformers."""

import asyncio
import math
import threading
from collections.abc import Sequence
from importlib import import_module
from typing import Protocol, cast

from legal_research.config import EmbeddingModelConfig
from legal_research.ports.embedding import (
    EmbeddingError,
    EmbeddingFailureKind,
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResponse,
)


class SentenceTransformerModel(Protocol):
    """The small synchronous surface needed from sentence-transformers."""

    max_seq_length: int

    def encode(
        self,
        sentences: Sequence[str],
        *,
        batch_size: int,
        normalize_embeddings: bool,
        show_progress_bar: bool,
    ) -> object:
        """Return one dense vector per supplied sentence."""

        ...


class SentenceTransformerLoader(Protocol):
    """Loads a sentence-transformers model without leaking it into the port."""

    def load(self, config: EmbeddingModelConfig) -> SentenceTransformerModel:
        """Load the fixed configured model."""

        ...


class DefaultSentenceTransformerLoader:
    """Lazy sentence-transformers loader used only by the host adapter."""

    def load(self, config: EmbeddingModelConfig) -> SentenceTransformerModel:
        try:
            sentence_transformers = import_module("sentence_transformers")
            sentence_transformer = sentence_transformers.SentenceTransformer
        except ImportError as error:
            raise EmbeddingError(EmbeddingFailureKind.UNAVAILABLE) from error

        try:
            model = cast(
                SentenceTransformerModel,
                sentence_transformer(
                    config.model_id,
                    revision=config.revision,
                    device=config.device,
                    trust_remote_code=False,
                    local_files_only=config.local_files_only,
                ),
            )
            return model
        except OSError as error:
            raise EmbeddingError(EmbeddingFailureKind.UNAVAILABLE) from error
        except Exception as error:
            raise EmbeddingError(EmbeddingFailureKind.LOAD_FAILURE) from error


class BgeM3EmbeddingProvider(EmbeddingProvider):
    """Cache and validate BGE-M3 dense embeddings for the configured runtime."""

    def __init__(
        self,
        config: EmbeddingModelConfig,
        loader: SentenceTransformerLoader | None = None,
    ) -> None:
        self._config = config
        self._loader = loader or DefaultSentenceTransformerLoader()
        self._model: SentenceTransformerModel | None = None
        self._load_lock = threading.Lock()

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Load once off the event loop, then validate the entire batch."""
        try:
            return await asyncio.to_thread(self._embed_sync, request)
        except EmbeddingError:
            raise
        except TimeoutError as error:
            raise EmbeddingError(EmbeddingFailureKind.TIMEOUT) from error
        except Exception as error:
            raise EmbeddingError(EmbeddingFailureKind.TRANSPORT_ERROR) from error

    def _embed_sync(self, request: EmbeddingRequest) -> EmbeddingResponse:
        model = self._get_model()
        raw_vectors = model.encode(
            request.texts,
            batch_size=self._config.batch_size,
            normalize_embeddings=False,
            show_progress_bar=False,
        )
        vectors = _validated_vectors(
            raw_vectors,
            input_count=len(request.texts),
            expected_dimension=self._config.expected_dimension,
            normalize=self._config.normalize,
        )
        return EmbeddingResponse(
            vectors=vectors,
            model_id=self._config.model_id,
            revision=self._config.revision,
            dimension=self._config.expected_dimension,
        )

    def _get_model(self) -> SentenceTransformerModel:
        with self._load_lock:
            if self._model is None:
                self._model = self._loader.load(self._config)
                self._model.max_seq_length = self._config.max_sequence_length
            return self._model


def _validated_vectors(
    raw_vectors: object,
    *,
    input_count: int,
    expected_dimension: int,
    normalize: bool,
) -> tuple[tuple[float, ...], ...]:
    """Return only complete finite vectors with the configured index dimension."""
    try:
        rows = tuple(tuple(float(value) for value in row) for row in raw_vectors)  # type: ignore[union-attr]
    except (TypeError, ValueError) as error:
        raise EmbeddingError(EmbeddingFailureKind.INVALID_OUTPUT) from error

    if len(rows) != input_count:
        raise EmbeddingError(EmbeddingFailureKind.INVALID_OUTPUT)
    if any(len(row) != expected_dimension for row in rows):
        raise EmbeddingError(EmbeddingFailureKind.INVALID_OUTPUT)
    if any(not math.isfinite(value) for row in rows for value in row):
        raise EmbeddingError(EmbeddingFailureKind.INVALID_OUTPUT)
    if not normalize:
        return rows

    normalized_rows: list[tuple[float, ...]] = []
    for row in rows:
        norm = math.sqrt(sum(value * value for value in row))
        if norm == 0:
            raise EmbeddingError(EmbeddingFailureKind.INVALID_OUTPUT)
        normalized_rows.append(tuple(value / norm for value in row))
    return tuple(normalized_rows)
