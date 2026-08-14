"""Charlotte School Search — the Streamlit entry point."""
from __future__ import annotations
import logging
import streamlit as st
from components.school_details import render_school_details
from components.school_compare import render_school_compare
from components.school_filters import filter_schools, render_filters
from components.school_map import render_school_map
from utils.data_sources import get_cms_schools, get_school_boundaries, get_transportation_zones
from utils.distance import add_distances
from utils.geocoding import geocode_address, is_likely_cms_area

logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="Charlotte School Search", page_icon="🏫", layout="wide")

def _find_address(address: str) -> None:
    result = geocode_address(address)
    if not result["ok"]:
        st.session_state.pop("home", None)
        st.error("We couldn't find that address. Please enter a complete Charlotte-area address.")
        return
    st.session_state.home = result
    if not is_likely_cms_area(result["latitude"], result["longitude"]):
        st.warning("This address appears to be outside the Charlotte-Mecklenburg Schools area. You can still explore schools.")

def render_find_schools() -> None:
    st.title("Charlotte School Search")
    st.caption("Find schools near your home and explore school types and zones.")
    with st.form("address_form"):
        left, right = st.columns([5, 1])
        address = left.text_input("Home Address", placeholder="123 Main St, Charlotte, NC")
        submitted = right.form_submit_button("Find Schools", use_container_width=True)
    if submitted: _find_address(address)
    try: schools_result = get_cms_schools()
    except Exception:
        logging.exception("CMS school retrieval failed")
        st.error("School data is temporarily unavailable. Please try again later.")
        return
    if not schools_result["available"]:
        st.error(schools_result["message"]); return
    schools = schools_result["data"]
    left, right = st.columns([1, 2])
    with left:
        levels, school_types = render_filters(schools)
        st.caption("Choose one or more school levels and types. Leave filters empty to show all nearby schools.")
    visible = filter_schools(schools, levels, school_types)
    home = st.session_state.get("home")
    if home: visible = add_distances(visible, home["latitude"], home["longitude"]).sort_values("distance_miles", na_position="last")
    else: visible = visible.sort_values("school_name")
    with right: render_school_map(visible, home, get_school_boundaries(), get_transportation_zones())
    with left: st.subheader(f"School results ({len(visible)})")
    columns = ["school_name", "school_level", "school_type", "address", "grades_served"]
    if "distance_miles" in visible: columns.insert(3, "distance_miles")
    table = visible[columns].rename(columns={"school_name":"School", "school_level":"Level", "school_type":"Type", "address":"Address", "grades_served":"Grades", "distance_miles":"Approx. distance (miles)"})
    with left: st.dataframe(table, hide_index=True, use_container_width=True, height=340, column_config={"Approx. distance (miles)": st.column_config.NumberColumn(format="%.1f")})
    if not home: left.caption("Enter a home address to see approximate straight-line distances, sorted closest first.")
    if visible.empty:
        st.info("No CMS schools match these filters. Try changing a filter."); return
    with left:
        selected_name = st.selectbox("Select a school for details", visible["school_name"].tolist())
        render_school_details(visible.loc[visible.school_name.eq(selected_name)].iloc[0])

def main() -> None:
    find_tab, compare_tab = st.tabs(["Find Schools", "Compare Schools"])
    with find_tab:
        render_find_schools()
    with compare_tab:
        try:
            schools_result=get_cms_schools()
            if not schools_result["available"]: st.error(schools_result["message"])
            else: render_school_compare(schools_result["data"])
        except Exception:
            logging.exception("Comparison school retrieval failed")
            st.error("School data is temporarily unavailable. Please try again later.")

if __name__ == "__main__": main()
