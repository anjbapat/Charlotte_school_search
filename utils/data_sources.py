"""Official/public data access, isolated from Streamlit presentation code."""
from io import BytesIO, TextIOWrapper
from zipfile import ZipFile
import logging
import re
import pandas as pd
import requests
import streamlit as st
from .data_processing import normalize_cms_directory
NCES_CCD_URL="https://nces.ed.gov/ccd/Data/zip/ccd_sch_029_2425_w_0a_051425.zip"
CMS_DIRECTORY_URL="https://www.cmsk12.org/schools/all-schools"
CMS_BOUNDARY_URL="https://www.cmsk12.org/academics/planning-services/student-boundary-maps"
SCHOOL_LOCATIONS_LAYER="https://gis.charlottenc.gov/arcgis/rest/services/HNS/HousingLocationalToolLayers/MapServer/1"
NC_DPI_SRC_URLS=("https://www.dpi.nc.gov/src-data-set-2024-251-2/open","https://www.dpi.nc.gov/src-data-set-2024-252-2/open")
NC_DPI_SRC_LANDING_URL="https://www.dpi.nc.gov/data-reports/school-report-cards/school-report-card-resources-researchers"
def _result(available:bool,data=None,message:str="",**extra)->dict:return {"available":available,"data":data,"message":message,**extra}
@st.cache_data(ttl=3600,show_spinner="Retrieving public CMS school data…")
def get_cms_schools()->dict:
    try:
        response=requests.get(f"{SCHOOL_LOCATIONS_LAYER}/query",params={"where":"1=1","outFields":"*","returnGeometry":"true","outSR":"4326","f":"json"},timeout=45);response.raise_for_status()
        features=response.json().get("features",[])
        rows=[]
        for feature in features:
            attributes=feature.get("attributes",{});geometry=feature.get("geometry",{});ownership=str(attributes.get("Ownership","")).strip().title()
            magnet=str(attributes.get("Magnet","")).strip().lower()=="yes"
            school_type="Magnet" if magnet else "Traditional/Public" if ownership=="Public" else ownership if ownership in {"Private","Charter"} else "Other"
            raw_level=str(attributes.get("Type","")).strip().title()
            level=raw_level if raw_level in {"Elementary","Middle","High"} else "Other"
            rows.append({"school_id":attributes.get("SchoolID"),"school_name":attributes.get("Name"),"school_type":school_type,"school_level":level,"address":attributes.get("FULL_ADDRESS"),"city":"Mecklenburg County","state":"NC","zip_code":pd.NA,"latitude":geometry.get("y"),"longitude":geometry.get("x"),"grades_served":attributes.get("GradeLevel"),"phone":pd.NA,"website":pd.NA,"magnet": "Yes" if magnet else "No"})
        schools=pd.DataFrame(rows).dropna(subset=["school_name"])
        dedupe_key=schools.school_id.fillna("").astype(str)
        schools=schools.loc[~dedupe_key.where(dedupe_key.ne(""),schools.school_name.astype(str)+"|"+schools.latitude.astype(str)+"|"+schools.longitude.astype(str)).duplicated()]
        if schools.empty:return _result(False,message="The official directory did not contain CMS school records.")
        return _result(True,schools,source_url=SCHOOL_LOCATIONS_LAYER,cms_directory_url=CMS_DIRECTORY_URL,school_year="current GIS layer")
    except Exception:
        logging.exception("CMS directory retrieval failed");return _result(False,message="School data is temporarily unavailable. Please try again later.")
def get_school_boundaries()->dict:return _result(True,message="CMS publishes official 2026–27 attendance-boundary maps as map documents, not a verified public GIS polygon service.",source_url=CMS_BOUNDARY_URL)
def get_transportation_zones()->dict:return _result(True,message="CMS publishes official 2026–27 transportation-zone maps as map documents, not a verified public GIS polygon service.",source_url=CMS_BOUNDARY_URL)
def get_magnet_zones()->dict:return _result(False,message="A public CMS magnet-zone polygon dataset was not identified from the selected sources.")

def _normal_key(value:object)->str:return re.sub(r"[^a-z0-9]", "", str(value).lower())

def _pick_column(frame:pd.DataFrame, choices:tuple[str,...])->str|None:
    columns={_normal_key(column):column for column in frame.columns}
    return next((columns.get(_normal_key(choice)) for choice in choices if _normal_key(choice) in columns),None)

@st.cache_data(ttl=86400,show_spinner="Loading official NC School Report Card data (first load can take about a minute)…")
def get_nc_dpi_school_insights()->dict:
    """Read only DPI's statewide School Performance Grade workbook, not both ZIP archives."""
    try:
        response=requests.get(NC_DPI_SRC_URLS[0],timeout=(20,300));response.raise_for_status()
        with ZipFile(BytesIO(response.content)) as archive:
            filename=next(name for name in archive.namelist() if name.endswith("rcd_acc_spg1.xlsx"))
            with archive.open(filename) as file: frame=pd.read_excel(BytesIO(file.read()))
        # agency_code is the official NC public-school agency identifier. The GIS
        # layer uses the final three-character local CMS school code.
        latest_year=pd.to_numeric(frame["year"],errors="coerce").max()
        frame=frame.loc[pd.to_numeric(frame["year"],errors="coerce").eq(latest_year)&frame["subgroup"].eq("ALL")].copy()
        agency=frame["agency_code"].astype("string").str.replace(r"\.0$","",regex=True).str.zfill(6)
        insights=pd.DataFrame({"school_id":agency.str[-3:],"performance_grade":frame["spg_grade"].astype("string"),"performance_score":pd.to_numeric(frame["spg_score"],errors="coerce"),"growth":frame["eg_status"].astype("string"),"math_proficiency":pd.to_numeric(frame["ma_score"],errors="coerce"),"reading_proficiency":pd.to_numeric(frame["rd_score"],errors="coerce"),"graduation_rate":pd.to_numeric(frame["cgrs_score"],errors="coerce")})
        return _result(True,insights.drop_duplicates("school_id"),source_url=NC_DPI_SRC_LANDING_URL,school_year="2024-25")
    except Exception:
        logging.exception("NC DPI School Report Card retrieval failed")
        return _result(False,message="Official NC School Report Card data could not be loaded. The official statewide file is temporarily unavailable; please try again later.")
