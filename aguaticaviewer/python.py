import threading
import time
import json
import hashlib
import pyepicollect as pyep
import geopandas as gpd
from aguaticaviewer.config import CLIENT_ID, CLIENT_SECRET, SLUG
from shapely.geometry import Point
import pprint

pp = pprint.PrettyPrinter(indent=2)

class APIClient:
    def __init__(self, interval=30):
        self._token = None
        self._entries = None
        self._previous_hash = None
        self.interval = interval  # Intervall in Sekunden, wie oft der Token aktualisiert wird

    def request_token(self):
        try:
            self._token = pyep.auth.request_token(CLIENT_ID, CLIENT_SECRET)
            print("Token successfully refreshed!")
            return self._token
        except Exception as e:
            print(f"Error requesting token: {e}")
            return None

    def fetch_entries(self):
        token = self.request_token()  # Aktuellen Token abrufen
        if token is not None:
            try:
                # Daten mit dem aktuellen Token abrufen
                wrapper_entries = pyep.api.get_entries(SLUG, token['access_token'])
                self._entries = wrapper_entries['data']['entries']  # Einträge speichern
                print("Fetched entries")
                return self._entries
            except Exception as e:
                print(f"Error fetching entries: {e}")
                return []
        else:
            print("Failed to fetch entries: No valid token.")
            return []

    def schedule_token_refresh(self):
        while True:
            print("Refreshing token and fetching new entries...")
            self.fetch_entries()  # Token aktualisieren und Einträge abrufen
            time.sleep(self.interval)  # Warte das festgelegte Intervall

    def start_token_scheduler(self):
        token_thread = threading.Thread(target=self.schedule_token_refresh)
        token_thread.daemon = True  # Der Daemon-Thread schließt automatisch, wenn das Hauptprogramm beendet wird
        token_thread.start()

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

            if latitude is not None and longitude is not None and latitude != '' and longitude != '':
                try:
                    geometry = Point(float(longitude), float(latitude))  # Konvertierung in Float sicherstellen
                    data_entry = {
                        'geometry': geometry,
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
        data_str = json.dumps(data, sort_keys=True)  # JSON-Daten als String, sortiert
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()  # MD5-Hash der Daten

    def has_data_changed(self, new_data):
        new_hash = self.calculate_hash(new_data)
        data_changed = new_hash != self._previous_hash
        self._previous_hash = new_hash  # Speichere den neuen Hash-Wert
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
                    # Hier kannst du den GeoDataFrame weiterverarbeiten
                    print("New GeoDataFrame created with updated data.")
                else:
                    print("No data changes detected.")

            time.sleep(self.interval)  # Warten, bevor die nächste Überprüfung erfolgt
