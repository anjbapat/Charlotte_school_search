"""Natural-language school advisor backed by the existing school service."""
from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from utils.data_sources import get_nc_dpi_school_insights
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
RANKING_TERMS = {
    "performance_grade": (
        "school performance grade", "performance grade", "spg grade", "grade",
        "best", "top", "highest performing",
    ),
    "performance_score": ("school performance score", "performance score", "spg score"),
    "math_proficiency": ("math proficiency", "math", "math scores"),
    "reading_proficiency": ("reading proficiency", "reading", "ela", "english"),
    "graduation_rate": ("graduation rate", "graduation"),
}
GRADE_RANK = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


def _requested_limit(text: str) -> int | None:
    match = re.search(r"\b(?:top|best|first)\s+(\d{1,2})\b", text)
    if match:
        return max(1, int(match.group(1)))
    match = re.search(r"\b(\d{1,2})\s+(?:top|best|highest|leading)\b", text)
    if match:
        return max(1, int(match.group(1)))
    return None


def _requested_ranking(text: str) -> str | None:
    for field, terms in RANKING_TERMS.items():
        if any(re.search(rf"\b{re.escape(term)}\b", text) for term in terms):
            return field
    return None


def _merge_school_insights(result: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    if "school_id" not in result:
        return result, "School Performance Grade data needs school IDs, which are missing from this data."
    insights_result = get_nc_dpi_school_insights()
    if not insights_result["available"]:
        return result, insights_result["message"]
    insights = insights_result["data"].copy()
    merged = result.copy()
    merged["school_id"] = merged.school_id.astype("string").str.zfill(3)
    merged = merged.merge(insights, on="school_id", how="left")
    return merged, None


def _sort_by_ranking(result: pd.DataFrame, ranking_field: str) -> pd.DataFrame:
    if ranking_field == "performance_grade":
        score = pd.to_numeric(result.get("performance_score"), errors="coerce")
        grade = result.get("performance_grade", pd.Series(pd.NA, index=result.index))
        grade_rank = grade.astype("string").str[0].map(GRADE_RANK)
        return result.assign(_grade_rank=grade_rank, _score=score).sort_values(
            ["_grade_rank", "_score", "school_name"], ascending=[False, False, True],
            na_position="last",
        ).drop(columns=["_grade_rank", "_score"])
    return result.sort_values(ranking_field, ascending=False, na_position="last")


def query_schools(
    schools: pd.DataFrame, question: str, home: dict | None = None
) -> tuple[pd.DataFrame, list[str]]:
    """Interpret supported phrases and query the canonical school DataFrame."""
    text = question.lower().strip()
    result = schools.copy()
    understood: list[str] = []
    limit = _requested_limit(text)
    ranking_field = _requested_ranking(text)

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

    ranking_warning: str | None = None
    if ranking_field:
        result, ranking_warning = _merge_school_insights(result)
        if ranking_field in result:
            result = _sort_by_ranking(result, ranking_field)
            understood.append("ranked by " + ranking_field.replace("_", " "))
        else:
            understood.append("requested academic ranking")

    wants_nearby = bool(re.search(r"\b(near me|nearby|closest|nearest)\b", text))
    if home:
        result = add_distances(result, home["latitude"], home["longitude"])
        if wants_nearby and not ranking_field:
            result = result.sort_values("distance_miles", na_position="last")
            understood.append("sorted by distance from your home")
        elif wants_nearby:
            understood.append("distance included from your home")
    else:
        if not ranking_field:
            result = result.sort_values("school_name")
        if wants_nearby:
            understood.append("nearby requested; home address needed for distance sorting")

    if limit:
        result = result.head(limit)
        understood.append(f"limited to top {limit}")
    if ranking_warning:
        understood.append(ranking_warning)

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
    academic_columns = [
        "performance_grade", "performance_score", "growth",
        "math_proficiency", "reading_proficiency", "graduation_rate",
    ]
    for column in reversed(academic_columns):
        if column in results and results[column].notna().any():
            columns.insert(3, column)
    if "distance_miles" in results:
        columns.insert(3, "distance_miles")
    table = results[columns].rename(columns={
        "school_name": "School", "school_level": "Level", "school_type": "Type",
        "distance_miles": "Approx. distance (miles)", "address": "Address", "grades_served": "Grades",
        "performance_grade": "Performance Grade", "performance_score": "Performance Score",
        "growth": "Growth", "math_proficiency": "Math (%)",
        "reading_proficiency": "Reading (%)", "graduation_rate": "Graduation (%)",
    })
    st.dataframe(table, hide_index=True, use_container_width=True,
                 column_config={"Approx. distance (miles)": st.column_config.NumberColumn(format="%.1f")})
