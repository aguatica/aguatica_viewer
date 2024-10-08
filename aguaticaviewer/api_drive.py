# api_drive.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
from aguaticaviewer.config import SERVICE_ACCOUNT_FILE, SCOPES
from googleapiclient.http import MediaIoBaseDownload
import geopandas as gpd
import io
import zipfile
import fiona
import tempfile
import os

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
    
    def download_shapefile_files(self, folder_id, shapefile_prefix):
        """Download all files belonging to a shapefile (shp, shx, dbf, etc.)"""
        files = self.list_files_in_folder(folder_id)
        shapefile_files = {}
        
        # Identify the required components (.shp, .shx, .dbf, etc.)
        extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg']
        for file in files:
            if any(file['name'].endswith(ext) for ext in extensions) and file['name'].startswith(shapefile_prefix):
                shapefile_files[file['name']] = self.read_file_from_drive(file['id'])
        
        return shapefile_files

    def read_shapefile_to_gdf(self, folder_id, shapefile_prefix):
        """Download and read a shapefile with all its components."""
        # Download the shapefile components
        shapefile_files = self.download_shapefile_files(folder_id, shapefile_prefix)
        
        if not shapefile_files:
            print(f"Shapefile {shapefile_prefix} not found.")
            return None
        
        # Create an in-memory ZIP file containing all shapefile components
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for filename, file_content in shapefile_files.items():
                zf.writestr(filename, file_content.getvalue())
        
        zip_buffer.seek(0)  # Move to the beginning of the buffer

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, f"{shapefile_prefix}.zip")

            # Write the in-memory ZIP file to disk
            with open(zip_path, 'wb') as f:
                f.write(zip_buffer.getvalue())

            # Read the shapefile from the temporary ZIP file using geopandas
            try:
                gdf = gpd.read_file(f"zip://{zip_path}")
                return gdf
            except Exception as e:
                print(f"Error reading shapefile: {e}")
                return None

    def process_files_in_folder(self, folder_id):
        """Recursively access files in the folder and process shapefiles."""
        items = self.list_files_in_folder(folder_id)

        if not items:
            print(f'No files found in folder with ID: {folder_id}')
            return []

        shapefiles = []

        for item in items:
            # Check if the item is a folder
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # Recursively process subfolders
                subfolder_files = self.process_files_in_folder(item['id'])
                shapefiles.extend(subfolder_files)
            else:
                # Process shapefile only if it matches '.shp' prefix
                if item['name'].endswith('.shp'):
                    shapefile_prefix = item['name'].replace('.shp', '')
                    gdf = self.read_shapefile_to_gdf(folder_id, shapefile_prefix)
                    if gdf is not None:
                        print(f"GeoDataFrame created from {item['name']}:")
                        shapefiles.append({'name': item['name'], 'gdf': gdf})

        return shapefiles