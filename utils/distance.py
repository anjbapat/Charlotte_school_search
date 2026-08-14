"""Testable straight-line distance utilities."""
from math import asin, cos, radians, sin, sqrt
import pandas as pd
def calculate_distance_miles(home_lat: float, home_lon: float, school_lat: float, school_lon: float) -> float:
    """Return Haversine (not driving) distance in miles."""
    a = sin(radians(school_lat-home_lat)/2)**2 + cos(radians(home_lat))*cos(radians(school_lat))*sin(radians(school_lon-home_lon)/2)**2
    return 3958.7613 * 2 * asin(sqrt(a))
def add_distances(schools: pd.DataFrame, home_lat: float, home_lon: float) -> pd.DataFrame:
    result = schools.copy()
    result["distance_miles"] = result.apply(lambda row: calculate_distance_miles(home_lat, home_lon, row.latitude, row.longitude) if pd.notna(row.latitude) and pd.notna(row.longitude) else pd.NA, axis=1)
    return result
