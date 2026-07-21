.PHONY: up down api lint test migrate

up:
	docker compose up -d postgres weaviate

down:
	docker compose down

api:
	uv run uvicorn apps.api.main:app --reload

lint:
	uv run ruff check .

test:
	uv run pytest

migrate:
	uv run alembic upgrade head
