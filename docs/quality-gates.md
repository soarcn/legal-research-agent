# Quality gates and CI

## Purpose

P1.1 creates one repeatable quality contract before infrastructure and model work expands the
failure surface. A developer and GitHub Actions should reach the same result from the same commit.
This gate answers a narrow question: is the repository internally consistent and free of known
dependency or committed-secret findings? It does not prove that databases, models, or legal RAG
behaviour work.

## Reproducible toolchain

| Concern | Repository control | Why it matters |
| --- | --- | --- |
| Python | `.python-version` selects `3.12`; `requires-python` rejects other minor versions | Removes accidental testing against a different language runtime |
| uv | `[tool.uv].required-version` and CI both select `0.11.26` | Avoids lock/sync behaviour changing between machines |
| Dependencies | `uv.lock` plus `uv sync --frozen --group dev` | Installs the reviewed resolution and refuses to rewrite it |
| Agent framework | `pydantic-ai` exists only in the explicit `agent` group | Keeps P1–P6 deterministic work independent of P7 Agent code |

Dependency groups have deliberate boundaries:

- project dependencies run the application;
- `dev` provides deterministic repository checks and security auditing;
- `agent` is opt-in and is not installed by the default P1 CI workflow.

## Local commands

Prepare the exact development environment:

```bash
uv sync --frozen --group dev
```

Run the shared repository gate:

```bash
make check
```

It runs, in order:

1. Ruff formatting verification;
2. Ruff static linting;
3. Pyright type checking;
4. deterministic pytest tests.

Run the dependency vulnerability check separately because it queries an external advisory service:

```bash
make audit
```

`pip-audit` exits non-zero when it finds a published vulnerability. Resolve the finding by reviewing
the advisory, upgrading the direct dependency or its constraint, regenerating `uv.lock`, and rerunning
both commands. Do not suppress a finding without a documented risk decision.

## GitHub Actions

`.github/workflows/ci.yml` runs on every pull request and every push to `main` with read-only
repository permissions. Its two jobs are:

- **Deterministic quality gate:** installs the pinned uv and Python versions, syncs the locked `dev`
  group, then runs `make check` and `make audit`.
- **Secret scan:** checks out full Git history and runs Gitleaks. If a real secret is found, revoke or
  rotate it first; deleting it from the latest commit does not remove it from history.

Third-party actions are pinned to immutable commit SHAs with human-readable release comments. This
reduces supply-chain drift while still making planned upgrades understandable.

The workflow intentionally does not start PostgreSQL, Weaviate, Ollama, Harbor, or model processes,
and it does not download raw legal corpora. Those checks have different resource and trust boundaries
and are introduced by their owning tickets.

## Evidence for P1.1

Before handoff, record these commands and outcomes:

```bash
uv lock --check
make check
make audit
```

The workflow configuration has a deterministic repository contract test. Actual GitHub execution is
verified after the branch is pushed; a locally valid workflow alone is not evidence that GitHub ran it.

## Limitations

- `pip-audit` detects published package vulnerabilities; it is not a source-code review or malicious
  package detector.
- Gitleaks detects likely committed secrets; runtime log redaction remains a separate P9 control.
- Container image scanning starts after P1.2 defines the stable service images.
- Model, provider, database, and retrieval correctness require their own smoke, integration, and
  evaluation suites.
