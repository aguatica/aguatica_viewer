# aguaticaviewer/data.py

import pyepicollect as pyep
import geopandas as gpd
from shapely.geometry import Point
from aguaticaviewer.auth import token  # Import the token from auth.py
from aguaticaviewer.config import SLUG

def fetch_entries():
    # Fetch entries using the token
    try:
        wrapper_entries = pyep.api.get_entries(SLUG, token['access_token'])
        entries = wrapper_entries['data']['entries']
        return entries
    except Exception as e:
        print(f"Error fetching entries: {e}")
        return []

def entries_to_geodataframe(entries):
    data_list = []
    
    for entry in entries:
        # Check if coordinates are present
        coords = entry.get('9_Coordenas_de_GPS', {})
        
        # Check for latitude and longitude presence and validity
        latitude = coords.get('latitude', None)
        longitude = coords.get('longitude', None)

        if latitude is not None and longitude is not None and latitude != '' and longitude != '':
            try:
                # Create a Point geometry
                geometry = Point(float(longitude), float(latitude))  # Ensure conversion to float
                data_entry = {
                    'geometry': geometry,
                    **entry  # Unpack the other fields in the entry
                }
                data_list.append(data_entry)
            except ValueError as ve:
                print(f"Invalid coordinates for entry {entry['ec5_uuid']}: {ve}")
        else:
            print(f"Skipping entry {entry['ec5_uuid']} due to missing or empty coordinates.")
    
    # Create the GeoDataFrame
    if data_list:
        return gpd.GeoDataFrame(data_list, geometry='geometry', crs='EPSG:4326')  # Use appropriate CRS
    else:
        return gpd.GeoDataFrame()  # Return empty GeoDataFrame if no valid entries

def plot_data(geodf, column):
    try:
        geodf.plot(column=column)
    except Exception as e:
        print(f"Error plotting data: {e}")
