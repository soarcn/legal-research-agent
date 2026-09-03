# Generation-provider configuration

P1.5 defined the configuration contract for one active generation provider.
P1.6 adds bounded HTTP adapters for the local Ollama API and the generic
OpenAI-compatible API. LM Studio is the reference runtime for validating the
latter. The adapters support plain text and caller-owned Pydantic JSON schemas;
they do not make legal answer generation available through the API.

## One active provider

The application has exactly one active provider configuration at a time. The
provider is selected explicitly; it is never inferred from the base URL.

| Field | Environment variable | Default | Meaning |
| --- | --- | --- | --- |
| Provider | `GENERATION_PROVIDER` | `ollama` | `ollama` or `openai_compatible` |
| Model | `GENERATION_MODEL` | `qwen3:8b` | Runtime model identifier |
| Base URL | `GENERATION_BASE_URL` | `http://localhost:11434` | Local runtime HTTP endpoint |
| API key | `GENERATION_API_KEY` | unset | Optional runtime credential |
| Timeout | `GENERATION_TIMEOUT_SECONDS` | `60` | Per-request timeout, greater than 0 and at most 300 seconds |
| Text generation | `GENERATION_SUPPORTS_TEXT_GENERATION` | `true` | Advertised capability flag |
| Structured output | `GENERATION_SUPPORTS_STRUCTURED_OUTPUT` | `false` | Advertised capability flag |
| Tool calling | `GENERATION_SUPPORTS_TOOL_CALLING` | `false` | Advertised capability flag |
| Streaming | `GENERATION_SUPPORTS_STREAMING` | `false` | Advertised capability flag |

`ollama` is the offline default. `openai_compatible` is the provider family
used to validate portability with LM Studio later in P1.6. These flags declare
configuration intent only; a later capability smoke test must verify them
against the configured runtime.

## Examples

Default local Ollama configuration needs no generation environment variables:

```dotenv
GENERATION_PROVIDER=ollama
GENERATION_MODEL=qwen3:8b
GENERATION_BASE_URL=http://localhost:11434
GENERATION_TIMEOUT_SECONDS=60
```

An LM Studio-compatible local endpoint is an explicit switch:

```dotenv
GENERATION_PROVIDER=openai_compatible
GENERATION_MODEL=local-qwen
GENERATION_BASE_URL=http://localhost:1234/v1
GENERATION_TIMEOUT_SECONDS=60
GENERATION_SUPPORTS_STRUCTURED_OUTPUT=true
```

## Safe configuration rules

- Only `ollama` and `openai_compatible` are accepted provider values.
- Model names and configured API keys cannot be blank.
- Base URLs must be absolute `http` or `https` URLs. Embedded credentials,
  query parameters, and fragments are rejected so credentials cannot be hidden
  in a URL or accidentally logged.
- API keys are stored as Pydantic `SecretStr` values and are redacted in model
  representations. Keep them in a local `.env` file or shell environment;
  never commit them or include them in diagnostics.
- A base URL does not prove that its provider is reachable or supports a flag.
  P1.6 will test text and structured-output capability through the provider
  contract.

The typed application-facing objects are `GenerationProvider`,
`GenerationCapabilities`, and `GenerationProviderConfig`. Adapters receive a
`GenerationProviderConfig`; application code must not read provider-specific
environment variables directly. An adapter is constructed with that one active
configuration and owns its model choice. Generation requests never carry a
per-request model identifier, so callers cannot bypass the configured model;
responses record the adapter's configured model for audit later.

## Readiness composition

The application composition root accepts at most one active generation adapter
and wraps it in a provider-neutral `generation` capability probe. The probe
uses the selected `GenerationProviderConfig` and maps only its status into the
shared readiness result; an inactive provider is never constructed or checked.

The default application's real `/ready` report constructs only the selected
adapter and checks whether its configured model is visible. It never performs
generation as part of readiness. Transport, timeout, rate-limit, rejected
request, malformed response, and schema-validation failures are translated to
the provider-neutral result contract without returning endpoint payloads or
exceptions.

## Explicit capability smoke tests

These opt-in commands run one non-legal plain-text prompt and one fixed JSON
schema prompt. They write a redacted local report under
`artifacts/capability-reports/`, which is not committed. A passing report
proves only this configured model/provider combination answered those two
requests; it does not prove legal answer quality, citation reliability, or
future model behaviour.

```bash
# Select a model visible in `ollama list`.
GENERATION_MODEL=gpt-oss:20b make generation-smoke-ollama

# Start an LM Studio local server, load a text-generation model, then use its
# model identifier from GET /v1/models.
GENERATION_MODEL=your-lm-studio-model make generation-smoke-lm-studio
```

The smoke test fails safely when the configured model is not visible. This is
expected when no model has been installed in Ollama or loaded into LM Studio;
it is not a signal to download a model automatically.

Some local reasoning models expose a JSON-schema-constrained object through
`reasoning_content` while returning an empty normal content field. For a
structured request only, the adapter may validate that field directly against
the caller's schema when normal content is empty. It never uses that fallback
for plain text and never records, returns, or exposes the raw field.
