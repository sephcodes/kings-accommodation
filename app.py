import ast
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, OverlappingMarkerSpiderfier
import geopandas as gpd

df = pd.read_excel('Accommodation.xlsx')
map_df = gpd.read_file('London_Borough_Excluding_MHW.shp')

df.fillna(method='ffill', inplace=True)

df.columns = ["Accommodation Type", "Features", "Location", "Distance to Strand", "Room Type", "Cost (per week)", "Details", "loc", "site"]
df.set_index(["Accommodation Type", "Location"], inplace=True)
df.drop(columns=["Features"], inplace=True)
df["loc"] = df["loc"].apply(lambda x: ast.literal_eval(x))

st.title("Accommodation Locations")

st.sidebar.title("Filters")

if "selected_location" not in st.session_state:
    st.session_state.selected_location = []

selected_location = st.sidebar.multiselect(
    "Select location", df.index.get_level_values(1).unique(),
    default=st.session_state.selected_location
)

filtered_df_location = df[df.index.get_level_values(1).isin(selected_location)]
selected_rooms = st.sidebar.multiselect(
    "Select rooms",
    filtered_df_location["Room Type"].unique() if not filtered_df_location.empty else df["Room Type"].unique(),
    default=filtered_df_location["Room Type"].unique() if not filtered_df_location.empty else [],
)

filtered_df = filtered_df_location[filtered_df_location["Room Type"].isin(selected_rooms)] if selected_location else df

m = folium.Map(location=[51.50161, -0.07625], zoom_start=12, width="%100", height="%100")


geojson_layer = folium.GeoJson(
    map_df,
    name="Borough Boundaries",
    style_function=lambda x: {'color':'blue', 'weight':2, 'fill':False}
).add_to(m)

map_df[['NAME', 'geometry']].explore(
    m=m,
    name="NAME",
    cmap=None,
    style_kwds={'color': None, 'fillOpacity': 0}
)

# Add King's Strand Campus marker
folium.Marker(
    location=[51.51161, -0.11625],
    popup="King's Strand Campus",
    tooltip="King's Strand Campus",
    icon=folium.Icon(color='red', icon='info-sign')
).add_to(m)

for (index1, index2), row in filtered_df.iterrows():
    html = f"""
        <h3> {index2}</h3>
        <ul>
            <li>Distance: {row['Distance to Strand']}</li>
            <li>Room Type: {row['Room Type']}</li>
            <li>Cost(per week): {row['Cost (per week)']}</li>
            <li>Details: {row['Details']}</li>
            <li><a href="{row['site']}">site</a></li>
        </ul>
    """
    iframe = folium.IFrame(html=html, width=200, height=200)
    popup = folium.Popup(iframe, max_width=2650)
    tooltip_text = f"Location: {index2} Room Type: {row['Room Type']}"
    folium.Marker(
        location=row["loc"],
        popup=popup,
        tooltip=tooltip_text,
        icon=folium.Icon(color='blue', icon='home')
    ).add_to(m)

oms = OverlappingMarkerSpiderfier().add_to(m)

# st_folium(m)
m.save('index.html')
st_folium(m, key="map", width=900, height=600)
