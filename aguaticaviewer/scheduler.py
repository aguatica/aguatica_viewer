import threading
import time

from aguaticaviewer.auth import request_token
from aguaticaviewer.data import fetch_entries

# Start the token refresh in a separate thread


# Function to refresh token every 2 hours (7200 seconds)
def schedule_token_refresh(interval=10):
    global _token, _entries
    while True:
        print("Refreshing token...")
        _token = request_token()
        _entries = fetch_entries()  # Fetch new entries after refreshing the token
        time.sleep(interval)

def start_token_scheduler():
    token_thread = threading.Thread(target=schedule_token_refresh)
    token_thread.daemon = True  # Daemon thread will automatically close when the main program exits
    token_thread.start()

