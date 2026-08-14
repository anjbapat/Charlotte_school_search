"""Normalize the official directory fields into the internal school model."""
import pandas as pd
def _grades(row: pd.Series) -> str:
    offered = [("PK","G_PK_OFFERED"),("K","G_KG_OFFERED")] + [(str(n),f"G_{n:02d}_OFFERED") for n in range(1,13)]
    return ", ".join(label for label,column in offered if str(row.get(column, "")).upper() in {"YES","Y","1"})
def school_level(grades: str) -> str:
    tokens = {part.strip() for part in str(grades).split(",")}; numbers = {int(x) for x in tokens if x.isdigit()}
    elementary = bool({"PK","K"}&tokens or any(n<=5 for n in numbers)); middle = any(6<=n<=8 for n in numbers); high = any(n>=9 for n in numbers)
    if elementary and middle and not high: return "K-8"
    if middle and high and not elementary: return "6-12"
    if elementary and middle and high: return "K-12"
    if elementary: return "Elementary"
    if middle: return "Middle"
    if high: return "High"
    return "Other"
def normalize_cms_directory(raw: pd.DataFrame) -> pd.DataFrame:
    """Filter CCD to CMS (LEAID 3702970), validate coordinates, remove duplicates."""
    cms = raw.loc[raw["LEAID"].astype(str).str.zfill(7).eq("3702970")].copy()
    street=cms["LSTREET1"].fillna("").astype("string");city=cms["LCITY"].fillna("").astype("string");zip_code=cms["LZIP"].fillna("").astype("string")
    latitude=cms.get("LATCOD",pd.Series(pd.NA,index=cms.index));longitude=cms.get("LONCOD",pd.Series(pd.NA,index=cms.index))
    result = pd.DataFrame({"school_id":cms["ST_SCHID"].astype("string"),"school_name":cms["SCH_NAME"].astype("string"),"school_type":cms["SCH_TYPE_TEXT"].fillna("Other").astype("string"),"address":(street+", "+city+", NC "+zip_code).str.strip(", "),"city":city,"state":"NC","zip_code":zip_code,"latitude":pd.to_numeric(latitude,errors="coerce"),"longitude":pd.to_numeric(longitude,errors="coerce"),"grades_served":cms.apply(_grades,axis=1),"phone":cms.get("PHONE",pd.Series(pd.NA,index=cms.index)).astype("string"),"website":cms.get("WEBSITE",pd.Series(pd.NA,index=cms.index)).astype("string")})
    result["school_level"] = result.grades_served.map(school_level)
    result.loc[~result.latitude.between(34.5,36.0)|~result.longitude.between(-82.0,-79.5),["latitude","longitude"]]=pd.NA
    return result.dropna(subset=["school_name"]).drop_duplicates("school_id").reset_index(drop=True)
