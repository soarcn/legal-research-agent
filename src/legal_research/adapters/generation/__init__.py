"""Local generation-runtime adapters."""

from legal_research.adapters.generation.http import (
    OllamaGenerationProvider,
    OpenAICompatibleGenerationProvider,
    create_generation_provider,
)

__all__ = [
    "OllamaGenerationProvider",
    "OpenAICompatibleGenerationProvider",
    "create_generation_provider",
]
