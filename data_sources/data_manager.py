"""Assemble official datasets into a validated canonical school table.

The manager contains no Streamlit dependency, keeping fetch/caching policy usable
from a CLI, scheduled refresh, tests, or a future web UI.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from .models import DataSourceError, DatasetResult, SourceMetadata
from .nc_dpi import NCDPIClient
from .nc_onemap import NCOneMapClient

CANONICAL_COLUMNS = [
    "school_id", "nces_id", "school_name", "district_name", "county", "city", "address",
    "zip_code", "school_type", "charter", "grades", "enrollment", "latitude", "longitude",
    "math_proficiency", "reading_proficiency", "graduation_rate", "student_teacher_ratio",
    "school_performance_score", "school_performance_grade", "growth",
]

ALIASES = {
    "school_id": ("school_id", "school number", "school_number", "schoolcode", "school code"),
    "nces_id": ("nces_id", "nces school id", "ncesschid", "ncessch"),
    "school_name": ("school_name", "school name", "school"),
    "district_name": ("district_name", "lea name", "lea_name", "district", "psu name"),
    "county": ("county", "county name"), "city": ("city", "mail city"),
    "address": ("address", "street address", "physical address"), "zip_code": ("zip", "zip code", "zipcode"),
    "school_type": ("school type", "school_type", "type"), "charter": ("charter", "is_charter"),
    "grades": ("grades", "grade span", "grade_span"), "enrollment": ("enrollment", "student enrollment"),
    "latitude": ("latitude", "lat"), "longitude": ("longitude", "lon", "long"),
    "math_proficiency": ("math proficiency", "math_proficiency", "math percent proficient"),
    "reading_proficiency": ("reading proficiency", "reading_proficiency", "ela proficiency"),
    "graduation_rate": ("graduation rate", "graduation_rate"),
    "student_teacher_ratio": ("student teacher ratio", "student_teacher_ratio"),
    "school_performance_score": ("school performance score", "school_performance_score", "performance score"),
    "school_performance_grade": ("school performance grade", "school_performance_grade", "performance grade"),
    "growth": ("growth", "growth status"),
}
NUMERIC_COLUMNS = {"enrollment", "latitude", "longitude", "math_proficiency", "reading_proficiency", "graduation_rate", "student_teacher_ratio", "school_performance_score"}


def _key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def normalize_school_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Map source-specific headers to stable fields and apply quality safeguards."""
    source_by_key = {_key(column): column for column in frame.columns}
    result = pd.DataFrame(index=frame.index)
    for canonical in CANONICAL_COLUMNS:
        source = next((source_by_key.get(_key(alias)) for alias in ALIASES[canonical] if _key(alias) in source_by_key), None)
        result[canonical] = frame[source] if source else pd.NA
    for column in NUMERIC_COLUMNS:
        result[column] = pd.to_numeric(result[column].astype("string").str.replace("%", "", regex=False), errors="coerce")
    result["school_id"] = result["school_id"].astype("string").str.replace(r"\.0$", "", regex=True).str.strip()
    result["nces_id"] = result["nces_id"].astype("string").str.replace(r"\.0$", "", regex=True).str.strip()
    result["charter"] = result["charter"].astype("string").str.lower().isin({"yes", "true", "y", "1"})
    valid_geo = result.latitude.between(33, 37) & result.longitude.between(-85, -75)
    result.loc[~valid_geo, ["latitude", "longitude"]] = pd.NA
    result = result.dropna(subset=["school_name"])
    # Stable state IDs are preferred; name/district is only a conservative fallback.
    dedupe_key = result.school_id.where(result.school_id.notna() & result.school_id.ne("<NA>"), result.school_name.astype("string") + "|" + result.district_name.astype("string"))
    return result.loc[~dedupe_key.duplicated()].reset_index(drop=True)


@dataclass(slots=True)
class SchoolData:
    schools: pd.DataFrame
    metadata: list[SourceMetadata]
    warnings: list[str]


class DataManager:
    def __init__(self, dpi: NCDPIClient | None = None, onemap: NCOneMapClient | None = None) -> None:
        self.dpi, self.onemap = dpi or NCDPIClient(), onemap or NCOneMapClient()

    def load_schools(self, *, include_accountability: bool = True, include_geography: bool = True) -> SchoolData:
        directory = self.dpi.school_directory()
        schools = normalize_school_frame(directory.data)
        metadata, warnings = [directory.metadata], []
        for label, enabled, loader in (
            ("accountability", include_accountability, self.dpi.accountability),
            ("NC OneMap geography", include_geography, self.onemap.school_locations),
        ):
            if not enabled:
                continue
            try:
                dataset = loader()
                schools = self._merge(schools, normalize_school_frame(dataset.data))
                metadata.append(dataset.metadata)
            except DataSourceError as exc:
                warnings.append(f"{label} unavailable: {exc}")
        return SchoolData(schools=schools, metadata=metadata, warnings=warnings)

    @staticmethod
    def _merge(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
        if right.empty:
            return left
        keys = [key for key in ("school_id", "nces_id") if left[key].notna().any() and right[key].notna().any()]
        if not keys:
            return left
        merged = left.merge(right, on=keys, how="left", suffixes=("", "_incoming"))
        for column in CANONICAL_COLUMNS:
            incoming = f"{column}_incoming"
            if incoming in merged:
                merged[column] = merged[column].combine_first(merged[incoming])
                merged.drop(columns=incoming, inplace=True)
        return merged[CANONICAL_COLUMNS]
