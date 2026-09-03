"""Deterministic contract tests for the BGE-M3 embedding adapter."""

import math
from collections.abc import Sequence

import pytest

from legal_research.adapters.embedding.bge_m3 import BgeM3EmbeddingProvider
from legal_research.config import EmbeddingModelConfig
from legal_research.ports.embedding import (
    EmbeddingError,
    EmbeddingFailureKind,
    EmbeddingRequest,
)


class FakeModel:
    def __init__(self, vectors: object) -> None:
        self.vectors = vectors
        self.encode_calls = 0
        self.max_seq_length = 0

    def encode(
        self,
        sentences: Sequence[str],
        *,
        batch_size: int,
        normalize_embeddings: bool,
        show_progress_bar: bool,
    ) -> object:
        del sentences, batch_size, normalize_embeddings, show_progress_bar
        self.encode_calls += 1
        return self.vectors


class FakeLoader:
    def __init__(self, model: FakeModel | Exception) -> None:
        self.model = model
        self.load_calls = 0

    def load(self, config: EmbeddingModelConfig) -> FakeModel:
        del config
        self.load_calls += 1
        if isinstance(self.model, Exception):
            raise self.model
        return self.model


def _config() -> EmbeddingModelConfig:
    return EmbeddingModelConfig(expected_dimension=3, device="cpu")


async def test_provider_returns_validated_vectors_and_caches_loaded_model() -> None:
    model = FakeModel([[3.0, 4.0, 0.0]])
    loader = FakeLoader(model)
    provider = BgeM3EmbeddingProvider(_config(), loader)

    response = await provider.embed(EmbeddingRequest(texts=("first",)))
    await provider.embed(EmbeddingRequest(texts=("second",)))

    assert response.vectors == ((0.6, 0.8, 0.0),)
    assert response.dimension == 3
    assert loader.load_calls == 1
    assert model.encode_calls == 2
    assert model.max_seq_length == _config().max_sequence_length


@pytest.mark.parametrize(
    "vectors",
    [
        [[0.1, 0.2]],
        [[0.1, 0.2, math.nan]],
        [[0.1, 0.2, math.inf]],
        [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        [[0.0, 0.0, 0.0]],
    ],
)
async def test_provider_rejects_invalid_vectors(vectors: object) -> None:
    provider = BgeM3EmbeddingProvider(_config(), FakeLoader(FakeModel(vectors)))

    with pytest.raises(EmbeddingError) as error:
        await provider.embed(EmbeddingRequest(texts=("input",)))

    assert error.value.kind is EmbeddingFailureKind.INVALID_OUTPUT


async def test_provider_preserves_loader_failure_category() -> None:
    provider = BgeM3EmbeddingProvider(
        _config(), FakeLoader(EmbeddingError(EmbeddingFailureKind.UNAVAILABLE))
    )

    with pytest.raises(EmbeddingError) as error:
        await provider.embed(EmbeddingRequest(texts=("input",)))

    assert error.value.kind is EmbeddingFailureKind.UNAVAILABLE


def test_request_rejects_blank_batches() -> None:
    with pytest.raises(ValueError, match="non-blank"):
        EmbeddingRequest(texts=(" ",))
