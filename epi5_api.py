import sys
sys.path.append('..')
import pyepicollect as pyep
import pprint
pp = pprint.PrettyPrinter(indent=2)
from IPython import display

import time
import threading

#
CLIENT_ID = 5603
CLIENT_SECRET = 's2IQsFWgw9Eygz85DsjBb9RduYOtH1xbWq9smTBq'
NAME = 'aguatica_viewer'
SLUG = 'monitoreo-de-agua'

result = pyep.api.search_project(NAME)
result

token = pyep.auth.request_token(CLIENT_ID, CLIENT_SECRET)
pp.pprint(token)

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


# Get entries
entries = pyep.api.get_entries(SLUG, token['access_token'])
# Entries data
data = entries['data']
pp.pprint(data)