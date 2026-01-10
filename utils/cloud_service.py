import os
import zipfile
import shutil
from datetime import datetime
from pathlib import Path
from loguru import logger

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/userinfo.email'
]

class CloudService:
    """Service to handle Google Drive Backup and Restore operations."""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self.token_path = 'token.json'
        self.creds_path = 'credentials.json' # User must provide this from Google Console

    def authenticate(self):
        """Authenticates the user with Google Drive."""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.creds_path):
                    logger.error("credentials.json not found. Please provide Google API credentials.")
                    raise FileNotFoundError("Google API credentials.json is missing.")
                
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
                
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('drive', 'v3', credentials=self.creds)
        return True

    def get_user_email(self):
        """Fetches the authenticated user's email address."""
        if not self.creds or not self.creds.valid:
            if not self.authenticate():
                return None
        
        try:
            user_info_service = build('oauth2', 'v2', credentials=self.creds)
            user_info = user_info_service.userinfo().get().execute()
            return user_info.get('email')
        except Exception as e:
            logger.error(f"Failed to fetch user email: {e}")
            return "Unknown"

    def unlink(self):
        """Deletes the local token file to logout."""
        if os.path.exists(self.token_path):
            os.remove(self.token_path)
            self.creds = None
            self.service = None
            logger.info("Google Drive account unlinked.")
            return True
        return False

    def is_linked(self):
        """Checks if a valid token exists."""
        return os.path.exists(self.token_path)

    def get_or_create_folder(self, folder_name="Inventory_Backups"):
        """Finds or creates the backup folder in Drive."""
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        
        if not items:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            return folder.get('id')
        return items[0].get('id')

    def upload_backup(self, db_path):
        """Zips the database and uploads it to Google Drive."""
        if not self.service:
            self.authenticate()
            
        folder_id = self.get_or_create_folder()
        
        # Create Zip
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        zip_filename = f"backup_{timestamp}.zip"
        zip_path = Path("logs") / zip_filename # Temporary storage in logs dir
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(db_path, arcname=os.path.basename(db_path))
            # If system_config file existed, we would add it here
            
        # Upload
        file_metadata = {
            'name': zip_filename,
            'parents': [folder_id]
        }
        media = MediaFileUpload(str(zip_path), mimetype='application/zip')
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        
        # Cleanup temp zip
        if zip_path.exists():
            os.remove(zip_path)
            
        logger.info(f"Cloud Backup successful: {zip_filename} | Drive ID: {file.get('id')}")
        return zip_filename

    def list_backups(self):
        """Lists available backup files in the Drive folder, sorted by newest first."""
        if not self.service:
            self.authenticate()
            
        folder_id = self.get_or_create_folder()
        query = f"'{folder_id}' in parents and trashed = false"
        # Order by createdTime descending
        results = self.service.files().list(
            q=query, 
            spaces='drive', 
            fields='files(id, name, createdTime)',
            orderBy='createdTime desc'
        ).execute()
        return results.get('files', [])

    def download_and_restore(self, file_id, db_path):
        """Downloads a backup and restores the local database."""
        if not self.service:
            self.authenticate()
            
        temp_zip = Path("logs") / "temp_restore.zip"
        
        # Download
        request = self.service.files().get_media(fileId=file_id)
        with open(temp_zip, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        
        # Extract and Replace
        with zipfile.ZipFile(temp_zip, 'r') as zipf:
            zipf.extractall("logs/temp_restore")
            
        # Assuming the first file in the zip is the DB
        extracted_files = list(Path("logs/temp_restore").glob("*.db"))
        if extracted_files:
            # Backup current DB to be safe before overwrite
            shutil.copy2(db_path, f"{db_path}.bak")
            shutil.move(str(extracted_files[0]), db_path)
            
        # Cleanup
        shutil.rmtree("logs/temp_restore")
        os.remove(temp_zip)
        
        logger.info(f"Database restored from Cloud ID: {file_id}")
        return True
