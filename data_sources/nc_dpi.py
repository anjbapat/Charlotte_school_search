"""NC DPI EDDIE and accountability clients.

URLs deliberately live in environment variables: DPI publishes reports through
its portal and can change an export URL without changing this application.
"""

from __future__ import annotations

import os
from io import BytesIO, TextIOWrapper
from zipfile import ZipFile

import pandas as pd

from .http import build_session, get, read_table
from .models import DataSourceError, DatasetResult, SourceMetadata

EDDIE_LANDING_URL = "https://www.dpi.nc.gov/districts-schools/district-operations/financial-and-business-services/demographics-and-finances/eddie"
REPORT_CARD_URL = "https://ncfvapublicprod.ondemand.sas.com/src/"
NCES_CCD_2024_25_URL = "https://nces.ed.gov/ccd/Data/zip/ccd_sch_029_2425_w_0a_051425.zip"


class NCDPIClient:
    def __init__(self, session=None) -> None:
        self.session = session or build_session()

    def school_directory(self) -> DatasetResult:
        url = os.getenv("NC_DPI_EDDIE_EXPORT_URL")
        if url:
            response = get(self.session, url)
            return DatasetResult(read_table(response), SourceMetadata.create("NC DPI", "EDDIE school directory", url))
        # EDDIE's public report exports are generated URLs, not a stable API. NCES
        # CCD is an official U.S. Department of Education directory fallback and
        # lets a first-run application function without manual configuration.
        response = get(self.session, NCES_CCD_2024_25_URL, timeout=90)
        try:
            with ZipFile(BytesIO(response.content)) as archive:
                csv_name = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
                with archive.open(csv_name) as csv_file:
                    directory = pd.read_csv(TextIOWrapper(csv_file, encoding="latin-1"), low_memory=False)
        except (KeyError, ValueError, UnicodeDecodeError, OSError) as exc:
            raise DataSourceError("Could not parse the NCES CCD directory fallback.") from exc
        north_carolina = directory.loc[directory["FIPST"].astype(str).str.zfill(2).eq("37")].copy()
        return DatasetResult(
            self._prepare_nces_directory(north_carolina),
            SourceMetadata.create("NCES / U.S. Department of Education", "CCD preliminary public-school directory", NCES_CCD_2024_25_URL, "2024-25", "historical"),
        )

    @staticmethod
    def _prepare_nces_directory(frame: pd.DataFrame) -> pd.DataFrame:
        """Expose CCD headers in the application's canonical-source vocabulary."""
        prepared = frame.rename(columns={
            "NCESSCH": "NCES ID", "SCH_NAME": "School Name", "LEA_NAME": "LEA Name",
            "LSTREET1": "Address", "LCITY": "City", "LZIP": "ZIP", "SCH_TYPE_TEXT": "School Type",
            "CHARTER_TEXT": "Charter", "LATCOD": "Latitude", "LONCOD": "Longitude",
        }).copy()
        grade_columns = [("PK", "G_PK_OFFERED"), ("K", "G_KG_OFFERED")] + [(str(grade), f"G_{grade:02d}_OFFERED") for grade in range(1, 13)]
        available = [(label, column) for label, column in grade_columns if column in prepared]
        prepared["Grades"] = prepared.apply(lambda row: ", ".join(label for label, column in available if str(row[column]).upper() in {"YES", "1", "Y"}), axis=1)
        return prepared

    def accountability(self) -> DatasetResult:
        url = os.getenv("NC_DPI_ACCOUNTABILITY_URL")
        if not url:
            raise DataSourceError("NC_DPI_ACCOUNTABILITY_URL is not configured; accountability metrics will be unavailable.")
        response = get(self.session, url)
        year = os.getenv("NC_DPI_ACCOUNTABILITY_SCHOOL_YEAR")
        return DatasetResult(read_table(response), SourceMetadata.create("NC DPI", "School Report Cards / accountability", url, year, "historical"))
