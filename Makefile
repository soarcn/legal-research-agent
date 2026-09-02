.PHONY: up down services-status reset-postgres reset-weaviate api lint format typecheck test cov check audit migrate

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

api:
	uv run uvicorn apps.api.main:app --reload

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
