from flask import Flask, render_template_string
import folium

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
