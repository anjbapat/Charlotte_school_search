import pandas as pd

from data_sources.data_manager import normalize_school_frame


def test_normalize_converts_types_deduplicates_and_rejects_out_of_state_coordinates():
    raw = pd.DataFrame({
        "School Number": ["001", "001"], "School Name": ["Oak", "Oak"], "LEA Name": ["Example", "Example"],
        "Enrollment": ["450", "450"], "Math Proficiency": ["71%", "71%"], "Charter": ["Yes", "Yes"],
        "Latitude": [35.2, 99], "Longitude": [-80.8, -80.8],
    })
    result = normalize_school_frame(raw)
    assert len(result) == 1
    assert result.loc[0, "school_id"] == "001"
    assert result.loc[0, "math_proficiency"] == 71
    assert bool(result.loc[0, "charter"]) is True
    assert result.loc[0, "latitude"] == 35.2
