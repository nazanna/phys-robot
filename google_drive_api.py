from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from constants import workdir, IMAGE_FOLDER_NAME, GOOGLE_DRIVE_FOLDER_ID 
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload 
import io 
import os
import logging

logger = logging.getLogger(__name__)

class FileNotFoundException(Exception):
    pass

class GoogleDriveAPI:
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    def __init__(self, id=GOOGLE_DRIVE_FOLDER_ID):
        creds = None
        self.FOLDER_ID = id
        if not creds:
            creds = service_account.Credentials.from_service_account_file(f"{workdir}/secrets/credentials.json").with_scopes(self.SCOPES)
            if not creds.valid:
                creds.refresh(Request())
        self.creds = creds    
        self.service = build('drive', 'v3', credentials=self.creds)

    async def download_file(self, file_id, file_name):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=5 * 1024 * 1024) 
        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.info(f'Download {int(status.progress() * 100)}% for {file_name}.')
        
        file_path = os.path.join(IMAGE_FOLDER_NAME, file_name)
        with open(file_path, 'wb') as f:
            f.write(fh.getvalue())
        logger.info(f'File saved to {file_path}')
        
    async def download_file_by_name(self, file_name):
        results = self.service.files().list(q=f"name='{file_name}'",
                                   fields="files(id, name)").execute()
        files = results.get('files', [])

        if not files:
            logger.info(f"File {file_name} not found.")
            raise FileNotFoundException()

        file_id = files[0]['id'] 
        
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=5 * 1024 * 1024) 
        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.info(f'Download {int(status.progress() * 100)}% for {file_name}.')
        
        file_path = os.path.join(IMAGE_FOLDER_NAME, file_name)
        with open(file_path, 'wb') as f:
            f.write(fh.getvalue())
        logger.info(f'File saved to {file_path}')


    async def download_files_from_drive(self, new_only = False):
        query = f"'{self.FOLDER_ID}' in parents"
        results = self.service.files().list(q=query, fields="files(id, name)", pageSize=1000).execute() # TODO: might be a problem when we exceed 1000 files
        items = results.get('files', [])
        if not items:
            logger.info('No files found.')
            return

        if not os.path.exists(IMAGE_FOLDER_NAME):
            os.mkdir(IMAGE_FOLDER_NAME)  
        logger.info(f'Found {len(items)} files in Google folder')  
        number_of_downloaded = 0
        for item in items:
            file_id = item['id']
            file_name = item['name']
            if not (new_only and os.path.exists(os.path.join(IMAGE_FOLDER_NAME, file_name))): 
                await self.download_file(file_id, file_name)
                number_of_downloaded += 1
        logger.info(f'All {number_of_downloaded} files downloaded successfully.')