"""School-selection and comparison presentation, independent from the map."""
import re
import pandas as pd
import streamlit as st
from utils.data_sources import get_nc_dpi_school_insights

NICHE_SCHOOL_NAME_OVERRIDES = {
    "butler high school": "David W Butler High School",
    "butler high": "David W Butler High School",
    "butler": "David W Butler High School",
}

def _niche_school_name(school_name:str,school_level:str|None)->str:
    name=str(school_name).strip()
    lower=name.lower()
    if lower in NICHE_SCHOOL_NAME_OVERRIDES:
        return NICHE_SCHOOL_NAME_OVERRIDES[lower]
    if any(token in lower for token in ("school","academy","institute")):
        return name
    if lower.endswith(("elementary","middle","high")):
        return f"{name} School"
    level=str(school_level or "").lower()
    if "middle" in level:
        return f"{name} Middle School"
    if "high" in level:
        return f"{name} High School"
    if "elementary" in level or "k-8" in level:
        return f"{name} Elementary School"
    return f"{name} School"

def _niche_slug(value:str)->str:
    normalized=str(value).lower().replace("&"," and ")
    return re.sub(r"[^a-z0-9]+","-",normalized).strip("-")

def _niche_city(school:pd.Series)->str:
    city=str(school.get("city") or "").strip()
    if city and city.lower() not in {"mecklenburg county", "county"}:
        return city
    address=str(school.get("address") or "")
    match=re.search(
        r"\b(CHARLOTTE|CORNELIUS|DAVIDSON|HUNTERSVILLE|MATTHEWS|MINT HILL|PINEVILLE)\s+NC\b",
        address,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).title()
    return "Charlotte"

def _niche_school_url(school:pd.Series)->str:
    name=_niche_school_name(school["school_name"],school.get("school_level"))
    city=_niche_city(school)
    state=str(school.get("state") or "NC").strip() or "NC"
    return f"https://www.niche.com/k12/{_niche_slug(f'{name} {city} {state}')}/"

def render_school_compare(schools:pd.DataFrame)->None:
    st.subheader("Compare Schools")
    st.caption("Select two to four schools. Academic data is from the official NC DPI 2024–25 School Report Cards; Niche links open Niche directly and do not copy its ratings or rankings.")
    selected=st.multiselect("Schools to compare",schools.school_name.sort_values().tolist(),max_selections=4,placeholder="Select 2–4 schools")
    if not selected:
        st.info("Select at least two schools to begin a comparison.");return
    if len(selected)<2:
        st.warning("Select one more school to compare.");return
    chosen=schools.loc[schools.school_name.isin(selected)].copy()
    insights_result=get_nc_dpi_school_insights()
    if insights_result["available"]:
        insights=insights_result["data"].copy()
        chosen["school_id"]=chosen.school_id.astype("string").str.zfill(3);chosen=chosen.merge(insights,on="school_id",how="left")
        st.caption(f"Official academic source: NC DPI School Report Cards, {insights_result['school_year']}. Private schools may not have an NC Report Card.")
    else:
        st.warning(insights_result["message"])
    fields=[("School", "school_name"),("Type","school_type"),("Level","school_level"),("Grades","grades_served"),("School Performance Grade","performance_grade"),("School Performance Score","performance_score"),("Growth","growth"),("Math Proficiency (%)","math_proficiency"),("Reading Proficiency (%)","reading_proficiency"),("Graduation Rate (%)","graduation_rate")]
    rows=[]
    for label,field in fields:
        if field in chosen and chosen[field].notna().any():rows.append([label]+[chosen.loc[chosen.school_name.eq(name),field].iloc[0] for name in selected])
    st.dataframe(pd.DataFrame(rows,columns=["Metric"]+selected),hide_index=True,use_container_width=True)
    st.caption("NC DPI performance grades are official state accountability grades—not a recommendation or rating.")
    links=st.columns(len(selected))
    for column,name in zip(links,selected):
        school=chosen.loc[chosen.school_name.eq(name)].iloc[0]
        column.link_button(f"View {name} on Niche",_niche_school_url(school),use_container_width=True)
