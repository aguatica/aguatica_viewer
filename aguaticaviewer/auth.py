# aguaticaviewer/auth.py

import pyepicollect as pyep
import threading
import time
from aguaticaviewer.config import CLIENT_ID, CLIENT_SECRET
import pprint

pp = pprint.PrettyPrinter(indent=2)

def request_token():
    try:
        token = pyep.auth.request_token(CLIENT_ID, CLIENT_SECRET)
        pp.pprint(token)
        return token
    except Exception as e:
        print(f"Error requesting token: {e}")
        return None

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

# Optionally initialize token at the start
token = request_token()

# Start the scheduler automatically
start_token_scheduler()