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
        self.counter_for_missing_files = 0

    def _authenticate(self):
        """Authenticate using the service account credentials."""
        return service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

    def _build_service(self):
        """Build the Google Drive API service."""
        return build('drive', 'v3', credentials=self.credentials)

    def list_files_in_folder(self, folder_id, page_size=100):
        """List all files in a specific Google Drive folder, including folder name, and handle pagination."""
        all_files = []
        next_page_token = None
        page_count = 0

        try:
            # Get the folder name by using the get method
            folder = self.service.files().get(fileId=folder_id, fields='name').execute()
            folder_name = folder['name']  # Extract the folder name

            while True:
                results = self.service.files().list(
                    q=f"'{folder_id}' in parents",
                    pageSize=page_size,
                    fields="nextPageToken, files(id, name, mimeType), incompleteSearch",
                    pageToken=next_page_token,
                    orderBy="name"
                ).execute()

                files = results.get('files', [])

                for file in files:
                    file['folder_name'] = folder_name  # Attach the folder name to each file

                all_files.extend(files)
                page_count += 1

                print(f"Page {page_count}: Retrieved {len(files)} files")
                if results.get('incompleteSearch'):
                    print("Warning: Search results may be incomplete")

                next_page_token = results.get('nextPageToken')
                if not next_page_token:
                    break

            if not all_files:
                print(f"No files found in folder with ID: {folder_id}")
            else:
                print(f"Total files found: {len(all_files)}")
                for file in all_files:
                    print(f"- {file['name']} (ID: {file['id']}, Type: {file['mimeType']})")

            return all_files

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []

    def read_file_from_drive(self, file_id):
            # Get the file metadata, including the name
            file_metadata = self.service.files().get(fileId=file_id, fields='name').execute()

            # Print the filename
            file_name = file_metadata.get('name')
            print(f"Downloading file: {file_name}")

            """Read file content directly from Google Drive into memory."""
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()  # In-memory buffer to store file contents
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                #print(f"Download {int(status.progress() * 100)}% complete.")
            
            # After downloading, seek to the start of the BytesIO buffer
            fh.seek(0)
            return fh
    
    def download_shapefile_files(self, folder_id, shapefile_prefix):
        """Download all files belonging to a shapefile (shp, shx, dbf, etc.)"""
        files = self.list_files_in_folder(folder_id)
        shapefile_files = {}
        
        # Identify the required components (.shp, .shx, .dbf, etc.)
        extensions = ['.shp', '.shx', '.dbf']
        for file in files:
            if any(file['name'].endswith(ext) for ext in extensions) and file['name'].startswith(shapefile_prefix):
                shapefile_files[file['name']] = self.read_file_from_drive(file['id'])
        
        return shapefile_files

    def read_shapefile_to_gdf(self, folder_id, shapefile_prefix, folder_name):
        """Download and read a shapefile with all its components."""
        shapefile_files = self.download_shapefile_files(folder_id, shapefile_prefix)

        required_extensions = ['.shp', '.shx', '.dbf']
        missing_extensions = [ext for ext in required_extensions if
                              not any(file_name.endswith(ext) for file_name in shapefile_files)]

        if not all(any(file_name.endswith(ext) for file_name in shapefile_files) for ext in required_extensions):
            print(
                f"Missing required shapefile components for {shapefile_prefix}: {', '.join(missing_extensions)}. Skipping...")
            self.counter_for_missing_files += 1
            return None

        if not shapefile_files:
            print(f"Shapefile {shapefile_prefix} not found.")
            return None

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for filename, file_content in shapefile_files.items():
                zf.writestr(filename, file_content.getvalue())

        zip_buffer.seek(0)

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, f"{shapefile_prefix}.zip")

            with open(zip_path, 'wb') as f:
                f.write(zip_buffer.getvalue())

            try:
                gdf = gpd.read_file(f"zip://{zip_path}")
                gdf.attrs['folder_name'] = folder_name  # Store folder name in GDF attributes
                return gdf
            except Exception as e:
                print(f"Error reading shapefile: {e}")
                return None

    def process_files_in_folder(self, folder_id):
        #Access files in the folder and process shapefiles, returning a list of GeoDataFrames with folder and file names.
        items = self.list_files_in_folder(folder_id)

        if not items:
            print(f'No files found in folder with ID: {folder_id}')
            return []

        gdf_list = []  # List to hold GeoDataFrames with their folder and file names

        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # Process subfolders
                subfolder_gdfs = self.process_files_in_folder(item['id'])  # Recursively process subfolder
                gdf_list.extend(subfolder_gdfs)  # Add subfolder GDFs to the main list
            else:
                # Process shapefile
                if item['name'].endswith('.shp'):
                    shapefile_prefix = item['name'].replace('.shp', '')
                    folder_name = item['folder_name']  # Get the folder name from the item
                    gdf = self.read_shapefile_to_gdf(folder_id, shapefile_prefix,
                                                     folder_name)  # Pass the correct folder name
                    if gdf is not None:
                        print(f"GeoDataFrame created from {item['name']} in folder {folder_name}:")
                        # Append a dictionary with folder name, file name, and GeoDataFrame
                        gdf_list.append({'folder_name': folder_name, 'file_name': item['name'], 'gdf': gdf})

        return gdf_list  # Return the list of GeoDataFrames with their folder and file names



