import pytest
from pydantic import ValidationError

from legal_research.config import EmbeddingModelConfig, Settings


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


def test_embedding_defaults_pin_the_future_index_contract() -> None:
    settings = Settings()

    assert settings.embedding.model_id == "BAAI/bge-m3"
    assert settings.embedding.revision == "3806044eb869c8756693584f7eb5dd04ab2bdd95"
    assert settings.embedding.expected_dimension == 1024
    assert settings.embedding.normalize is True
    assert settings.embedding.local_files_only is True


def test_embedding_config_rejects_a_non_commit_revision() -> None:
    with pytest.raises(ValidationError, match="commit SHA"):
        EmbeddingModelConfig(revision="main")
