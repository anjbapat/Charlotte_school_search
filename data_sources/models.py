"""Small, UI-independent contracts shared by data-source clients."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import pandas as pd


class DataSourceError(RuntimeError):
    """Raised when an upstream official data source cannot be used safely."""


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    source: str
    dataset: str
    school_year: str | None
    source_url: str
    retrieved_at: str
    refresh_type: str

    @classmethod
    def create(
        cls, source: str, dataset: str, source_url: str, school_year: str | None = None,
        refresh_type: str = "current",
    ) -> "SourceMetadata":
        return cls(source, dataset, school_year, source_url, datetime.now(UTC).isoformat(), refresh_type)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DatasetResult:
    data: pd.DataFrame
    metadata: SourceMetadata
