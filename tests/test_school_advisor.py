import pandas as pd

from components.school_advisor import query_schools


SCHOOLS = pd.DataFrame({
    "school_name": ["Magnet Elementary", "Regular Elementary", "Magnet High"],
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
