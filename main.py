from flask import Flask, render_template_string
import folium
import asyncio
import threading
from aguaticaviewer.api import APIClient
from shapely.geometry import Point


app = Flask(__name__)

# Initialize APIClient
api_client = APIClient(interval=60)

@app.route('/')
def index():
    start_coords = (9.9281, -84.0907)  # Coordinates for San José, Costa Rica
    folium_map = folium.Map(location=start_coords, zoom_start=13)

    tooltip = 'Click For More Info'
    logoIcon = folium.features.CustomIcon('aguatica_logo.png', icon_size=(50, 50))
    folium.Marker(location=start_coords, popup='<strong>Here are some data from measurement Point 1: ... <strong>',
                  tooltip=tooltip, icon=logoIcon).add_to(folium_map)

    # Fetch entries synchronously by running the async method in the current event loop
    asyncio.run(api_client.fetch_entries())  # Use asyncio.run to run the async method in sync context

    entries_df = api_client.entries_to_geodataframe()  # Get updated entries as GeoDataFrame
    if entries_df.empty:
        print("No entries to display on the map.")
        # Optionally, return a different message or page
        return "No data available"

    for _, row in entries_df.iterrows():
        if isinstance(row.geometry, Point):
            latitude = row.geometry.y
            longitude = row.geometry.x

            popup_text = f"""
            <strong>Nombre de la finca:</strong> {row.get('2_Nombre_de_la_finca', 'N/A')}<br>
            <strong>Sitio de muestreo:</strong> {row.get('3_Sitio_de_muestreo', 'N/A')}<br>
            <strong>Fecha de colecta:</strong> {row.get('4_Da_de_la_colecta', 'N/A')}<br>
            <!-- Add more fields as needed -->
            """

            folium.Marker(location=(latitude, longitude), popup=popup_text, tooltip=tooltip).add_to(folium_map)

    # Save the map to an HTML file
    folium_map.save('templates/map.html')

    with open('templates/map.html', 'r') as f:
        map_html = f.read()

    return render_template_string(map_html)

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
    # Run APIClient in background with asyncio
    loop = asyncio.get_event_loop()

    # Start Flask app in a separate thread (since Flask runs synchronously)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start asyncio loop for APIClient in the main thread
    loop.run_until_complete(run_background_tasks())
