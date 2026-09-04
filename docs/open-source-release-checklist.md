# Open-source release checklist

The repository remains private until every applicable item is complete.

## Legal and licensing

- [ ] Apache License 2.0 text is present.
- [ ] `NOTICE` and third-party dependency/model/data attribution are complete.
- [ ] [Licence register](licence-register.md) has been rechecked against every selected upstream revision.
- [ ] Legal RAG Bench licence discrepancy is resolved or clearly documented under the stricter policy.
- [ ] No raw or derived dataset content is redistributed contrary to its terms.
- [ ] Model weights and caches are absent from the repository.

## Security and privacy

- [ ] Full-history secret scan passes.
- [ ] `.env`, keys, tokens, local endpoints, and credentials are absent.
- [ ] Dependency and container baseline scans are reviewed.
- [ ] Logs and committed examples contain no personal, privileged, or sensitive data.
- [ ] Agent tools and network boundaries match the documented security model.

## Reproducibility and quality

- [ ] Setup works from a clean macOS Apple Silicon environment.
- [ ] Dataset download verifies pinned revision, counts, and hashes.
- [ ] Index rebuild produces documented stable results.
- [ ] Deterministic CI tests pass.
- [ ] Published benchmark configuration and summary are reproducible.
- [ ] No formal result is presented as production/legal correctness.

## Documentation

- [ ] README, architecture, ADRs, data/licence, risks, known limitations, and demo are current.
- [ ] The offline default and optional LM Studio/OpenAI-compatible path are clear.
- [ ] Research-assistance/non-legal-advice positioning is prominent.
- [ ] Supported platform and 100 GB resource boundary are clear.
