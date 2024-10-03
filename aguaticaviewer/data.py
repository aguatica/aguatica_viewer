# aguaticaviewer/data.py

import pyepicollect as pyep
import geopandas as gpd
from shapely.geometry import Point
from aguaticaviewer.config import SLUG
import hashlib
import json
import time

from aguaticaviewer.auth import request_token

_entries = None
# Funktion zum Abrufen der Daten mit dem aktuellen Token
def fetch_entries():
    global _entries
    token = request_token()
    if token is not None:
        try:
            wrapper_entries = pyep.api.get_entries(SLUG, token['access_token'])
            _entries = wrapper_entries['data']['entries']
            print("Fetched entries")
            return _entries
        except Exception as e:
            print(f"Error fetching entries: {e}")
            return []
    else:
        print("Failed to fetch entries: No valid token.")
        return []



def entries_to_geodataframe(_entries):
    _entries = fetch_entries()
    data_list = []

    for entry in _entries:
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



# Funktion zur Berechnung des Hash-Werts
def calculate_hash(data):
    data_str = json.dumps(data, sort_keys=True)  # JSON-Daten als string, sortiert
    return hashlib.md5(data_str.encode('utf-8')).hexdigest()  # MD5-Hash der Daten

# Funktion zum Überprüfen, ob sich die Daten geändert haben
def has_data_changed(new_data, previous_hash):
    new_hash = calculate_hash(new_data)
    return new_hash != previous_hash, new_hash

if data_changed:
    print("Data has changed, updating GeoDataFrame...")
    previous_hash = new_hash  # Speichere den neuen Hash-Wert

    # Konvertiere die Einträge in einen GeoDataFrame
    entries_df = entries_to_geodataframe(_entries)

    # Hier kannst du den GeoDataFrame weiterverarbeiten
    print("New GeoDataFrame created with updated data.")
else:
    print("No data changes detected.")



def plot_data(geodf, column):
    try:
        geodf.plot(column=column)
    except Exception as e:
        print(f"Error plotting data: {e}")
