# drive_clientapi_drive.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
from aguaticaviewer.config import SERVICE_ACCOUNT_FILE, SCOPES
from googleapiclient.http import MediaIoBaseDownload
import geopandas as gpd
import io
import zipfile
import fiona

class APIClient_Drive:
    def __init__(self):
        self.credentials = self._authenticate()
        self.service = self._build_service()

    def _authenticate(self):
        """Authenticate using the service account credentials."""
        return service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

    def _build_service(self):
        """Build the Google Drive API service."""
        return build('drive', 'v3', credentials=self.credentials)

    def list_files_in_folder(self, folder_id, page_size=10):
        """List files in a specific Google Drive folder."""
        results = self.service.files().list(
            q=f"'{folder_id}' in parents",
            pageSize=page_size,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()

        return results.get('files', [])
    
    def read_file_from_drive(self, file_id):
            """Read file content directly from Google Drive into memory."""
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()  # In-memory buffer to store file contents
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}% complete.")
            
            # After downloading, seek to the start of the BytesIO buffer
            fh.seek(0)
            return fh

    def read_shapefile_to_gdf(self, file_id, file_name):
        """Read shapefile content from Google Drive into a GeoDataFrame."""
        # Only process files with the .shp extension
        if not file_name.endswith('.shp'):
            print(f"Skipping non-shapefile: {file_name}")
            return None

        # Stream file content from Google Drive into memory
        file_content = self.read_file_from_drive(file_id)
        
        # Try to read the shapefile into a GeoDataFrame
        try:
            gdf = gpd.read_file(file_content)
            return gdf
        except fiona.errors.DriverError as e:
            print(f"Error reading shapefile {file_name}: {e}")
            return None


    def process_files_in_folder(self, folder_id):
        """Recursively access files in the folder and process shapefiles."""
        items = self.list_files_in_folder(folder_id)

        if not items:
            print(f'No files found in folder with ID: {folder_id}')
            return []

        shapefiles = []

        for item in items:
            #print(f"{item['name']} ({item['id']}) - MIME Type: {item['mimeType']}")

            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # It's a folder, recursively process files in the subfolder
                subfolder_files = self.process_files_in_folder(item['id'])
                shapefiles.extend(subfolder_files)
            else:
                # Process if it's a shapefile
                if item['name'].endswith('.shp'):
                    gdf = self.read_shapefile_to_gdf(item['id'], item['name'])
                    if gdf is not None:
                        print(f"GeoDataFrame created from {item['name']}:")
                        shapefiles.append({'name': item['name'], 'gdf': gdf})

        return shapefiles