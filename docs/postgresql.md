# PostgreSQL runtime capability

PostgreSQL is the authoritative system of record for this project. In P1 it
contains only Alembic's migration ledger; legal documents, passages, research
runs, and audit records are intentionally deferred to P2 and later.

## What is verified now

The PostgreSQL adapter uses SQLAlchemy's async `asyncpg` driver and proves a
real connection with `SELECT 1`. The opt-in integration check also proves that
a transaction commit persists a row and a rollback does not, using a temporary
table on one connection. It creates no persistent application table.

The `0001_initial` migration is deliberately empty. After a fresh upgrade, the
only persistent relation in the `public` schema is Alembic's
`alembic_version` ledger. The real integration test creates a uniquely named
temporary database for this assertion, upgrades it, and drops it afterwards;
it never writes the normal `legal_agent` database's migration ledger.

## Local lifecycle

Start the project's database service and wait for Docker's health check:

```bash
make up
docker compose ps postgres
make migrate
```

Stopping the service is non-destructive and preserves its named volume:

```bash
make down
```

To run the real PostgreSQL check, Docker Desktop must be running and the
service must be healthy:

```bash
RUN_REAL_INTEGRATION=1 uv run pytest tests/integration/test_postgres.py -q
```

The normal `make check` suite does not require Docker. It skips this opt-in
test file with an explicit reason when `RUN_REAL_INTEGRATION` is not `1`.

## Reset and recovery

Resetting database storage is destructive and is never part of application
startup, migrations, or tests. Use the explicit project-scoped reset command
only when you intentionally want to discard local PostgreSQL state:

```bash
make reset-postgres CONFIRM_RESET=postgres
make up
make migrate
```

`reset-postgres` targets only the named PostgreSQL volume for this project,
never all Docker volumes. After a reset, use `make migrate` to recreate the
empty P1 baseline before running real integration tests.

## Readiness behavior

`PostgresReadinessProbe` is a narrow adapter around `AsyncPostgresDatabase`.
It reports only `ready` or `failed`; the application-level `ReadinessService`
sets the HTTP status and replaces diagnostic details with a fixed safe message.
Connection URLs, credentials, and database driver exceptions must never appear
in `/ready`, test fixtures, or operator-facing reports.

The API composition root registers this probe with the configured
`DATABASE_URL`. A healthy Docker container alone is not enough: `/ready`
returns PostgreSQL `ready` only after the async adapter can connect and issue
its query.
