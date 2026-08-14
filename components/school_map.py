"""Folium map rendering; document links never masquerade as GIS polygons."""
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
def render_school_map(schools:pd.DataFrame,home:dict|None,boundaries:dict,transportation:dict)->None:
    center=[home["latitude"],home["longitude"]] if home else [35.2271,-80.8431];map_=folium.Map(location=center,zoom_start=12 if home else 10,control_scale=True)
    if home:folium.Marker(center,tooltip="Home Location",popup=folium.Popup(home["formatted_address"],max_width=260),icon=folium.Icon(color="red",icon="home")).add_to(map_)
    layer=folium.FeatureGroup(name="Matching CMS schools",show=True)
    for _,school in schools.dropna(subset=["latitude","longitude"]).iterrows():
        detail=f"<b>{school.school_name}</b><br>Level: {school.school_level}<br>Type: {school.school_type}<br>Address: {school.address}<br>Grades: {school.grades_served}"
        if pd.notna(school.get("school_id")):detail+=f"<br>School ID: {school.school_id}"
        if pd.notna(school.get("distance_miles")):detail+=f"<br>Approx. straight-line distance: {school.distance_miles:.1f} miles"
        folium.Marker([school.latitude,school.longitude],tooltip=school.school_name,popup=folium.Popup(detail,max_width=280)).add_to(layer)
    layer.add_to(map_);folium.LayerControl(collapsed=False).add_to(map_);st.subheader("Map");st_folium(map_,height=520,use_container_width=True,returned_objects=[])
    with st.expander("Official map layers and availability"):
        if boundaries["available"]:st.markdown(f"Attendance boundaries: {boundaries['message']} [Open official CMS maps]({boundaries['source_url']}).")
        if transportation["available"]:st.markdown(f"Transportation zones: {transportation['message']} [Open official CMS maps]({transportation['source_url']}).")
