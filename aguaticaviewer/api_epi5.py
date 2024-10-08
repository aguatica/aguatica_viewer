import asyncio
import logging
import time
import json
import hashlib
import pyepicollect as pyep
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from aguaticaviewer.config import CLIENT_ID, CLIENT_SECRET, SLUG


class APIClient_EPI5:
    def __init__(self, interval=60):
        self._token = None
        self.token_lock = asyncio.Lock()
        self._token_expiry_time = None
        self._entries = None
        self._previous_hash = None
        self._geodataframe = None
        self.interval = interval  # Interval in seconds for token refresh

    async def request_token(self):
        try:
            token_data = pyep.auth.request_token(CLIENT_ID, CLIENT_SECRET)
            self._token = token_data
            expires_in = token_data.get('expires_in', 7200)  # Default to 2 hours if not provided

            # Store the exact time when the token will expire
            self._token_expiry_time = time.time() + expires_in
            logging.info("Token successfully refreshed!")
            return self._token, self._token_expiry_time
        except Exception as e:
            logging.error(f"Error requesting token: {e}")
            return None

    def is_token_expired(self):
        """Check if the token has expired based on the expiry time."""
        if self._token_expiry_time is None:
            return True
        return time.time() >= self._token_expiry_time

    async def fetch_entries(self):
        if self._token is not None:
            try:
                # Simulate fetching data with the current token
                wrapper_entries = pyep.api.get_entries(SLUG, self._token['access_token'])
                self._entries = wrapper_entries['data']['entries']
                logging.info("Fetched entries.")
                return self._entries
            except Exception as e:
                logging.error(f"Error fetching entries: {e}")
                return []
        else:
                logging.error("Failed to fetch entries: No valid token.")
                return []

    def get_entries(self):
        return self._entries

    async def entries_to_geodataframe(self):
        data_list = []
        for entry in self._entries:
            coords = entry.get('9_Coordenas_de_GPS', {})
            latitude = coords.get('latitude', None)
            longitude = coords.get('longitude', None)
            uploaded_at = entry.get('uploaded_at', None)

            uploaded_at_dt = pd.to_datetime(uploaded_at) if uploaded_at else None

            if latitude is not None and longitude is not None and latitude != '' and longitude != '':
                try:
                    geometry = Point(float(longitude), float(latitude))
                    data_entry = {
                        'geometry': geometry,
                        'uploaded_at': uploaded_at_dt,
                        **entry
                    }
                    data_list.append(data_entry)
                except ValueError as ve:
                    logging.info(f"Invalid coordinates for entry {entry['ec5_uuid']}: {ve}")
            else:
                logging.info(f"Skipping entry {entry['ec5_uuid']} due to missing or empty coordinates.")

        if data_list:
            self._geodataframe = gpd.GeoDataFrame(data_list, geometry='geometry', crs='EPSG:4326')
            return self._geodataframe

    def get_geodataframe(self):
        return self._geodataframe

    def calculate_hash(self, data):
        filtered_data = [
            {
                'latitude': entry.get('9_Coordenas_de_GPS', {}).get('latitude'),
                'longitude': entry.get('9_Coordenas_de_GPS', {}).get('longitude'),
                'uploaded_at': entry.get('uploaded_at')
            }
            for entry in data if entry.get('9_Coordenas_de_GPS')
        ]

        filtered_data_str = json.dumps(filtered_data, sort_keys=True)
        return hashlib.sha256(filtered_data_str.encode('utf-8')).hexdigest()

    def has_data_changed(self, new_data):
        new_hash = self.calculate_hash(new_data)
        data_changed = new_hash != self._previous_hash
        self._previous_hash = new_hash
        return data_changed

    async def run(self):
        logging.debug("Run method has started.")
        while True:
            try:
                # Check if the token is expired before fetching entries
                if self._token is None or self.is_token_expired():
                    logging.info("Token is expired or not set, requesting a new token.")
                    await self.request_token()

                latest_entries = await self.fetch_entries()  # Fetch entries asynchronously
                if latest_entries:
                    data_changed = self.has_data_changed(latest_entries)
                    if data_changed:
                        logging.debug("Data has changed, updating GeoDataFrame...")
                        # Convert entries to GeoDataFrame and store it in the class
                        self._geodataframe = await (self.entries_to_geodataframe())
                        logging.info("New GeoDataFrame created with updated data.")
                    else:
                        logging.info("No data changes detected.")
                else:
                    logging.debug("No latest entries found.")
            except Exception as e:
                logging.error(f"Error in run method: {e}")

            await asyncio.sleep(self.interval)


