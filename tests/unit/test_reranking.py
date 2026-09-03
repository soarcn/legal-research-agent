"""Deterministic contract tests for the BGE cross-encoder adapter."""

import math
from collections.abc import Sequence

import pytest

from legal_research.adapters.reranking import BgeM3RerankerProvider
from legal_research.config import RerankerModelConfig
from legal_research.ports.reranking import RerankerError, RerankerFailureKind, RerankRequest


class FakeModel:
    def __init__(self, scores: object) -> None:
        self.scores = scores
        self.predict_calls = 0

    def predict(self, sentences: Sequence[tuple[str, str]], *, batch_size: int) -> object:
        del sentences, batch_size
        self.predict_calls += 1
        return self.scores


class FakeLoader:
    def __init__(self, model: FakeModel | Exception) -> None:
        self.model = model
        self.load_calls = 0

    def load(self, config: RerankerModelConfig) -> FakeModel:
        del config
        self.load_calls += 1
        if isinstance(self.model, Exception):
            raise self.model
        return self.model


def _config() -> RerankerModelConfig:
    return RerankerModelConfig(device="cpu")


async def test_provider_returns_finite_scores_and_caches_the_model() -> None:
    model = FakeModel([-2.0, 3.5])
    loader = FakeLoader(model)
    provider = BgeM3RerankerProvider(_config(), loader)

    response = await provider.rerank(RerankRequest(query="query", passages=("first", "second")))
    await provider.rerank(RerankRequest(query="query", passages=("first", "second")))

    assert response.scores == (-2.0, 3.5)
    assert response.model_id == "BAAI/bge-reranker-v2-m3"
    assert loader.load_calls == 1
    assert model.predict_calls == 2


@pytest.mark.parametrize("scores", [[0.1], [math.nan, 0.1], [math.inf, 0.1], "invalid"])
async def test_provider_rejects_invalid_scores(scores: object) -> None:
    provider = BgeM3RerankerProvider(_config(), FakeLoader(FakeModel(scores)))

    with pytest.raises(RerankerError) as error:
        await provider.rerank(RerankRequest(query="query", passages=("first", "second")))

    assert error.value.kind is RerankerFailureKind.INVALID_OUTPUT


async def test_provider_preserves_loader_failure_category() -> None:
    provider = BgeM3RerankerProvider(
        _config(), FakeLoader(RerankerError(RerankerFailureKind.UNAVAILABLE))
    )

    with pytest.raises(RerankerError) as error:
        await provider.rerank(RerankRequest(query="query", passages=("first",)))

    assert error.value.kind is RerankerFailureKind.UNAVAILABLE


def test_request_rejects_blank_query_or_passage() -> None:
    with pytest.raises(ValueError, match="non-blank"):
        RerankRequest(query=" ", passages=("passage",))
