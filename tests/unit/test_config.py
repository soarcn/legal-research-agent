from legal_research.config import Settings


def test_default_settings_load() -> None:
    """Settings can be instantiated with defaults (no .env required)."""
    settings = Settings()

    assert settings.app_env == "development"
    assert "legal_agent" in settings.database_url
    assert settings.corpus_source_snapshot_id.startswith("legal-rag-bench@")


def test_corpus_snapshot_id_pinned() -> None:
    """The pinned revision matches the P0 decision."""
    settings = Settings()
    expected_revision = "db0b31dc6d195ce9916897e1ac5e4e6209736c8a"

    assert expected_revision in settings.corpus_source_snapshot_id
