"""Selected-school details panel."""
import pandas as pd
import streamlit as st
def render_school_details(school:pd.Series)->None:
    st.subheader(school.school_name)
    for label,field in (("School type","school_type"),("Level","school_level"),("Grades","grades_served"),("Address","address"),("Phone","phone")):
        value=school.get(field)
        if pd.notna(value) and str(value).strip():st.write(f"**{label}:** {value}")
    if pd.notna(school.get("distance_miles")):st.write(f"**Approximate straight-line distance from home:** {school.distance_miles:.1f} miles")
    website=school.get("website")
    if pd.notna(website) and str(website).startswith("http"):st.link_button("Official school website",website)
