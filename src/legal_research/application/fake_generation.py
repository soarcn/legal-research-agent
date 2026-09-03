"""A deterministic provider for contract and workflow tests.

It exercises the same result contract as real adapters while performing no
network I/O, model download, or provider SDK call.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field

from pydantic import BaseModel, ValidationError

from legal_research.ports.generation import (
    GenerationFailure,
    GenerationFailureKind,
    GenerationResult,
    PlainTextGenerationRequest,
    PlainTextGenerationResponse,
    StructuredGenerationRequest,
    StructuredGenerationResponse,
)
from legal_research.ports.readiness import CapabilityStatus


@dataclass(slots=True)
class FakeGenerationProvider:
    """Return configured outputs keyed by prompt, with explicit failure injection."""

    model_id: str = "fake-model"
    text_responses: Mapping[str, str] = field(default_factory=dict)
    structured_responses: Mapping[str, Mapping[str, object] | str] = field(default_factory=dict)
    failures: Mapping[str, GenerationFailureKind] = field(default_factory=dict)
    readiness: CapabilityStatus = CapabilityStatus.READY

    async def readiness_status(self) -> CapabilityStatus:
        """Return a configured capability state without contacting a provider."""

        return self.readiness

    async def generate_text(
        self,
        request: PlainTextGenerationRequest,
    ) -> GenerationResult[PlainTextGenerationResponse]:
        """Return a configured plain-text completion without external I/O."""

        failure = self._configured_failure(request.prompt)
        if failure is not None:
            return failure

        text = self.text_responses.get(request.prompt)
        if text is None:
            return GenerationFailure(kind=GenerationFailureKind.PROVIDER_REJECTED)

        return PlainTextGenerationResponse(text=text, model_id=self.model_id)

    async def generate_structured[StructuredOutputT: BaseModel](
        self,
        request: StructuredGenerationRequest[StructuredOutputT],
    ) -> GenerationResult[StructuredGenerationResponse[StructuredOutputT]]:
        """Return a configured payload after validating it with the requested schema."""

        failure = self._configured_failure(request.prompt)
        if failure is not None:
            return failure

        payload = self.structured_responses.get(request.prompt)
        if payload is None:
            return GenerationFailure(kind=GenerationFailureKind.PROVIDER_REJECTED)
        if not isinstance(payload, Mapping):
            return GenerationFailure(kind=GenerationFailureKind.MALFORMED_RESPONSE)

        try:
            output = request.response_model.model_validate(payload)
        except ValidationError:
            return GenerationFailure(kind=GenerationFailureKind.VALIDATION_FAILURE)

        return StructuredGenerationResponse(output=output, model_id=self.model_id)

    def _configured_failure(self, prompt: str) -> GenerationFailure | None:
        kind = self.failures.get(prompt)
        return GenerationFailure(kind=kind) if kind is not None else None
