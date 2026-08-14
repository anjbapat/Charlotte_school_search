"""Testable school-filtering UI and logic."""
import pandas as pd
import streamlit as st
def filter_schools(schools:pd.DataFrame,levels:list[str],school_types:list[str])->pd.DataFrame:
    result=schools.copy()
    if levels:result=result[result.school_level.isin(levels)]
    if school_types:result=result[result.school_type.isin(school_types)]
    return result
def render_filters(schools:pd.DataFrame)->tuple[list[str],list[str]]:
    st.subheader("Filters");first,second=st.columns(2)
    levels=first.multiselect("School Level",sorted(schools.school_level.dropna().unique().tolist()),placeholder="All levels")
    types=second.multiselect("School Type",sorted(schools.school_type.dropna().unique().tolist()),placeholder="All school types")
    return levels,types
