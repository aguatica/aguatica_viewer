import sys
sys.path.append('..')
import pyepicollect as pyep
import pprint
pp = pprint.PrettyPrinter(indent=2)
#from IPython import display
from shapely.geometry import Point
import matplotlib.pyplot as plt

import time
import threading

#
CLIENT_ID = 5603
CLIENT_SECRET = 's2IQsFWgw9Eygz85DsjBb9RduYOtH1xbWq9smTBq'
NAME = 'aguatica_viewer'
SLUG = 'monitoreo-de-agua'


def request_token():
    try:
        token = pyep.auth.request_token(CLIENT_ID, CLIENT_SECRET)
        pp.pprint(token)
    except Exception as e:
        print(f"Error requesting token: {e}")


# Function to refresh token every 2 hours (7200 seconds)
def schedule_token_refresh(interval=7200):
    while True:
        request_token()
        time.sleep(interval)

# Start the token refresh in a separate thread
def start_token_scheduler():
    token_thread = threading.Thread(target=schedule_token_refresh)
    token_thread.daemon = True  # Daemon thread will automatically close when the main program exits
    token_thread.start()

# Call the scheduler
start_token_scheduler()

# Main program loop (to keep it running)
while True:
    time.sleep(1)  # Keeps the main thread alive



result = pyep.api.search_project(NAME)
result

token = pyep.auth.request_token(CLIENT_ID, CLIENT_SECRET)
pp.pprint(token)
wrapper_entries = pyep.api.get_entries(SLUG, token['access_token'])


# Extract entries
entries = wrapper_entries['data']['entries']
data_list = []

for entry in entries:
    # Check if coordinates are present
    coords = entry.get('9_Coordenas_de_GPS', {})
    
    # Check for latitude and longitude presence and validity
    latitude = coords.get('latitude', None)
    longitude = coords.get('longitude', None)

    # Ensure latitude and longitude are not None and can be converted to float
    if latitude is not None and longitude is not None and latitude != '' and longitude != '':
        try:
            # Attempt to convert to float
            #lat_float = float(latitude)
            #lon_float = float(longitude)

            # Create a Point geometry
            geometry = Point(latitude, longitude)  # Note: (longitude, latitude)
            data_entry = {
                'geometry': geometry,
                **entry  # Unpack the other fields in the entry
            }
            data_list.append(data_entry)
        except ValueError as ve:
            print(f"Invalid coordinates for entry {entry['ec5_uuid']}: {ve}")
    else:
        print(f"Skipping entry {entry['ec5_uuid']} due to missing or empty coordinates.")

print("HIIII")
# Create the GeoDataFrame
entries_df = gpd.GeoDataFrame(data_list, geometry='geometry', crs='EPSG:32616')

entries_df.plot(column='13_Temperatura')  # Make sure the column name matches your DataFrame