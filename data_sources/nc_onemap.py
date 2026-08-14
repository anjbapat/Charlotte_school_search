"""NC OneMap ArcGIS FeatureServer client for public-school geography."""

from __future__ import annotations

import os

import pandas as pd

from .http import build_session, get
from .models import DataSourceError, DatasetResult, SourceMetadata


class NCOneMapClient:
    def __init__(self, layer_url: str | None = None, session=None) -> None:
        self.layer_url = (layer_url or os.getenv("NC_ONEMAP_SCHOOLS_LAYER_URL", "")).rstrip("/")
        self.session = session or build_session()

    def school_locations(self) -> DatasetResult:
        if not self.layer_url:
            raise DataSourceError("NC_ONEMAP_SCHOOLS_LAYER_URL is required and must be a public-school ArcGIS FeatureServer/MapServer layer URL.")
        query_url = f"{self.layer_url}/query"
        params = {"where": "1=1", "outFields": "*", "returnGeometry": "true", "f": "json", "resultRecordCount": 2000}
        payload = get(self.session, query_url, params=params).json()
        if "error" in payload:
            raise DataSourceError(f"NC OneMap query error: {payload['error']}")
        rows = []
        for feature in payload.get("features", []):
            row = dict(feature.get("attributes", {}))
            geometry = feature.get("geometry", {})
            row["latitude"] = geometry.get("y")
            row["longitude"] = geometry.get("x")
            rows.append(row)
        return DatasetResult(pd.DataFrame(rows), SourceMetadata.create("NC OneMap", "Public schools GIS layer", self.layer_url))
