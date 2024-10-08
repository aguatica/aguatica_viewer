from quart import Quart, render_template
import folium
import asyncio
from aguaticaviewer.api_epi5 import APIClient_EPI5
from shapely.geometry import Point
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)

# Initialize APIClient
api_client = APIClient_EPI5(interval=60)

@app.route('/')
async def index():
    start_coords = (9.9281, -84.0907)  # Coordinates for San José, Costa Rica
    folium_map = folium.Map(location=start_coords, zoom_start=13)
    tooltip = 'Click For More Info'

    entries_df = api_client.get_geodataframe() # Get updated entries as GeoDataFrame
    # Check if the GeoDataFrame exists and is not empty
    if entries_df is None:
        print("GeoDataFrame is None, background task might not have fetched data yet.")
        return "Data is not available yet, please try again later."
    elif entries_df.empty:
        print("No entries to display on the map.")
        return "No data available"

    for _, row in entries_df.iterrows():
        if isinstance(row.geometry, Point):
            latitude = row.geometry.y
            longitude = row.geometry.x

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
        ).add_to(folium_map)


    # Save the map as an HTML file in the templates directory
    folium_map.save('templates/map.html')

    # Render the map.html using render_template
    return await render_template('map.html')  # Use await with render_template for asynchronous context

@app.before_serving
async def start_background_tasks():
    """Start background tasks before the Quart app starts serving requests."""
    asyncio.create_task(api_client.run())  # Run background tasks in a new task

if __name__ == "__main__":
    app.run(debug=True)

