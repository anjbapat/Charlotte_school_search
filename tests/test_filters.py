import pandas as pd
from components.school_filters import filter_schools
SCHOOLS=pd.DataFrame({"school_level":["Elementary","Middle","High","K-8"],"school_type":["Regular school","Regular school","Magnet","Magnet"]})
def test_level_filter():assert len(filter_schools(SCHOOLS,["Elementary"],[]))==1
def test_multiple_levels_filter():assert len(filter_schools(SCHOOLS,["Elementary","Middle"],[]))==2
def test_combined_filter():assert len(filter_schools(SCHOOLS,["High"],["Magnet"]))==1
