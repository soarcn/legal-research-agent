from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]


def test_local_quality_contract_is_reproducible() -> None:
    """The documented local gate must use pinned tooling and exclude P7 Agent code."""
    python_version = (PROJECT_ROOT / ".python-version").read_text().strip()
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    assert python_version == "3.12"
    assert project["tool"]["uv"]["required-version"] == "==0.11.26"

    runtime_dependencies = project["project"]["dependencies"]
    dependency_groups = project["dependency-groups"]
    assert not any(dependency.startswith("pydantic-ai") for dependency in runtime_dependencies)
    assert any(dependency.startswith("pydantic-ai") for dependency in dependency_groups["agent"])
    assert any(dependency.startswith("pip-audit") for dependency in dependency_groups["dev"])

    check = subprocess.run(
        ["make", "-n", "check"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "ruff format --check" in check
    assert "ruff check" in check
    assert "pyright" in check
    assert "pytest" in check

    audit = subprocess.run(
        ["make", "-n", "audit"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "pip-audit --local" in audit


def test_ci_runs_only_deterministic_offline_quality_checks() -> None:
    """Pull requests and main pushes must apply the local gate without loading AI services."""
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text()

    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "contents: read" in workflow
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1" in workflow
    assert "astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9" in workflow
    assert "gitleaks/gitleaks-action@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e" in workflow
    assert "uv sync --frozen --group dev" in workflow
    assert "make check" in workflow
    assert "make audit" in workflow

    forbidden_runtime_dependencies = (
        "--group agent",
        "docker compose",
        "ollama",
        "data/raw",
        "harbor run",
    )
    assert not any(command in workflow.lower() for command in forbidden_runtime_dependencies)
