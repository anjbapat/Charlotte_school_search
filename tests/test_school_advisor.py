import pandas as pd

from components.school_advisor import query_schools


SCHOOLS = pd.DataFrame({
    "school_name": ["Magnet Elementary", "Regular Elementary", "Magnet High"],
    "school_id": ["001", "002", "003"],
    "school_level": ["Elementary", "Elementary", "High"],
    "school_type": ["Magnet", "Traditional/Public", "Magnet"],
    "magnet": ["Yes", "No", "Yes"],
    "latitude": [35.21, 35.30, 35.22],
    "longitude": [-80.81, -80.90, -80.82],
})


def test_queries_level_and_program():
    result, understood = query_schools(SCHOOLS, "Which elementary schools offer a magnet program?")
    assert result.school_name.tolist() == ["Magnet Elementary"]
    assert "level: Elementary" in understood


def test_near_me_sorts_by_home_distance():
    home = {"latitude": 35.20, "longitude": -80.80}
    result, understood = query_schools(SCHOOLS, "Which schools are closest near me?", home)
    assert result.school_name.iloc[0] == "Magnet Elementary"
    assert result.distance_miles.is_monotonic_increasing
    assert "sorted by distance from your home" in understood


def test_top_elementary_schools_rank_by_performance_grade(monkeypatch):
    insights = pd.DataFrame({
        "school_id": ["001", "002", "003"],
        "performance_grade": ["B", "A", "A"],
        "performance_score": [78, 91, 95],
    })
    monkeypatch.setattr(
        "components.school_advisor.get_nc_dpi_school_insights",
        lambda: {"available": True, "data": insights, "message": "", "school_year": "2024-25"},
    )

    result, understood = query_schools(SCHOOLS, "top 1 elementary school based on school performance grade")

    assert result.school_name.tolist() == ["Regular Elementary"]
    assert result.performance_grade.tolist() == ["A"]
    assert "ranked by performance grade" in understood
    assert "limited to top 1" in understood


def test_top_near_me_keeps_academic_rank_order(monkeypatch):
    insights = pd.DataFrame({
        "school_id": ["001", "002", "003"],
        "performance_grade": ["A", "B", "A"],
        "performance_score": [88, 79, 96],
    })
    monkeypatch.setattr(
        "components.school_advisor.get_nc_dpi_school_insights",
        lambda: {"available": True, "data": insights, "message": "", "school_year": "2024-25"},
    )
    home = {"latitude": 35.20, "longitude": -80.80}

    result, understood = query_schools(SCHOOLS, "top 2 schools near me", home)

    assert result.school_name.tolist() == ["Magnet High", "Magnet Elementary"]
    assert "distance_miles" in result
    assert "distance included from your home" in understood
