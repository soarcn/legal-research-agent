"""Only source-native v1 section references are eligible for exact resolution."""

from legal_research.application.exact_reference import ExactReferenceResolver, ExactReferenceStatus
from legal_research.domain import SourcePassage


def _passage(passage_id: str) -> SourcePassage:
    return SourcePassage(
        source_snapshot_id="snapshot",
        passage_id=passage_id,
        title="title",
        text="text",
        footnotes=None,
        content_sha256="a" * 64,
    )


def test_resolves_source_section_id_and_all_its_source_chunks() -> None:
    result = ExactReferenceResolver().resolve(
        "section 8.1.2", (_passage("8.1.2-c1-s1"), _passage("8.1.3-c1-s1"))
    )
    assert result.status is ExactReferenceStatus.RESOLVED
    assert result.passage_ids == ("8.1.2-c1-s1",)


def test_reports_not_found_and_unsupported_without_inventing_legal_metadata() -> None:
    resolver = ExactReferenceResolver()
    assert (
        resolver.resolve("8.9", (_passage("8.1-c1-s1"),)).status is ExactReferenceStatus.NOT_FOUND
    )
    assert (
        resolver.resolve("Crimes Act 1958 s 322K", (_passage("8.1-c1-s1"),)).status
        is ExactReferenceStatus.UNSUPPORTED
    )
