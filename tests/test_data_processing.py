import pandas as pd
from utils.data_processing import normalize_cms_directory,school_level
def test_levels_preserve_configurations():
    assert school_level("K, 1, 2, 3, 4, 5, 6, 7, 8")=="K-8";assert school_level("6, 7, 8, 9, 10, 11, 12")=="6-12"
def test_normalization_deduplicates_and_validates_coordinates():
    raw=pd.DataFrame({"LEAID":[3702970,3702970],"ST_SCHID":[1,1],"SCH_NAME":["A","A"],"SCH_TYPE_TEXT":["Regular school","Regular school"],"LSTREET1":["1 Main","1 Main"],"LCITY":["Charlotte","Charlotte"],"LZIP":["28202","28202"],"LATCOD":[35.2,99],"LONCOD":[-80.8,0],"G_KG_OFFERED":["YES","YES"]})
    result=normalize_cms_directory(raw);assert len(result)==1 and result.loc[0,"school_level"]=="Elementary"
