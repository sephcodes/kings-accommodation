import ast
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import OverlappingMarkerSpiderfier
import geopandas as gpd
from zipfile import ZipFile

df = pd.read_excel('Accommodation.xlsx')
map_df = gpd.read_file('London_Borough_Excluding_MHW.shp')

gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
with ZipFile('Zones.kmz', 'r') as z:
    kml_files = [name for name in z.namelist() if name.endswith('.kml')]
    
    if not kml_files:
        print("No KML file found in KMZ!")
    else:
        kml_filename = kml_files[0]
        z.extract(kml_filename, '.')
        print(f"Extracted: {kml_filename}")

zones_gdf = gpd.GeoDataFrame(gpd.read_file(kml_filename, driver='KML'), crs="EPSG:4326")
zones_gdf.set_crs("EPSG:4326", inplace=True)
zones_gdf.to_crs("EPSG:27700", inplace=True)

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

folium.GeoJson(
    map_df,
    name="Borough Boundaries",
    style_function=lambda x: {'color':'blue', 'weight':2, 'fill':False}
).add_to(m)

folium.GeoJson(
    zones_gdf,
    name="Zone Boundaries",
    tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Zone: "]),
    style_function=lambda feature: {
        "color": "black",
        "weight": 2,
        "fill": False,
        "fillColor": "transparent"
    },
    highlight_function=lambda x: {'fillColor': '#000000', 
                                'color':'#000000', 
                                'fillOpacity': 0, 
                                'weight': 0.1,
                                "fillColor": "transparent"}
    # style_function=lambda x: {'color':'blue', 'weight':2, 'fill':False}
).add_to(m)

map_df[['NAME', 'geometry']].explore(
    m=m,
    name="NAME",
    cmap=None,
    style_kwds={'color': None, 'fillOpacity': 0}
)

zones_gdf.explore(
    m=m,
    name="Name",
    cmap=None,
    style_kwds={'color': None, 'fillOpacity': 0}
)

folium.LayerControl().add_to(m)

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

m.save('index.html')
st_folium(m, key="map", width=600, height=600)