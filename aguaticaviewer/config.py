from dotenv import load_dotenv
import os
# aguaticaviewer/config.py

#For EpiCollect API
CLIENT_ID = 5603
CLIENT_SECRET = 's2IQsFWgw9Eygz85DsjBb9RduYOtH1xbWq9smTBq'
NAME = 'aguatica_viewer'
SLUG = 'monitoreo-de-agua'


#For Google Drive API
load_dotenv()
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
SCOPES = ['https://www.googleapis.com/auth/drive']  # Read-only access to Google Drive
FOLDER_ID = '1t-u10CLuh7LCYjCKFP4W-3LKSzrwN0W4'



