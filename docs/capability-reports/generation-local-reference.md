# Local generation capability reference report

**Report schema:** `1`  
**Run date:** 2026-09-03  
**Implementation commit:** `cc46244ef22a52d19c2871d56f708d34d7b268eb`  
**Reference platform:** macOS Apple Silicon, M5 Max, 48 GB unified memory

## Result

Both P1.6 non-legal capability checks passed. Each provider first confirmed the
configured model was visible through its read-only model-list endpoint, then
completed one plain-text request and one Pydantic JSON-schema request. The
local JSON artifacts are ignored by Git; they omit raw model output, legal
source data, credentials, and endpoint exceptions.

| Provider family | Runtime / model | Text latency | Structured latency | Result |
| --- | --- | ---: | ---: | --- |
| Ollama | `gpt-oss:20b` | 21,379.70 ms | 927.86 ms | Passed |
| OpenAI-compatible (LM Studio) | `qwen/qwen3.5-9b` | 6,090.70 ms | 237.10 ms | Passed |

The Ollama test used `http://localhost:11434/api/chat`. The LM Studio test used
`http://localhost:1234/v1/chat/completions`. Both runs used a 60-second
request timeout and advertised plain-text and structured-output capability.

## LM Studio compatibility observation

The tested LM Studio Qwen reasoning model placed its schema-constrained JSON in
`reasoning_content` and returned an empty normal content field. The adapter
accepts this only for a structured request when the normal content field is
empty, immediately validates it against the caller's schema, and discards the
raw field. It is never used for plain-text generation, returned to callers, or
persisted as a trace.

## Interpretation

This demonstrates the configured local provider/model combinations can answer
two bounded non-legal requests through the project contract. It does not
demonstrate legal-answer correctness, citation support, tool use, retrieval
quality, stable performance, or suitability of either model as the project's
future default.
