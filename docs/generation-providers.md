# Generation-provider configuration

P1.5 defines the configuration contract for one active generation provider.
It does not connect to a model runtime, download a model, or make generation
available through the API. Those capability checks are P1.6 work.

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

P1.5 deliberately does not construct a network adapter from configuration.
The fake provider proves the contract deterministically. P1.6 supplies the
Ollama or OpenAI-compatible adapter to this seam, at which point the active
provider becomes part of the default application's real `/ready` report.
