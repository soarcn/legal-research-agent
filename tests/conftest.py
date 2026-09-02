"""Shared test fixtures and real-service test policy."""

import os

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Keep Docker-backed integration tests opt-in for local development and CI."""
    if os.environ.get("RUN_REAL_INTEGRATION") == "1":
        return

    skip_real_service = pytest.mark.skip(
        reason="requires local Docker services; set RUN_REAL_INTEGRATION=1 to run"
    )
    for item in items:
        if item.get_closest_marker("real_service"):
            item.add_marker(skip_real_service)
