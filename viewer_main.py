from flask import Flask, render_template
import folium

app = Flask(__name__) #creates an instance of the Flask class

@app.route('/')

def index():
    # Create a map centered at a specific latitude and longitude
    start_coords = (45.5236, -122.6750)  # Coordinates for Portland, Oregon
    folium_map = folium.Map(location=start_coords, zoom_start=13)

    # Save the map as an HTML file
    folium_map.save('templates/map.html')

    # Render the main HTML page (index.html) which will load the map
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
