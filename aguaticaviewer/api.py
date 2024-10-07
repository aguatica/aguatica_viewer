import asyncio
import time
import json
import hashlib
import pyepicollect as pyep
import geopandas as gpd
import pandas as pd
from aguaticaviewer.config import CLIENT_ID, CLIENT_SECRET, SLUG
from shapely.geometry import Point

class APIClient:
    def __init__(self, interval=60):
        self._token = None
        self._token_expiry_time = None
        self._entries = None
        self._previous_hash = None
        self.interval = interval  # Interval in seconds for token refresh

    async def request_token(self):
        try:
            token_data = pyep.auth.request_token(CLIENT_ID, CLIENT_SECRET)
            self._token = token_data
            expires_in = token_data.get('expires_in', 7200)  # Default to 2 hours if not provided

            # Store the exact time when the token will expire
            self._token_expiry_time = time.time() + expires_in
            print("Token successfully refreshed!")
            return self._token
        except Exception as e:
            print(f"Error requesting token: {e}")
            return None

    def is_token_expired(self):
        """Check if the token has expired based on the expiry time."""
        if self._token_expiry_time is None:
            return True
        return time.time() >= self._token_expiry_time

    async def fetch_entries(self):
        if self._token is None or self.is_token_expired():
            token = await self.request_token()
            print("Token expired, requesting new one")
        else:
            token = self._token
            print("Token still valid.")

        if token is not None:
            try:
                # Fetch data with the current token
                wrapper_entries = pyep.api.get_entries(SLUG, token['access_token'])
                self._entries = wrapper_entries['data']['entries']
                print("Fetched entries")
                return self._entries
            except Exception as e:
                print(f"Error fetching entries: {e}")
                return []
        else:
            print("Failed to fetch entries: No valid token.")
            return []

    async def schedule_token_refresh(self):
        while True:
            await self.fetch_entries()  # Refresh token and fetch entries
            await asyncio.sleep(self.interval)  # Wait for the specified interval

    async def run(self):
        while True:
            latest_entries = self.get_entries()

            if latest_entries:
                data_changed = self.has_data_changed(latest_entries)
                if data_changed:
                    print("Data has changed, updating GeoDataFrame...")
                    entries_df = self.entries_to_geodataframe()
                    print("New GeoDataFrame created with updated data.")
                else:
                    print("No data changes detected.")

            await asyncio.sleep(self.interval)

    def get_entries(self):
        return self._entries

    def get_token(self):
        return self._token

    def entries_to_geodataframe(self):
        data_list = []
        for entry in self._entries:  # Verwende die aktuellen Einträge
            coords = entry.get('9_Coordenas_de_GPS', {})
            latitude = coords.get('latitude', None)
            longitude = coords.get('longitude', None)
            uploaded_at = entry.get('uploaded_at', None)

            # Convert "created_at" to datetime if it's a string and needed for further processing
            uploaded_at_dt = pd.to_datetime(uploaded_at) if uploaded_at else None

            if latitude is not None and longitude is not None and latitude != '' and longitude != '':
                try:
                    geometry = Point(float(longitude), float(latitude))  # Konvertierung in Float sicherstellen
                    data_entry = {
                        'geometry': geometry,
                        'uploaded_at': uploaded_at_dt,
                        **entry  # Unpack die anderen Felder im Eintrag
                    }
                    data_list.append(data_entry)
                except ValueError as ve:
                    print(f"Invalid coordinates for entry {entry['ec5_uuid']}: {ve}")
            else:
                print(f"Skipping entry {entry['ec5_uuid']} due to missing or empty coordinates.")

        if data_list:
            return gpd.GeoDataFrame(data_list, geometry='geometry', crs='EPSG:4326')  # Passendes CRS verwenden
        else:
            return gpd.GeoDataFrame()  # Leeren GeoDataFrame zurückgeben, wenn keine gültigen Einträge

    def calculate_hash(self, data):
        # Extract only relevant fields (coordinates and created_at) and create a list of dicts
        filtered_data = [
            {
                'latitude': entry.get('9_Coordenas_de_GPS', {}).get('latitude'),
                'longitude': entry.get('9_Coordenas_de_GPS', {}).get('longitude'),
                'uploaded_at': entry.get('uploaded_at')
            }
            for entry in data if entry.get('9_Coordenas_de_GPS')  # Only include entries with coordinates
        ]

        # Sort the data list to ensure consistent ordering before hashing
        filtered_data_str = json.dumps(filtered_data, sort_keys=True)  # JSON data as string, sorted by keys
        return hashlib.sha256(filtered_data_str.encode('utf-8')).hexdigest()  # Hash with SHA256

    def has_data_changed(self, new_data):
        new_hash = self.calculate_hash(new_data)  # Only hash relevant fields
        data_changed = new_hash != self._previous_hash
        self._previous_hash = new_hash  # Store the new hash
        return data_changed

    def run(self):
        while True:
            # Hauptlogik zur Überprüfung der Einträge
            latest_entries = self.get_entries()  # Aktuelle Einträge abrufen

            if latest_entries:
                # Überprüfen, ob sich die Daten geändert haben
                data_changed = self.has_data_changed(latest_entries)
                if data_changed:
                    print("Data has changed, updating GeoDataFrame...")
                    # Konvertiere die Einträge in einen GeoDataFrame
                    entries_df = self.entries_to_geodataframe()
                    print("New GeoDataFrame created with updated data.")
                else:
                    print("No data changes detected.")

            time.sleep(self.interval)  # Warten, bevor die nächste Überprüfung erfolgt
