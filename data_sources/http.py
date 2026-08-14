"""HTTP primitives with timeouts, retries, and format-aware tabular parsing."""

from __future__ import annotations

from io import BytesIO, StringIO

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import DataSourceError


def build_session() -> requests.Session:
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET",))
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "NC-School-Search-AI/0.1 (official-data-client)"})
    return session


def get(session: requests.Session, url: str, *, params: dict | None = None, timeout: int = 30) -> requests.Response:
    try:
        response = session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.RequestException as exc:
        raise DataSourceError(f"Official data request failed for {url}: {exc}") from exc


def read_table(response: requests.Response) -> pd.DataFrame:
    content_type = response.headers.get("content-type", "").lower()
    url = response.url.lower()
    try:
        if "json" in content_type or url.endswith(".json"):
            payload = response.json()
            return pd.json_normalize(payload.get("results", payload) if isinstance(payload, dict) else payload)
        if any(marker in content_type for marker in ("excel", "spreadsheet")) or url.endswith((".xlsx", ".xls")):
            return pd.read_excel(BytesIO(response.content))
        return pd.read_csv(StringIO(response.text))
    except (ValueError, UnicodeDecodeError) as exc:
        raise DataSourceError(f"Could not parse the official dataset at {response.url}.") from exc
