"""Bounded HTTP adapters for the local generation runtimes used in P1."""

import json
from collections.abc import Mapping
from typing import Any, ClassVar

import httpx
from pydantic import BaseModel, ValidationError

from legal_research.config import GenerationProvider as GenerationProviderKind
from legal_research.config import GenerationProviderConfig
from legal_research.ports.generation import (
    GenerationFailure,
    GenerationFailureKind,
    GenerationProvider,
    GenerationResult,
    PlainTextGenerationRequest,
    PlainTextGenerationResponse,
    StructuredGenerationRequest,
    StructuredGenerationResponse,
)
from legal_research.ports.readiness import CapabilityStatus


class _HttpGenerationProvider(GenerationProvider):
    """Shared safe HTTP handling for one configured local generation provider."""

    def __init__(
        self,
        config: GenerationProviderConfig,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = config
        self._client = client or httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            headers=_headers(config),
        )
        self._owns_client = client is None

    async def aclose(self) -> None:
        """Close only the client constructed by this adapter."""
        if self._owns_client:
            await self._client.aclose()

    async def readiness_status(self) -> CapabilityStatus:
        """Check that the configured model is visible without invoking it."""
        response_or_failure = await self._request("GET", self._models_path)
        if isinstance(response_or_failure, GenerationFailure):
            return (
                CapabilityStatus.ERROR if response_or_failure.retryable else CapabilityStatus.FAILED
            )

        try:
            model_ids = self._model_ids(response_or_failure.json())
        except (TypeError, ValueError, json.JSONDecodeError):
            return CapabilityStatus.ERROR
        return (
            CapabilityStatus.READY if self._config.model in model_ids else CapabilityStatus.FAILED
        )

    async def generate_text(
        self, request: PlainTextGenerationRequest
    ) -> GenerationResult[PlainTextGenerationResponse]:
        response_or_failure = await self._request(
            "POST", self._chat_path, json_body=self._text_payload(request)
        )
        if isinstance(response_or_failure, GenerationFailure):
            return response_or_failure

        content = _response_content(response_or_failure)
        if content is None:
            return GenerationFailure(GenerationFailureKind.MALFORMED_RESPONSE)
        return PlainTextGenerationResponse(text=content, model_id=self._config.model)

    async def generate_structured[StructuredOutputT: BaseModel](
        self, request: StructuredGenerationRequest[StructuredOutputT]
    ) -> GenerationResult[StructuredGenerationResponse[StructuredOutputT]]:
        response_or_failure = await self._request(
            "POST", self._chat_path, json_body=self._structured_payload(request)
        )
        if isinstance(response_or_failure, GenerationFailure):
            return response_or_failure

        content = _response_content(response_or_failure, allow_structured_reasoning=True)
        if content is None:
            return GenerationFailure(GenerationFailureKind.MALFORMED_RESPONSE)
        try:
            output = request.response_model.model_validate_json(content)
        except ValidationError:
            return GenerationFailure(GenerationFailureKind.VALIDATION_FAILURE)
        return StructuredGenerationResponse(output=output, model_id=self._config.model)

    async def _request(
        self, method: str, path: str, *, json_body: dict[str, object] | None = None
    ) -> httpx.Response | GenerationFailure:
        try:
            response = await self._client.request(method, path, json=json_body)
        except httpx.TimeoutException:
            return GenerationFailure(GenerationFailureKind.TIMEOUT)
        except httpx.TransportError:
            return GenerationFailure(GenerationFailureKind.TRANSPORT_ERROR)

        if response.status_code == 429:
            return GenerationFailure(GenerationFailureKind.RATE_LIMITED)
        if response.is_error:
            return GenerationFailure(GenerationFailureKind.PROVIDER_REJECTED)
        return response

    _models_path: ClassVar[str]
    _chat_path: ClassVar[str]

    def _model_ids(self, payload: object) -> set[str]:
        raise NotImplementedError

    def _text_payload(self, request: PlainTextGenerationRequest) -> dict[str, object]:
        raise NotImplementedError

    def _structured_payload[StructuredOutputT: BaseModel](
        self, request: StructuredGenerationRequest[StructuredOutputT]
    ) -> dict[str, object]:
        raise NotImplementedError


class OllamaGenerationProvider(_HttpGenerationProvider):
    """Ollama native `/api/chat` adapter with JSON-schema output support."""

    _models_path = "api/tags"
    _chat_path = "api/chat"

    def _model_ids(self, payload: object) -> set[str]:
        if not isinstance(payload, Mapping) or not isinstance(payload.get("models"), list):
            raise ValueError("Ollama model list is malformed")
        ids: set[str] = set()
        for item in payload["models"]:
            if not isinstance(item, Mapping):
                continue
            for key in ("name", "model"):
                value = item.get(key)
                if isinstance(value, str):
                    ids.add(value)
        return ids

    def _text_payload(self, request: PlainTextGenerationRequest) -> dict[str, object]:
        return _ollama_payload(self._config.model, request.prompt)

    def _structured_payload[StructuredOutputT: BaseModel](
        self, request: StructuredGenerationRequest[StructuredOutputT]
    ) -> dict[str, object]:
        return _ollama_payload(
            self._config.model, request.prompt, format=request.response_model.model_json_schema()
        )


class OpenAICompatibleGenerationProvider(_HttpGenerationProvider):
    """Generic OpenAI-compatible adapter, validated against LM Studio in P1.6."""

    _models_path = "models"
    _chat_path = "chat/completions"

    def _model_ids(self, payload: object) -> set[str]:
        if not isinstance(payload, Mapping) or not isinstance(payload.get("data"), list):
            raise ValueError("OpenAI-compatible model list is malformed")
        return {
            item["id"]
            for item in payload["data"]
            if isinstance(item, Mapping) and isinstance(item.get("id"), str)
        }

    def _text_payload(self, request: PlainTextGenerationRequest) -> dict[str, object]:
        return _openai_payload(self._config.model, request.prompt)

    def _structured_payload[StructuredOutputT: BaseModel](
        self, request: StructuredGenerationRequest[StructuredOutputT]
    ) -> dict[str, object]:
        schema_name = request.response_model.__name__.lower()
        return _openai_payload(
            self._config.model,
            request.prompt,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": request.response_model.model_json_schema(),
                },
            },
        )


def create_generation_provider(config: GenerationProviderConfig) -> _HttpGenerationProvider:
    """Construct exactly the provider explicitly selected by validated settings."""
    if config.provider is GenerationProviderKind.OLLAMA:
        return OllamaGenerationProvider(config)
    return OpenAICompatibleGenerationProvider(config)


def _headers(config: GenerationProviderConfig) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if config.api_key is not None:
        headers["Authorization"] = f"Bearer {config.api_key.get_secret_value()}"
    return headers


def _ollama_payload(
    model: str, prompt: str, *, format: dict[str, object] | None = None
) -> dict[str, object]:
    payload: dict[str, object] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0},
    }
    if format is not None:
        payload["format"] = format
    return payload


def _openai_payload(
    model: str, prompt: str, *, response_format: dict[str, object] | None = None
) -> dict[str, object]:
    payload: dict[str, object] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "temperature": 0,
    }
    if response_format is not None:
        payload["response_format"] = response_format
    return payload


def _response_content(
    response: httpx.Response, *, allow_structured_reasoning: bool = False
) -> str | None:
    """Extract only user-facing content, with a narrow schema-only compatibility fallback.

    Some local reasoning models return a JSON-schema-constrained response in
    ``reasoning_content`` while leaving ``content`` empty. The fallback is
    available only for a structured request and the caller immediately validates
    it against its schema. No raw reasoning value is retained, returned, or
    persisted by this adapter.
    """
    try:
        payload: Any = response.json()
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, Mapping):
        return None

    message = payload.get("message")
    if isinstance(message, Mapping) and isinstance(message.get("content"), str):
        return message["content"]

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], Mapping):
        return None
    choice_message = choices[0].get("message")
    if not isinstance(choice_message, Mapping):
        return None
    content = choice_message.get("content")
    if isinstance(content, str) and content:
        return content
    if allow_structured_reasoning:
        reasoning_content = choice_message.get("reasoning_content")
        return reasoning_content if isinstance(reasoning_content, str) else None
    return None
