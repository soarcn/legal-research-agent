"""Deterministic contract tests for provider-neutral text generation."""

from pydantic import BaseModel
from pytest import mark

from legal_research.application.fake_generation import FakeGenerationProvider
from legal_research.ports.generation import (
    GenerationFailure,
    GenerationFailureKind,
    PlainTextGenerationRequest,
    PlainTextGenerationResponse,
    StructuredGenerationRequest,
    StructuredGenerationResponse,
)
from legal_research.ports.readiness import CapabilityStatus


class AnswerSchema(BaseModel):
    """A small schema that makes structured-output validation observable."""

    answer: str
    passage_ids: list[str]


async def test_fake_provider_returns_a_typed_plain_text_response() -> None:
    provider = FakeGenerationProvider(
        model_id="test-model",
        text_responses={"Summarise this.": "A short summary."},
    )

    result = await provider.generate_text(PlainTextGenerationRequest(prompt="Summarise this."))

    assert result == PlainTextGenerationResponse(text="A short summary.", model_id="test-model")


async def test_fake_provider_validates_structured_output_against_the_requested_schema() -> None:
    provider = FakeGenerationProvider(
        model_id="test-model",
        structured_responses={
            "Answer with evidence.": {"answer": "Supported.", "passage_ids": ["passage-1"]}
        },
    )

    result = await provider.generate_structured(
        StructuredGenerationRequest(
            prompt="Answer with evidence.",
            response_model=AnswerSchema,
        )
    )

    assert result == StructuredGenerationResponse(
        output=AnswerSchema(answer="Supported.", passage_ids=["passage-1"]),
        model_id="test-model",
    )


@mark.parametrize(
    ("failure_kind", "retryable"),
    [
        (GenerationFailureKind.TRANSPORT_ERROR, True),
        (GenerationFailureKind.TIMEOUT, True),
        (GenerationFailureKind.RATE_LIMITED, True),
        (GenerationFailureKind.PROVIDER_REJECTED, False),
        (GenerationFailureKind.MALFORMED_RESPONSE, False),
        (GenerationFailureKind.VALIDATION_FAILURE, False),
    ],
)
async def test_fake_provider_preserves_each_provider_neutral_failure_classification(
    failure_kind: GenerationFailureKind,
    retryable: bool,
) -> None:
    provider = FakeGenerationProvider(failures={"Unavailable.": failure_kind})

    result = await provider.generate_text(PlainTextGenerationRequest(prompt="Unavailable."))

    assert isinstance(result, GenerationFailure)
    assert result.kind is failure_kind
    assert result.retryable is retryable


async def test_fake_provider_distinguishes_malformed_structured_payloads() -> None:
    provider = FakeGenerationProvider(structured_responses={"Bad JSON.": "not a JSON object"})

    result = await provider.generate_structured(
        StructuredGenerationRequest(
            prompt="Bad JSON.",
            response_model=AnswerSchema,
        )
    )

    assert result == GenerationFailure(kind=GenerationFailureKind.MALFORMED_RESPONSE)


async def test_fake_provider_distinguishes_schema_validation_failures() -> None:
    provider = FakeGenerationProvider(structured_responses={"Wrong shape.": {"answer": 42}})

    result = await provider.generate_structured(
        StructuredGenerationRequest(
            prompt="Wrong shape.",
            response_model=AnswerSchema,
        )
    )

    assert result == GenerationFailure(kind=GenerationFailureKind.VALIDATION_FAILURE)


async def test_fake_provider_exposes_a_provider_neutral_readiness_state() -> None:
    provider = FakeGenerationProvider(readiness=CapabilityStatus.DISABLED)

    assert await provider.readiness_status() is CapabilityStatus.DISABLED
