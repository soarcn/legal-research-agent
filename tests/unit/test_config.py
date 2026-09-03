import pytest
from pydantic import SecretStr, ValidationError

from legal_research.config import GenerationProvider, Settings


def test_default_settings_load() -> None:
    """Settings can be instantiated with defaults (no .env required)."""
    settings = Settings()

    assert settings.app_env == "development"
    assert "legal_agent" in settings.database_url
    assert settings.weaviate_grpc_port == 50051
    assert settings.corpus_source_snapshot_id.startswith("legal-rag-bench@")


def test_corpus_snapshot_id_pinned() -> None:
    """The pinned revision matches the P0 decision."""
    settings = Settings()
    expected_revision = "db0b31dc6d195ce9916897e1ac5e4e6209736c8a"

    assert expected_revision in settings.corpus_source_snapshot_id


def test_active_generation_provider_config_has_safe_ollama_defaults() -> None:
    """Exactly one typed, offline-default provider configuration is active."""
    settings = Settings()

    provider = settings.generation_provider_config

    assert provider.provider is GenerationProvider.OLLAMA
    assert provider.model == "qwen3:8b"
    assert provider.base_url == "http://localhost:11434"
    assert provider.api_key is None
    assert provider.timeout_seconds == 60.0
    assert provider.capabilities.text_generation is True
    assert provider.capabilities.structured_output is False
    assert provider.capabilities.tool_calling is False
    assert provider.capabilities.streaming is False


def test_openai_compatible_provider_uses_one_active_typed_configuration() -> None:
    """Provider selection is explicit rather than inferred from an endpoint."""
    settings = Settings(
        generation_provider=GenerationProvider.OPENAI_COMPATIBLE,
        generation_model="local-qwen",
        generation_base_url="http://localhost:1234/v1",
        generation_api_key=SecretStr("local-development-key"),
        generation_timeout_seconds=12.5,
        generation_supports_structured_output=True,
        generation_supports_tool_calling=True,
        generation_supports_streaming=True,
    )

    provider = settings.generation_provider_config

    assert provider.provider is GenerationProvider.OPENAI_COMPATIBLE
    assert provider.model == "local-qwen"
    assert provider.base_url == "http://localhost:1234/v1"
    assert provider.api_key is not None
    assert provider.api_key.get_secret_value() == "local-development-key"
    assert provider.timeout_seconds == 12.5
    assert provider.capabilities.structured_output is True
    assert provider.capabilities.tool_calling is True
    assert provider.capabilities.streaming is True
    assert "local-development-key" not in repr(provider)


def test_generation_configuration_loads_the_active_provider_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deployment selects the provider through documented, provider-neutral variables."""
    monkeypatch.setenv("GENERATION_PROVIDER", "openai_compatible")
    monkeypatch.setenv("GENERATION_MODEL", "lm-studio-model")
    monkeypatch.setenv("GENERATION_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("GENERATION_SUPPORTS_STRUCTURED_OUTPUT", "true")

    provider = Settings().generation_provider_config

    assert provider.provider is GenerationProvider.OPENAI_COMPATIBLE
    assert provider.model == "lm-studio-model"
    assert provider.base_url == "http://localhost:1234/v1"
    assert provider.capabilities.structured_output is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("generation_provider", "unknown"),
        ("generation_model", "   "),
        ("generation_base_url", "ftp://localhost:11434"),
        ("generation_base_url", "http://user:password@localhost:11434"),
        ("generation_base_url", "http://localhost:11434/?token=secret"),
        ("generation_api_key", " "),
        ("generation_timeout_seconds", 0),
        ("generation_timeout_seconds", 301),
    ],
)
def test_generation_configuration_rejects_unsafe_or_ambiguous_values(
    field: str, value: object
) -> None:
    """Configuration failures occur before a provider can make a network call."""
    with pytest.raises(ValidationError):
        Settings.model_validate({field: value})
