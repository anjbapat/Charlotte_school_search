# Charlotte School Search

A focused MVP for exploring **Charlotte-Mecklenburg Schools (CMS)** near a home address. It shows CMS school locations, filters results by available directory values, calculates approximate straight-line distance, and links to official CMS boundary and transportation-zone maps. It does not provide recommendations, rankings, AI, accounts, or address storage.

The **Compare Schools** tab lets a family select 2–4 schools. It uses NC DPI School Report Card data for available academic measures and links out to Niche searches; it does not copy, store, or display Niche ratings or rankings.

The **AI School Advisor** tab accepts natural-language questions about school level, type, magnet status, and proximity. It translates those questions into filters over the existing CMS service data; it does not send questions or addresses to a generative-AI service.

## Run

```powershell
uv sync --group dev
uv run streamlit run app.py
```

Run unit tests with `uv run pytest`.

## Architecture

- `app.py` owns Streamlit state and layout. A home address only remains in the current Streamlit session.
- `utils/data_sources.py` retrieves and caches public directory data separately from UI code.
- `utils/geocoding.py` converts an entered address into coordinates without writing it to disk.
- `utils/data_processing.py` maps source fields to a predictable school model.
- `utils/distance.py` supplies Haversine, straight-line miles.
- `components/` contains filters, Folium map rendering, and school details.

## Data sources

| Source | Dataset / type | Used for | Relevant fields / limitation |
| --- | --- | --- | --- |
| [City of Charlotte / Mecklenburg GIS Schools layer](https://gis.charlottenc.gov/arcgis/rest/services/HNS/HousingLocationalToolLayers/MapServer/1) | Public ArcGIS point Feature Layer | School markers and distance calculations | Coordinates, school ID, name, address, ownership, school level, grade level, and CMS magnet flag. The layer description credits the Planning Department and Charlotte-Mecklenburg Schools. Cached for one hour. |
| [Charlotte-Mecklenburg Schools](https://www.cmsk12.org/schools/all-schools) | Current official CMS school directory, HTML | Confirms CMS-only scope and links to individual official school sites | Current directory organized by configuration; not used as a stable location API. |
| [CMS Student Boundary Maps](https://www.cmsk12.org/academics/planning-services/student-boundary-maps) | Official 2026–27 attendance-boundary and transportation-zone map documents | Official boundary/zone access | CMS publishes separate attendance-boundary and transportation-zone maps. No verified public GeoJSON/FeatureServer polygon endpoint was identified, so the app links to official documents and does **not** draw or relabel polygons. |
| [NC DPI School Report Card researcher data](https://www.dpi.nc.gov/data-reports/school-report-cards/school-report-card-resources-researchers) | Official downloadable 2024–25 School Report Card datasets | Compare-tab academics | Where present in the published source: School Performance Grade and Score, growth, and graduation rate. NC Report Cards cover public, charter, and alternative schools; private schools may have no values. |
| [Niche](https://www.niche.com/) | Outbound school-search links only | Optional further research | The app does not ingest, copy, store, or display Niche ratings/rankings. |
| [OpenStreetMap Nominatim](https://nominatim.org/release-docs/latest/api/Search/) | Public geocoding service | Address to coordinates for the current session only | Availability and results are external-service dependent. Set `GEOCODER_USER_AGENT` in `.env`; no key is required. |

## Known limitations

- Distance is approximate straight-line distance, never driving distance or commute time.
- School types are derived from the GIS layer’s ownership and magnet fields: Traditional/Public, Private, Charter, and Magnet. A magnet flag takes precedence where supplied by the source.
- The CMS boundary and transportation-zone sources are official map documents, not verified interactive GIS layers. The map does not fabricate boundaries or transportation zones.
- A CMS magnet-zone polygon dataset was not identified in the selected public sources.
- CCD is currently the 2024–25 directory release; confirm and update the constant when NCES releases a newer verified file.

## Privacy

Home addresses are not written to files, databases, analytics, or cached data. They exist only in Streamlit session state while the app is open.
