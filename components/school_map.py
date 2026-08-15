"""Folium map rendering; document links never masquerade as GIS polygons."""
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

TYPE_COLORS={"Traditional/Public":"#2563eb","Magnet":"#7c3aed","Charter":"#ea580c","Private":"#059669"}

def _school_icon(school_type:str)->folium.DivIcon:
    """A self-contained SVG marker that cannot fail due to a missing image asset."""
    color=TYPE_COLORS.get(school_type,"#475569")
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="34" height="42" viewBox="0 0 34 42">'
         f'<path d="M17 1C8.2 1 1 8.2 1 17c0 11.8 16 24 16 24s16-12.2 16-24C33 8.2 25.8 1 17 1z" fill="{color}" stroke="white" stroke-width="2"/>'
         '<text x="17" y="23" text-anchor="middle" font-size="16">🏫</text></svg>')
    return folium.DivIcon(html=svg,icon_size=(34,42),icon_anchor=(17,42),popup_anchor=(0,-38),class_name="school-pin")

def _home_icon()->folium.DivIcon:
    svg=('<svg xmlns="http://www.w3.org/2000/svg" width="38" height="46" viewBox="0 0 38 46">'
         '<path d="M19 1C9.1 1 1 9.1 1 19c0 13.1 18 26 18 26s18-12.9 18-26C37 9.1 28.9 1 19 1z" fill="#dc2626" stroke="white" stroke-width="2"/>'
         '<text x="19" y="25" text-anchor="middle" font-size="17">⌂</text></svg>')
    return folium.DivIcon(html=svg,icon_size=(38,46),icon_anchor=(19,46),popup_anchor=(0,-42),class_name="home-pin")
def render_school_map(schools:pd.DataFrame,home:dict|None,boundaries:dict,transportation:dict)->None:
    center=[home["latitude"],home["longitude"]] if home else [35.2271,-80.8431];map_=folium.Map(location=center,zoom_start=12 if home else 10,control_scale=True)
    if home:folium.Marker(center,tooltip="Home Location",popup=folium.Popup(home["formatted_address"],max_width=260),icon=_home_icon()).add_to(map_)
    layer=folium.FeatureGroup(name="Matching CMS schools",show=True)
    clusters=MarkerCluster(name="Nearby schools",disableClusteringAtZoom=14).add_to(layer)
    for _,school in schools.dropna(subset=["latitude","longitude"]).iterrows():
        detail=f"<b>{school.school_name}</b><br>Level: {school.school_level}<br>Type: {school.school_type}<br>Address: {school.address}<br>Grades: {school.grades_served}"
        if pd.notna(school.get("school_id")):detail+=f"<br>School ID: {school.school_id}"
        if pd.notna(school.get("distance_miles")):detail+=f"<br>Approx. straight-line distance: {school.distance_miles:.1f} miles"
        folium.Marker([school.latitude,school.longitude],tooltip=school.school_name,popup=folium.Popup(detail,max_width=280),icon=_school_icon(school.school_type)).add_to(clusters)
    layer.add_to(map_);folium.LayerControl(collapsed=False).add_to(map_);st.subheader("Map");st_folium(map_,height=520,use_container_width=True,returned_objects=[])
    st.caption("Marker colors: blue = Traditional/Public · purple = Magnet · orange = Charter · green = Private · red = Home. Nearby schools group into numbered clusters; zoom in to expand them.")
    with st.expander("Official map layers and availability"):
        if boundaries["available"]:st.markdown(f"Attendance boundaries: {boundaries['message']} [Open official CMS maps]({boundaries['source_url']}).")
        if transportation["available"]:st.markdown(f"Transportation zones: {transportation['message']} [Open official CMS maps]({transportation['source_url']}).")
