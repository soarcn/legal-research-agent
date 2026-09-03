"""BGE reranker adapter isolated from optional Transformers dependencies."""

import asyncio
import math
import threading
from collections.abc import Sequence
from importlib import import_module
from typing import Protocol, cast

from legal_research.config import RerankerModelConfig
from legal_research.ports.reranking import (
    RerankerError,
    RerankerFailureKind,
    RerankerProvider,
    RerankRequest,
    RerankResponse,
)


class CrossEncoderModel(Protocol):
    """The synchronous scoring surface required from a local cross-encoder."""

    def predict(self, sentences: Sequence[tuple[str, str]], *, batch_size: int) -> object:
        """Return one relevance score for each query-passage pair."""

        ...


class CrossEncoderLoader(Protocol):
    """Load a cross-encoder without exposing optional package imports to callers."""

    def load(self, config: RerankerModelConfig) -> CrossEncoderModel:
        """Load the pinned model using only the accepted local configuration."""

        ...


class DefaultCrossEncoderLoader:
    """Lazy sentence-transformers loader used only by the host adapter."""

    def load(self, config: RerankerModelConfig) -> CrossEncoderModel:
        try:
            sentence_transformers = import_module("sentence_transformers")
            cross_encoder = sentence_transformers.CrossEncoder
        except ImportError as error:
            raise RerankerError(RerankerFailureKind.UNAVAILABLE) from error
        try:
            return cast(
                CrossEncoderModel,
                cross_encoder(
                    config.model_id,
                    revision=config.revision,
                    max_length=config.max_sequence_length,
                    device=config.device,
                    trust_remote_code=False,
                    local_files_only=config.local_files_only,
                ),
            )
        except OSError as error:
            raise RerankerError(RerankerFailureKind.UNAVAILABLE) from error
        except Exception as error:
            raise RerankerError(RerankerFailureKind.LOAD_FAILURE) from error


class BgeM3RerankerProvider(RerankerProvider):
    """Cache and validate BGE cross-encoder scores for candidate reranking."""

    def __init__(
        self, config: RerankerModelConfig, loader: CrossEncoderLoader | None = None
    ) -> None:
        self._config = config
        self._loader = loader or DefaultCrossEncoderLoader()
        self._model: CrossEncoderModel | None = None
        self._load_lock = threading.Lock()

    async def rerank(self, request: RerankRequest) -> RerankResponse:
        """Load once off the event loop, then return finite scores in input order."""
        try:
            return await asyncio.to_thread(self._rerank_sync, request)
        except RerankerError:
            raise
        except TimeoutError as error:
            raise RerankerError(RerankerFailureKind.TIMEOUT) from error
        except Exception as error:
            raise RerankerError(RerankerFailureKind.TRANSPORT_ERROR) from error

    def _rerank_sync(self, request: RerankRequest) -> RerankResponse:
        raw_scores = self._get_model().predict(
            [(request.query, passage) for passage in request.passages],
            batch_size=self._config.batch_size,
        )
        scores = _validated_scores(raw_scores, expected_count=len(request.passages))
        return RerankResponse(
            scores=scores, model_id=self._config.model_id, revision=self._config.revision
        )

    def _get_model(self) -> CrossEncoderModel:
        with self._load_lock:
            if self._model is None:
                self._model = self._loader.load(self._config)
            return self._model


def _validated_scores(raw_scores: object, *, expected_count: int) -> tuple[float, ...]:
    """Return only one finite scalar relevance score for every candidate."""
    try:
        scores = tuple(float(value) for value in raw_scores)  # type: ignore[union-attr]
    except (TypeError, ValueError) as error:
        raise RerankerError(RerankerFailureKind.INVALID_OUTPUT) from error
    if len(scores) != expected_count or any(not math.isfinite(score) for score in scores):
        raise RerankerError(RerankerFailureKind.INVALID_OUTPUT)
    return scores
