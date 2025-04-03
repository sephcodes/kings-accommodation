import ast
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import OverlappingMarkerSpiderfier
import geopandas as gpd
from zipfile import ZipFile
import requests

df = pd.read_excel('Accommodation.xlsx')
map_df = gpd.read_file('London_Borough_Excluding_MHW.shp')

response = requests.get('https://api.tfl.gov.uk/StopPoint/Mode/tube')
data = response.json()
stop_points = data['stopPoints']
tube_df = pd.json_normalize(stop_points)
columns = ['id', 'commonName', 'lat', 'lon', 'indicator', 'stopLetter']
tube_df = tube_df[columns]
tube_df = tube_df[(tube_df['lat'] > 51.45) & (tube_df['lat'] < 51.57) & (tube_df['lon'] > -0.27) & (tube_df['lon'] < 0.0044)]
tube_df['commonName'] = tube_df['commonName'].str.replace(' Underground Station','')
tube_df['commonName'] = tube_df['commonName'].str.replace(' Station','')
tube_df.drop_duplicates(subset=['commonName'], inplace=True)

gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
with ZipFile('Zones.kmz', 'r') as z:
    kml_files = [name for name in z.namelist() if name.endswith('.kml')]
    
    if not kml_files:
        print("No KML file found in KMZ!")
    else:
        kml_filename = kml_files[0]
        z.extract(kml_filename, '.')

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
popup1 = folium.GeoJsonPopup(
    fields=["NAME"],
    aliases=["Borough"],
    localize=True,
    labels=True
)
popup2 = folium.GeoJsonPopup(
    fields=["Name"],
    aliases=["Zone"],
    localize=True,
    labels=True
)
# popup3 = folium.GeoJsonPopup(
#     fields=["commonName"],
#     aliases=["Station"],
#     localize=True,
#     labels=True
# )

tooltip1 = folium.GeoJsonTooltip(
    fields=["NAME"],
    aliases=["Borough"],
    localize=True,
    labels=True,
    max_width=800,
)
tooltip2 = folium.GeoJsonTooltip(
    fields=["Name"],
    aliases=["Zone"],
    localize=True,
    labels=True,
    max_width=800,
)
# tooltip3 = folium.GeoJsonTooltip(
#     fields=["commonName"],
#     aliases=["Station"],
#     localize=True,
#     labels=True,
#     max_width=800,
# )

folium.GeoJson(
    map_df,
    name="Borough Boundaries",
    tooltip=tooltip1,
    popup=popup1,
    style_function=lambda x: {
        "fillColor": "transparent",
        "color": "blue",
        "weight": 2
    }
).add_to(m)

folium.GeoJson(
    zones_gdf,
    name="Zone Boundaries",
    tooltip=tooltip2,
    popup=popup2,
    style_function=lambda feature: {
        "color": "black",
        "weight": 2,
        "fillColor": "transparent"
    }
).add_to(m)

map_df[['NAME', 'geometry']].explore(
    m=m,
    name="Boroughs",
    cmap=None,
    highlight_kwds={'fillOpacity': 0.1},
    style_kwds={'color': 'blue', 'fillOpacity': 0}
)

zones_gdf.explore(
    m=m,
    name="Zones",
    cmap=None,
    highlight_kwds={'fillOpacity': 0.1},
    style_kwds={'color': 'black', 'fillOpacity': 0}
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

for row in tube_df.itertuples(index=False):
    folium.Marker(
        location=[row.lat, row.lon],
        popup=row.commonName,
        tooltip=row.commonName,
        icon=folium.Icon(prefix='fa', color='green', icon='train')
    ).add_to(m)

oms = OverlappingMarkerSpiderfier().add_to(m)

m.save('index.html')
st_folium(m, key="map", width=600, height=600)