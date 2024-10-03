from flask import Flask, render_template_string
import folium
import sys
import os

# Add the project directory to the Python path
#sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from aguaticaviewer.python import APIClient
if __name__ == "__main__":
    # Erstelle eine Instanz des APIClients und starte den Scheduler
    api_client = APIClient(interval=30)  # Aktualisierung des Tokens alle 30 Sekunden
    api_client.start_token_scheduler()  # Starte den Token-Scheduler in einem separaten Thread

    # Hauptprogramm, das weiterläuft und auf die Daten zugreifen kann
    api_client.run()  # Führe die Hauptlogik aus

app = Flask(__name__)
@app.route('/')
def index():
    start_coords = (9.9281, -84.0907)  # Coordinates for San José, Costa Rica
    folium_map = folium.Map(location=start_coords, zoom_start=13)

    tooltip = 'Click For More Info'

    logoIcon = folium.features.CustomIcon('aguatica_logo.png', icon_size=(50, 50))

    folium.Marker(location=start_coords, popup='<strong>Here are some data from measurement Point 1: ... <strong>', tooltip=tooltip, icon=logoIcon).add_to(folium_map)

    # Save the map as an HTML file in the templates directory
    folium_map.save('templates/map.html')

    # Render the map.html directly using render_template_string
    with open('templates/map.html', 'r') as f:
        map_html = f.read()

    return render_template_string(map_html)

if __name__ == '__main__':
    app.run(debug=True)  # Keep debug=True for development
