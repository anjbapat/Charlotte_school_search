"""Natural-language school advisor backed by the existing school service."""
from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from utils.distance import add_distances


LEVEL_TERMS = {
    "elementary": "Elementary",
    "middle": "Middle",
    "high": "High",
    "k-8": "K-8",
    "k8": "K-8",
}
TYPE_TERMS = {
    "magnet": "Magnet",
    "charter": "Charter",
    "private": "Private",
    "traditional": "Traditional/Public",
    "public": "Traditional/Public",
}


def query_schools(
    schools: pd.DataFrame, question: str, home: dict | None = None
) -> tuple[pd.DataFrame, list[str]]:
    """Interpret supported phrases and query the canonical school DataFrame."""
    text = question.lower().strip()
    result = schools.copy()
    understood: list[str] = []

    levels = [value for term, value in LEVEL_TERMS.items() if re.search(rf"\b{re.escape(term)}\b", text)]
    levels = list(dict.fromkeys(levels))
    if levels:
        result = result[result["school_level"].isin(levels)]
        understood.append("level: " + ", ".join(levels))

    types = [value for term, value in TYPE_TERMS.items() if re.search(rf"\b{term}\b", text)]
    types = list(dict.fromkeys(types))
    if types:
        if "Magnet" in types and "magnet" in result:
            result = result[result["magnet"].astype("string").str.lower().eq("yes")]
        else:
            result = result[result["school_type"].isin(types)]
        understood.append("type: " + ", ".join(types))

    wants_nearby = bool(re.search(r"\b(near me|nearby|closest|nearest)\b", text))
    if home:
        result = add_distances(result, home["latitude"], home["longitude"])
        result = result.sort_values("distance_miles", na_position="last")
        if wants_nearby:
            understood.append("sorted by distance from your home")
    else:
        result = result.sort_values("school_name")
        if wants_nearby:
            understood.append("nearby requested; home address needed for distance sorting")

    return result.reset_index(drop=True), understood


def render_school_advisor(schools: pd.DataFrame, home: dict | None) -> None:
    st.title("AI School Advisor")
    st.caption("Ask in everyday language. Answers query the same CMS school data used elsewhere in this app.")
    question = st.text_input(
        "What would you like to know?",
        placeholder="Which elementary schools near me offer a magnet program?",
    )
    if not question:
        st.info("Try: “Which elementary schools near me offer a magnet program?”")
        return

    results, understood = query_schools(schools, question, home)
    if understood:
        st.caption("Interpreted as: " + "; ".join(understood) + ".")
    else:
        st.warning("I couldn't identify a level or school type, so I'm showing all schools. Try terms such as elementary, middle, high, magnet, charter, or private.")
    if not home and re.search(r"\b(near me|nearby|closest|nearest)\b", question.lower()):
        st.info("Enter your address in the Find Schools tab so I can sort these results by proximity.")
    if results.empty:
        st.info("No schools in the current CMS data match that question.")
        return

    st.subheader(f"I found {len(results)} matching school{'s' if len(results) != 1 else ''}")
    columns = ["school_name", "school_level", "school_type", "address", "grades_served"]
    if "distance_miles" in results:
        columns.insert(3, "distance_miles")
    table = results[columns].rename(columns={
        "school_name": "School", "school_level": "Level", "school_type": "Type",
        "distance_miles": "Approx. distance (miles)", "address": "Address", "grades_served": "Grades",
    })
    st.dataframe(table, hide_index=True, use_container_width=True,
                 column_config={"Approx. distance (miles)": st.column_config.NumberColumn(format="%.1f")})
