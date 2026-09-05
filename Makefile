.PHONY: up down services-status reset-postgres reset-weaviate rebuild-index api api-with-embedding api-with-model-capabilities lint format typecheck test cov check audit migrate dataset-fetch dataset-verify benchmark-development benchmark-validation baseline-bm25 baseline-dense ingest embedding-smoke reranker-smoke generation-smoke generation-smoke-ollama generation-smoke-lm-studio

up:
	docker compose up -d postgres weaviate

down:
	docker compose down

services-status:
	docker compose ps

# Destructive: only removes the named PostgreSQL volume after an explicit confirmation value.
reset-postgres:
	test "$(CONFIRM_RESET)" = "postgres"
	docker compose stop postgres
	docker compose rm --force postgres
	docker volume rm legal-research-agent-postgres-data

# Destructive: only removes the named Weaviate volume after an explicit confirmation value.
reset-weaviate:
	test "$(CONFIRM_RESET)" = "weaviate"
	docker compose stop weaviate
	docker compose rm --force weaviate
	docker volume rm legal-research-agent-weaviate-data

# Destructive to the named derived collection only; never touches PostgreSQL or raw source files.
rebuild-index:
	test "$(CONFIRM_REBUILD_INDEX)" = "legal-passage-v1"
	PYTHONPATH=src uv run --group embedding python scripts/rebuild_legal_rag_index.py

api:
	PYTHONPATH=src uv run uvicorn apps.api.main:app --reload

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run pyright

test:
	uv run pytest

cov:
	uv run pytest --cov --cov-report=term-missing

check:
	uv run ruff format --check .
	uv run ruff check .
	uv run pyright
	uv run pytest

audit:
	uv run pip-audit --local

migrate:
	uv run alembic upgrade head

dataset-fetch:
	PYTHONPATH=src uv run python scripts/fetch_legal_rag_bench.py

dataset-verify:
	PYTHONPATH=src uv run python scripts/fetch_legal_rag_bench.py --verify-only

benchmark-development:
	PYTHONPATH=src uv run python scripts/load_retrieval_benchmark.py --split development

benchmark-validation:
	PYTHONPATH=src uv run python scripts/load_retrieval_benchmark.py --split validation

baseline-bm25:
	PYTHONPATH=src uv run python scripts/run_retrieval_baseline.py --mode bm25 --experiment-id retrieval-bm25-dev-v1

baseline-dense:
	PYTHONPATH=src uv run --group embedding python scripts/run_retrieval_baseline.py --mode dense --experiment-id retrieval-dense-dev-v1

ingest:
	PYTHONPATH=src uv run --group embedding python scripts/ingest_legal_rag_bench.py

embedding-smoke:
	EMBEDDING__LOCAL_FILES_ONLY=false PYTHONPATH=src uv run --group embedding python scripts/run_embedding_smoke.py

reranker-smoke:
	RERANKER__LOCAL_FILES_ONLY=false PYTHONPATH=src uv run --group reranker python scripts/run_reranker_smoke.py

generation-smoke:
	PYTHONPATH=src uv run python scripts/run_generation_smoke.py

generation-smoke-ollama:
	GENERATION_PROVIDER=ollama GENERATION_BASE_URL=http://localhost:11434 $(MAKE) generation-smoke

generation-smoke-lm-studio:
	GENERATION_PROVIDER=openai_compatible GENERATION_BASE_URL=http://localhost:1234/v1 $(MAKE) generation-smoke

api-with-embedding:
	EMBEDDING_ENABLED=true PYTHONPATH=src uv run uvicorn apps.api.main:app --reload

api-with-model-capabilities:
	EMBEDDING_ENABLED=true RERANKER_ENABLED=true PYTHONPATH=src uv run uvicorn apps.api.main:app --reload
