.PHONY: up down api lint format typecheck test cov check migrate

up:
	docker compose up -d postgres weaviate

down:
	docker compose down

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

migrate:
	uv run alembic upgrade head
