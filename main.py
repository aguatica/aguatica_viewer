from quart import Quart, render_template_string
import folium
import asyncio
import threading
from aguaticaviewer.api import APIClient
from aguaticaviewer.api_drive import APIClient_Drive
from shapely.geometry import Point
from google.oauth2 import service_account
from googleapiclient.discovery import build
from Google import Create_Service
from aguaticaviewer.config import FOLDER_ID
import geopandas as gpd

app = Quart(__name__)

# Initialize APIClient
api_client = APIClient(interval=600)

# Instantiate DriveClient
drive_client = APIClient_Drive()

# Global variable to store the entries GeoDataFrame
cached_entries_df = None

# Event to signal when data is ready
data_ready_event = asyncio.Event()


async def update_entries():
    global cached_entries_df
    while True:
        try:
            await api_client.fetch_entries()  # Fetch new entries
            cached_entries_df = api_client.entries_to_geodataframe()  # Update the cached entries
            print("Entries updated.")

            # Signal that data is ready after the first fetch
            if not data_ready_event.is_set():
                data_ready_event.set()

        except Exception as e:
            print(f"Error fetching entries: {e}")

        await asyncio.sleep(api_client.interval)  # Wait for the specified interval before fetching again


@app.route('/')
async def index():
    # Wait until data is ready
    await data_ready_event.wait()

    start_coords = (9.9281, -84.0907)  # Coordinates for San José, Costa Rica
    folium_map = folium.Map(location=start_coords, zoom_start=13)

    tooltip = 'Click For More Info'

    if cached_entries_df is None or cached_entries_df.empty:
        print("No entries to display on the map.")
        return "No data available"

    # Retrieve and print the CRS of the GeoDataFrame
    crs = cached_entries_df.crs
    print(f"CRS of the entries GeoDataFrame: {crs}")

    # Create a FeatureGroup for entries_df
    entries_group = folium.FeatureGroup(name='Entries')
    # Iterate through the entries_df to add markers for each entry
    for _, row in cached_entries_df.iterrows():
        if isinstance(row.geometry, Point):  # Check if geometry is a Point
            latitude = row.geometry.y  # Get latitude
            longitude = row.geometry.x  # Get longitude

            popup_text = f"""
            <table style="width:100%; border: 1px solid black; border-collapse: collapse;">
              <tr style="border: 1px solid black;">
                <th style="border: 1px solid black; padding: 8px;">Parameter</th>
                <th style="border: 1px solid black; padding: 8px;">Value</th>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Nombre de la finca</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('2_Nombre_de_la_finca', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Sitio de muestreo</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('3_Sitio_de_muestreo', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Fecha de colecta</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('4_Da_de_la_colecta', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Hora de colecta</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('5_Hora_de_la_colecta', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Tipo de sitio</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('6_Tipo_de_sitio_de_m', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Tipo de Agua</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('7_Tipo_de_Agua', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Tipo de mediciones</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('8_Tipo_de_mediciones', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>GPS Coordinates</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('9_Coordenas_de_GPS', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>pH</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('10_pH', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Sólidos disueltos</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('11_Slidos_disueltos', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Conductividad</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('12_Conductividad', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Temperatura</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('13_Temperatura', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Fosfatos</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('14_Fosfatos', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Nitritos</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('15_Nitritos', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>O18</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('16_O18', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>H2</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('17_H2', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>E. coli</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('18_Ecoli', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Coliformes Totales</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('19_Coliformes_totale', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Foto</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('20_Tome_una_foto', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Video</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('21_Grabe_un_video_de', 'N/A')}</td>
              </tr>
              <tr style="border: 1px solid black;">
                <td style="border: 1px solid black; padding: 8px;"><strong>Notas adicionales</strong></td>
                <td style="border: 1px solid black; padding: 8px;">{row.get('22_Anote_cualquier_c', 'N/A')}</td>
              </tr>
            </table>
            """

            # Add marker to the map
            folium.Marker(
                location=(latitude, longitude),
                popup=popup_text,
                tooltip=tooltip
            ).add_to(entries_group)

    # Add the entries FeatureGroup to the map
    entries_group.add_to(folium_map)

    # Process shapefiles and add them to the map asynchronously
    shapefiles_drive = await drive_client.process_files_in_folder(FOLDER_ID)

    if shapefiles_drive:
        for shapefile in shapefiles_drive:
            # Check if the GeoDataFrame is valid
            if isinstance(shapefile['gdf'], gpd.GeoDataFrame) and not shapefile['gdf'].empty:
                # Print the CRS
                print(f"Shapefile '{shapefile['file_name']}' CRS: {shapefile['gdf'].crs}")

                # Reproject to WGS 84 if needed
                if shapefile['gdf'].crs is not None and shapefile['gdf'].crs != "EPSG:4326":
                    shapefile['gdf'] = shapefile['gdf'].to_crs("EPSG:4326")
                    print(f"Reprojected '{shapefile['file_name']}' to EPSG:4326")

                # Create a FeatureGroup for each shapefile
                feature_group = folium.FeatureGroup(name=shapefile['file_name'])
                geojson_data = shapefile['gdf'].to_json()
                folium.GeoJson(geojson_data).add_to(feature_group)
                feature_group.add_to(folium_map)  # Add FeatureGroup to the map
            else:
                print(f"Shapefile '{shapefile['file_name']}' is not a valid GeoDataFrame or is empty.")
    else:
        print(f"No shapefiles found in folder ID: {FOLDER_ID}")

    # Add LayerControl to the map
    folium.LayerControl().add_to(folium_map)

    # Save the map as an HTML file in the templates directory
    folium_map.save('templates/map.html')

    # Render the map.html directly using render_template_string
    with open('templates/map.html', 'r', encoding='utf-8') as f:
        map_html = f.read()

    return await render_template_string(map_html)

def run_flask():
    """Function to run Flask in the main thread."""
    app.run(debug=True, use_reloader=False)

async def run_background_tasks():
    """Run APIClient token scheduler and main logic concurrently in the background."""
    await asyncio.gather(
        api_client.schedule_token_refresh(),  # Schedule the token refresh
        api_client.run()  # Main logic to check for data changes
    )

if __name__ == "__main__":
    # Start the background task for fetching entries
    loop = asyncio.get_event_loop()
    loop.create_task(update_entries())

    # Run Quart application with asyncio
    loop.run_until_complete(app.run_task())
