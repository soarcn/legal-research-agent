"""Provider-neutral contracts for bounded text and structured generation.

Concrete providers translate their own SDK or HTTP failures into
``GenerationFailure``.  The application therefore never imports a provider
SDK or needs to infer operational meaning from provider-specific exceptions.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel

from legal_research.ports.readiness import CapabilityStatus


class GenerationFailureKind(StrEnum):
    """Stable, provider-neutral classifications for a generation attempt."""

    TRANSPORT_ERROR = "transport_error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    PROVIDER_REJECTED = "provider_rejected"
    MALFORMED_RESPONSE = "malformed_response"
    VALIDATION_FAILURE = "validation_failure"


@dataclass(frozen=True, slots=True)
class GenerationFailure:
    """A failed attempt with no provider exception or raw response attached."""

    kind: GenerationFailureKind

    @property
    def retryable(self) -> bool:
        """Whether callers may retry without changing the request."""

        return self.kind in {
            GenerationFailureKind.TRANSPORT_ERROR,
            GenerationFailureKind.TIMEOUT,
            GenerationFailureKind.RATE_LIMITED,
        }


@dataclass(frozen=True, slots=True)
class PlainTextGenerationRequest:
    """A provider-neutral request for one plain-text completion."""

    prompt: str


@dataclass(frozen=True, slots=True)
class PlainTextGenerationResponse:
    """The provider-neutral result of a plain-text completion."""

    text: str
    model_id: str


@dataclass(frozen=True, slots=True)
class StructuredGenerationRequest[StructuredOutputT: BaseModel]:
    """A request whose output must validate against a caller-owned Pydantic schema."""

    prompt: str
    response_model: type[StructuredOutputT]


@dataclass(frozen=True, slots=True)
class StructuredGenerationResponse[StructuredOutputT: BaseModel]:
    """A Pydantic-validated structured completion."""

    output: StructuredOutputT
    model_id: str


type GenerationResult[OutputT] = OutputT | GenerationFailure


class GenerationProvider(Protocol):
    """The only generation boundary that application workflows depend on."""

    async def generate_text(
        self,
        request: PlainTextGenerationRequest,
    ) -> GenerationResult[PlainTextGenerationResponse]:
        """Generate plain text or return a classified failure."""

        ...

    async def generate_structured[StructuredOutputT: BaseModel](
        self,
        request: StructuredGenerationRequest[StructuredOutputT],
    ) -> GenerationResult[StructuredGenerationResponse[StructuredOutputT]]:
        """Generate and validate a structured response or return a classified failure."""

        ...


class GenerationReadinessProvider(Protocol):
    """A provider-neutral, read-only health boundary for an active generator."""

    async def readiness_status(self) -> CapabilityStatus:
        """Return whether the configured provider is usable without generating text."""

        ...
