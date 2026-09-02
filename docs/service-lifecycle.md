# Local service lifecycle

PostgreSQL and Weaviate run in Docker. Python, the FastAPI application, model
runtimes, and evaluation commands run on the macOS host. This preserves Apple
Silicon model acceleration while making the two persistent services repeatable.

## Service boundary

| Service | Container image | Host ports | Persistent volume | Role |
| --- | --- | --- | --- | --- |
| PostgreSQL | `postgres:16.6-alpine3.20` | `5432` | `legal-research-agent-postgres-data` | Authoritative system of record |
| Weaviate | `cr.weaviate.io/semitechnologies/weaviate:1.28.4` | `8080` HTTP, `50051` gRPC | `legal-research-agent-weaviate-data` | Derived, rebuildable search index |

The explicit Compose project name and volume names make the scope of persistent
state visible. A normal stop or start never removes either volume.

## Start, inspect, and stop

Copy the example settings once, then start the two services:

```bash
cp .env.example .env
make up
make services-status
```

Docker reports container health separately from API readiness. Wait for both
services to show `healthy` before running the real-service tests or migrations:

```bash
docker compose ps
make migrate
RUN_REAL_INTEGRATION=1 uv run pytest tests/integration -m real_service -q
```

`make down` stops and removes containers and the Compose network only. It does
not remove named volumes, so a subsequent `make up` preserves local state.

## Connection settings

Host Python uses these development defaults from `.env.example`:

```text
DATABASE_URL=postgresql+asyncpg://legal_agent:legal_agent@localhost:5432/legal_agent
WEAVIATE_URL=http://localhost:8080
WEAVIATE_GRPC_PORT=50051
```

Do not put production credentials in `.env.example`, commit `.env`, or paste a
connection URL containing credentials into issue comments. The development
credentials in Compose are local-only defaults.

## Explicit data reset

Reset is destructive and is never part of `make up`, `make down`, migrations,
or tests. Stop the relevant service and use its exact confirmation value:

```bash
make reset-postgres CONFIRM_RESET=postgres
make reset-weaviate CONFIRM_RESET=weaviate
```

Each command removes only its named project volume. Start the service again
with `make up`; PostgreSQL then needs `make migrate`. Weaviate remains an empty
derived index until a later ingestion phase rebuilds it. Do not use `docker
compose down -v` for routine work because it removes both project volumes.

## Recovery guide

| Situation | Safe recovery |
| --- | --- |
| Container is not running | Run `make up`, then inspect `make services-status`. |
| Container is unhealthy | Inspect `docker compose logs <service>` locally, correct configuration, and restart only that service. Do not copy credentials or raw logs into shared reports. |
| PostgreSQL local state is intentionally discarded | Run the explicit PostgreSQL reset, then `make up` and `make migrate`. |
| Weaviate local state is intentionally discarded | Run the explicit Weaviate reset, then `make up`. A later ingestion command rebuilds the index from authoritative source data. |
| API `/ready` is unavailable while Docker health is healthy | Run the focused capability test and inspect the API's safe diagnostic. Container health and host-Python configuration are separate checks. |

## Real-service test policy

Tests marked `real_service` exercise actual local containers. They are opt-in
because the repository's deterministic quality gate and GitHub Actions do not
start Docker services. The skip reason is visible when the opt-in flag is not
set; it is not a passing connectivity assertion.

```bash
RUN_REAL_INTEGRATION=1 uv run pytest tests/integration -m real_service -q
```

Run `make check` for deterministic tests and `make audit` before handoff. Run
the real-service command after starting Docker whenever changing an adapter,
container configuration, migration, or readiness composition.
