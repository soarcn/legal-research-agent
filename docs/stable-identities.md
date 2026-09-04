# Stable identity rules

The v1 benchmark keeps the source-provided passage ID unchanged. A persistence
key scopes it with `source_snapshot_id`, so the same native ID in a later source
snapshot cannot collide. No text is re-chunked or renamed for v1 scoring.

Future sources use deterministic UUIDv5 identities with a fixed project
namespace:

```text
document          = source authority + canonical citation
document version  = document ID + source-content SHA-256
section           = document-version ID + complete section path
derived passage   = section ID + validated offsets + content SHA-256
```

Retrieval time, model choice, and legal effective date are never identity
inputs. A content change creates a new document version. Identical text in two
different sections remains distinct because its parent section identity differs.

UUIDv5 collisions are treated as cryptographically negligible for this learning
project. If an upstream canonical citation changes, preserve the old source
snapshot and introduce an explicit supersession relation in the later database
schema; do not rewrite existing IDs.
