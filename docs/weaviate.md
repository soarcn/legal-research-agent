# Weaviate runtime capability

Weaviate is the project’s derived, rebuildable search index. It is not the
authoritative source of legal documents, source snapshots, or audit records;
those responsibilities belong to PostgreSQL and local source artifacts.

Issue #5 establishes only a runtime connectivity capability. It does **not**
create a collection, define a vector schema, ingest a corpus, run BM25, or
perform retrieval. Those are later P3–P5 responsibilities.

## Readiness contract

`WeaviateReadinessProbe` establishes an asynchronous connection to the
configured endpoint, relies on the v4 client's initialization readiness check,
and closes the client. It intentionally does not call the SDK's separate
`is_ready()` helper because that helper can print raw connection errors before
the application's diagnostic boundary can redact them. The probe uses the
configured `WEAVIATE_URL` rather than a hard-coded hostname. The local default
is `http://localhost:8080`; Docker also exposes gRPC on `50051` for the Python
client's connection checks.

The probe returns only `ready` or `failed`. The shared `ReadinessService`
maps a failure to the fixed diagnostic `Capability is unavailable.` before it
reaches `GET /ready`. Connection URLs, credentials, SDK exception text, and
server responses must never be exposed by this endpoint.

## Lifecycle

Start the project services from the repository root:

```bash
docker compose up -d weaviate
docker compose ps weaviate
```

Normal stop/start cycles preserve the named Weaviate volume. Do not delete the
volume as part of routine development. A reset is a deliberate destructive
operation and is never performed by tests or application startup. When a reset
is explicitly required, use the confirmation-protected command:

```bash
make reset-weaviate CONFIRM_RESET=weaviate
```

When the API composition registers this capability, confirm it with:

```bash
curl -i http://127.0.0.1:8000/ready
```

The response proves only the currently configured service is reachable. It
does not prove that an index exists, a corpus was loaded, or any legal answer
is reliable.

## Tests

The deterministic adapter tests need no Docker:

```bash
uv run pytest tests/integration/test_weaviate.py -q
```

They include a fake unavailable client and verify the shared readiness layer
does not reveal an unsafe connection detail. The real connectivity test is
explicitly opt-in:

```bash
docker compose up -d weaviate
RUN_REAL_INTEGRATION=1 uv run pytest tests/integration/test_weaviate.py -q
```

If the service cannot start, inspect `docker compose ps weaviate` and local
container logs without copying credentials into issue comments. Do not solve
a failed readiness check by disabling the probe.
