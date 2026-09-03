"""Deterministic contract tests for the local HTTP generation adapters."""

import json

import httpx
import pytest
from pydantic import BaseModel

from legal_research.adapters.generation import (
    OllamaGenerationProvider,
    OpenAICompatibleGenerationProvider,
    create_generation_provider,
)
from legal_research.config import (
    GenerationCapabilities,
    GenerationProvider,
    GenerationProviderConfig,
)
from legal_research.ports.generation import (
    GenerationFailure,
    GenerationFailureKind,
    PlainTextGenerationRequest,
    StructuredGenerationRequest,
)
from legal_research.ports.readiness import CapabilityStatus


class SmokeSchema(BaseModel):
    """The minimal P1.6 JSON-schema capability fixture."""

    status: str


def _config(provider: GenerationProvider = GenerationProvider.OLLAMA) -> GenerationProviderConfig:
    return GenerationProviderConfig(
        provider=provider,
        model="test-model",
        base_url="http://local.test"
        if provider is GenerationProvider.OLLAMA
        else "http://local.test/v1",
        api_key=None,
        timeout_seconds=10,
        capabilities=GenerationCapabilities(structured_output=True),
    )


def _client(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=handler, base_url="http://local.test/v1")


async def test_ollama_adapter_checks_model_and_generates_text() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/v1/api/tags":
            return httpx.Response(200, json={"models": [{"name": "test-model"}]})
        return httpx.Response(200, json={"message": {"content": "capability-ok"}})

    provider = OllamaGenerationProvider(_config(), client=_client(httpx.MockTransport(handler)))

    assert await provider.readiness_status() is CapabilityStatus.READY
    result = await provider.generate_text(PlainTextGenerationRequest(prompt="Reply."))

    assert not isinstance(result, GenerationFailure)
    assert result.text == "capability-ok"
    assert json.loads(requests[1].content) == {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Reply."}],
        "stream": False,
        "options": {"temperature": 0},
    }


async def test_ollama_adapter_sends_pydantic_schema_and_validates_result() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["format"] == SmokeSchema.model_json_schema()
        return httpx.Response(200, json={"message": {"content": '{"status":"ok"}'}})

    provider = OllamaGenerationProvider(_config(), client=_client(httpx.MockTransport(handler)))
    result = await provider.generate_structured(
        StructuredGenerationRequest(prompt="Return JSON.", response_model=SmokeSchema)
    )

    assert not isinstance(result, GenerationFailure)
    assert result.output == SmokeSchema(status="ok")


async def test_openai_compatible_adapter_checks_model_and_generates_structured_output() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": "test-model"}]})
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"status":"ok"}'}}]},
        )

    provider = OpenAICompatibleGenerationProvider(
        _config(GenerationProvider.OPENAI_COMPATIBLE),
        client=_client(httpx.MockTransport(handler)),
    )

    assert await provider.readiness_status() is CapabilityStatus.READY
    result = await provider.generate_structured(
        StructuredGenerationRequest(prompt="Return JSON.", response_model=SmokeSchema)
    )

    assert not isinstance(result, GenerationFailure)
    assert result.output == SmokeSchema(status="ok")
    payload = json.loads(requests[1].content)
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["schema"] == SmokeSchema.model_json_schema()


async def test_openai_compatible_adapter_uses_reasoning_content_only_for_validated_schema() -> None:
    provider = OpenAICompatibleGenerationProvider(
        _config(GenerationProvider.OPENAI_COMPATIBLE),
        client=_client(
            httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    json={
                        "choices": [
                            {
                                "message": {
                                    "content": "",
                                    "reasoning_content": '{"status":"ok"}',
                                }
                            }
                        ]
                    },
                )
            )
        ),
    )

    structured = await provider.generate_structured(
        StructuredGenerationRequest(prompt="Return JSON.", response_model=SmokeSchema)
    )
    text = await provider.generate_text(PlainTextGenerationRequest(prompt="Reply."))

    assert not isinstance(structured, GenerationFailure)
    assert structured.output == SmokeSchema(status="ok")
    assert text == GenerationFailure(GenerationFailureKind.MALFORMED_RESPONSE)


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [(429, GenerationFailureKind.RATE_LIMITED), (400, GenerationFailureKind.PROVIDER_REJECTED)],
)
async def test_adapter_maps_http_failures_without_retaining_response_details(
    status_code: int, expected: GenerationFailureKind
) -> None:
    provider = OllamaGenerationProvider(
        _config(),
        client=_client(httpx.MockTransport(lambda _: httpx.Response(status_code))),
    )

    result = await provider.generate_text(PlainTextGenerationRequest(prompt="Reply."))

    assert result == GenerationFailure(expected)


async def test_adapter_rejects_malformed_and_schema_invalid_responses() -> None:
    malformed = OllamaGenerationProvider(
        _config(),
        client=_client(httpx.MockTransport(lambda _: httpx.Response(200, json={}))),
    )
    invalid = OllamaGenerationProvider(
        _config(),
        client=_client(
            httpx.MockTransport(
                lambda _: httpx.Response(200, json={"message": {"content": '{"wrong":true}'}})
            )
        ),
    )

    malformed_result = await malformed.generate_text(PlainTextGenerationRequest(prompt="Reply."))
    invalid_result = await invalid.generate_structured(
        StructuredGenerationRequest(prompt="Return JSON.", response_model=SmokeSchema)
    )

    assert malformed_result == GenerationFailure(GenerationFailureKind.MALFORMED_RESPONSE)
    assert invalid_result == GenerationFailure(GenerationFailureKind.VALIDATION_FAILURE)


def test_factory_constructs_only_the_configured_provider_family() -> None:
    assert isinstance(create_generation_provider(_config()), OllamaGenerationProvider)
    assert isinstance(
        create_generation_provider(_config(GenerationProvider.OPENAI_COMPATIBLE)),
        OpenAICompatibleGenerationProvider,
    )
