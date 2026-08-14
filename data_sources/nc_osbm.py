"""NC OSBM LINC API client for optional county/district context metrics."""

from __future__ import annotations

import pandas as pd

from .http import build_session, get
from .models import DatasetResult, SourceMetadata

BASE_URL = "https://linc.osbm.nc.gov/api/explore/v2.1/catalog/datasets/education/records"


class NCOSBMClient:
    def __init__(self, session=None) -> None:
        self.session = session or build_session()

    def education_context(self, *, limit: int = 100, year: int | None = None) -> DatasetResult:
        params = {"limit": limit}
        if year:
            params["where"] = f"year = '{year}'"
        payload = get(self.session, BASE_URL, params=params).json()
        return DatasetResult(pd.json_normalize(payload.get("results", [])), SourceMetadata.create("NC OSBM", "LINC Education", BASE_URL, str(year) if year else None, "historical"))
