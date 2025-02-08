from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from constants import workdir, IMAGE_FOLDER_NAME, GOOGLE_DRIVE_FOLDER_ID 
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload 
import io 
import os

class GoogleDriveAPI:
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    def __init__(self, id=GOOGLE_DRIVE_FOLDER_ID):
        creds = None
        self.FOLDER_ID = id
        if not creds:
            creds = service_account.Credentials.from_service_account_file(f"{workdir}/credentials.json").with_scopes(self.SCOPES)
            if not creds.valid:
                creds.refresh(Request())
        self.creds = creds    

    async def download_file(self, service, file_id, file_name):
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=5 * 1024 * 1024) 
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f'Download {int(status.progress() * 100)}% for {file_name}.')
        
        file_path = os.path.join(IMAGE_FOLDER_NAME, file_name)
        with open(file_path, 'wb') as f:
            f.write(fh.getvalue())
        print(f'File saved to {file_path}')

    async def download_files_from_drive(self):
        service = build('drive', 'v3', credentials=self.creds)
        query = f"'{self.FOLDER_ID}' in parents"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return

        for item in items:
            file_id = item['id']
            file_name = item['name']
            await self.download_file(service, file_id, file_name)

        print('All files downloaded successfully.')