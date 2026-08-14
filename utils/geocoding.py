"""Privacy-preserving address geocoding; addresses are never written to disk."""
import os
from geopy.geocoders import Nominatim
def geocode_address(address: str) -> dict:
    if not address or not address.strip(): return {"ok":False, "message":"An address is required."}
    try: location = Nominatim(user_agent=os.getenv("GEOCODER_USER_AGENT", "charlotte-school-search"), timeout=10).geocode(address, country_codes="us", addressdetails=False)
    except Exception: return {"ok":False, "message":"Geocoding service unavailable."}
    return {"ok":True, "latitude":location.latitude, "longitude":location.longitude, "formatted_address":location.address} if location else {"ok":False, "message":"Address not found."}
def is_likely_cms_area(latitude: float, longitude: float) -> bool:
    """A warning only, not an assignment determination."""
    return 34.9 <= latitude <= 35.55 and -81.2 <= longitude <= -80.45
