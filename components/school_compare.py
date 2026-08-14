"""School-selection and comparison presentation, independent from the map."""
from urllib.parse import quote_plus
import pandas as pd
import streamlit as st
from utils.data_sources import get_nc_dpi_school_insights

def _niche_search_url(school_name:str)->str:
    return f"https://www.niche.com/k12/search/best-schools/?q={quote_plus(school_name + ' Charlotte NC')}"

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
    for column,name in zip(links,selected):column.link_button(f"View {name} on Niche",_niche_search_url(name),use_container_width=True)
