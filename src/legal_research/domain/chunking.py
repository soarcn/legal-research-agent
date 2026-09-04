"""Future-source section and derived-passage contracts, separate from v1 facts."""

from __future__ import annotations

from pydantic import Field, field_validator

from legal_research.domain.models import DomainModel


class FutureSourceSection(DomainModel):
    """One structured section from a source that supplies section metadata."""

    source_snapshot_id: str = Field(min_length=1)
    document_version_id: str = Field(min_length=1)
    section_path: tuple[str, ...] = Field(min_length=1)
    text: str = Field(min_length=1)

    @field_validator("section_path")
    @classmethod
    def section_path_must_not_contain_blank_parts(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("section paths cannot contain blank parts")
        return value


class DerivedPassage(DomainModel):
    """A deterministic subsection of one future source section."""

    source_snapshot_id: str = Field(min_length=1)
    passage_id: str = Field(min_length=1)
    parent_section_id: str = Field(min_length=1)
    section_path: tuple[str, ...] = Field(min_length=1)
    text: str = Field(min_length=1)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("section_path")
    @classmethod
    def section_path_must_not_contain_blank_parts(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("section paths cannot contain blank parts")
        return value
