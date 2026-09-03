# Service liveness and readiness

This document defines the operational boundary introduced by Issue #3. It is a
small learning step: a running HTTP process and a system that is safe to accept
research requests are related, but they are not the same thing.

## Two endpoints, two questions

| Endpoint | Question answered | External calls | Success response |
| --- | --- | --- | --- |
| `GET /health` | Is the API process alive and able to serve HTTP? | Never | `200 OK` |
| `GET /ready` | Are all configured capabilities currently usable? | Only through registered probes | `200 OK` |

`/health` is deliberately shallow. It must continue to return `200 OK` when a
database, search index, model runtime, or provider is unavailable. A failing
`/ready` response has a different meaning: the API process is up, but at least
one capability needed by the configured workflow is unavailable.

## HTTP contract

`GET /health` always returns a small process-only body:

```json
{
  "status": "ok",
  "environment": "development"
}
```

`GET /ready` returns a capability report. When every configured probe passes,
it returns `200 OK` and `status: "ready"`. When any configured probe is not
ready, it returns `503 Service Unavailable` and `status: "not_ready"`, while
still returning the result for every probe that completed. A non-ready
capability receives a fixed, bounded diagnostic chosen by the application.

```json
{
  "status": "not_ready",
  "capabilities": [
    {"name": "postgres", "status": "ready"},
    {
      "name": "weaviate",
      "status": "failed",
      "diagnostic": "Capability is unavailable."
    }
  ]
}
```

The specific capability list is configuration-dependent. Each capability has
one of `ready`, `failed`, `disabled`, `timed_out`, or `error` status values;
any value other than `ready` makes the aggregate report `not_ready`. A response
is only a statement about the configured probes at that instant; it is not
evidence that the legal corpus is complete, current, or legally correct.

## Safe diagnostics

Capability results are operator diagnostics, not a debugging dump. The v1 HTTP
response exposes a stable capability name and status, plus a fixed diagnostic
only for a non-ready status. It never forwards probe-provided text. This makes
the diagnostic bounded and useful without trusting an SDK error message. It
must not expose:

- connection URLs, passwords, API keys, or tokens;
- raw exception traces or request headers;
- prompt contents, retrieved passages, or user inputs;
- model internals or source data.

Persisted diagnostics follow the same boundary. Use structured, redacted
operational events rather than arbitrary exception strings.

## Current configured capabilities

The application now composes two real, host-Python capability probes:

- PostgreSQL: an async SQLAlchemy connection issues a read-only `SELECT 1`.
- Weaviate: an async client connects through the configured HTTP and gRPC
  endpoints, asks the server whether it is ready, then closes the client.

The deterministic tests still inject fake probes to prove orchestration and
safe diagnostic behaviour without Docker. Separate tests marked
`real_service` exercise the pinned local containers, and run only when
`RUN_REAL_INTEGRATION=1` is explicitly set. A fake-probe `200` proves the HTTP
semantics; a real-service `200` proves only these two runtime connections at
that instant. Neither establishes an indexed corpus, legal completeness,
currency, or answer correctness.

P1.6 registers exactly one configured local generation adapter in the default
readiness composition. The `generation` probe lists the visible models through
the provider's read-only endpoint and reports ready only when the configured
model is present; it does not send a prompt or disclose provider payloads.

Embedding and reranker capability checks remain opt-in during P1. With
`EMBEDDING_ENABLED=true`, the first `/ready` call can load BGE-M3 and run one
fixed non-legal embedding probe. With `RERANKER_ENABLED=true`, it can also load
the BGE cross-encoder and score two fixed non-legal passages. These first calls
can take materially longer than subsequent calls; `READINESS_TIMEOUT_SECONDS`
defaults to 60. See [BGE-M3 embedding capability](embedding-capability.md) and
[BGE reranker capability](reranker-capability.md).

Use `make api-with-model-capabilities` to enable both optional local checks.
The configured generation provider remains required, so set its model and
endpoint to a locally installed compatible model before expecting `/ready` to
return `200`. Each addition must document its timeout and configuration and add
a focused test before it becomes a configured default capability.

## Local verification

Run the deterministic readiness tests during development:

```bash
uv run pytest tests/unit/test_readiness.py -q
uv run pytest tests/integration/test_health.py -q
```

Run the complete deterministic gate before handoff:

```bash
make check
make audit
```

With Docker services healthy, exercise the real adapters explicitly:

```bash
make up
make migrate
RUN_REAL_INTEGRATION=1 uv run pytest tests/integration -m real_service -q
```

See [local service lifecycle](service-lifecycle.md) for volume preservation,
recovery, and the destructive reset confirmation required for each service.

For a manual HTTP check, start the API and query both endpoints:

```bash
make api
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/ready
```

The endpoint body is intentionally safe to display in a terminal. Do not add
credentials to a `curl` command or paste secrets into issue reports.

## Troubleshooting guide

| Observation | Interpretation | Safe next action |
| --- | --- | --- |
| `/health` does not return `200` | The process, route, or local configuration is broken. | Read local application logs; run the focused health test. |
| `/health` is `200`, `/ready` is `503` | The process is alive but a configured capability is unavailable. | Identify the failed capability by name; inspect that service's local status without printing credentials. |
| Both endpoints return `200` | Process and currently configured probes are healthy. | Continue with the relevant smoke or integration test; this is not an end-to-end RAG result. |
| A probe reports an unsafe detail | The diagnostic boundary has regressed. | Remove/redact the detail and add a deterministic regression test before sharing logs. |

## What changes later

When each later model dependency is introduced, readiness will gain a
configured capability probe. Each addition must document its timeout, safe
failure reason, configuration requirement, and focused integration test.
`/health` remains process-only throughout.
