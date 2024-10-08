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
              <!-- Add other rows as necessary -->
            </table>
            """

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
