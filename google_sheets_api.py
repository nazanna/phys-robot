from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from constants import workdir, IMAGE_FOLDER_NAME, GOOGLE_SHEET_ANSWERS_ID, ANSWERS_SHEET_NAME, QUESTIONS_SHEET_NAME
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload 
import io 
import asyncio
import os

class GoogleSheetsAPI:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", 'https://www.googleapis.com/auth/drive.readonly']
    def __init__(self, id=GOOGLE_SHEET_ANSWERS_ID):
        creds = None
        self.SPREADSHEET_ID = id
        if not creds:
            creds = service_account.Credentials.from_service_account_file(f"{workdir}/credentials.json").with_scopes(self.SCOPES)
            if not creds.valid:
                creds.refresh(Request())
        self.creds = creds

    async def fetch_questions(self):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            range_name = f'{QUESTIONS_SHEET_NAME}!A:B' 
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=self.SPREADSHEET_ID, range=range_name)
                .execute()
            )
            questions = result.get("values", [])

            if not questions:
                print("No questions found.")
                return
            return questions

        except HttpError as err:
            print(err)


    async def fetch_questions_for_grade(self, grade: int):
        try:
            sheet_name = f'{grade} класс'
            service = build("sheets", "v4", credentials=self.creds)
            range_name = f'{sheet_name}!A:A'  
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=self.SPREADSHEET_ID, range=range_name)
                .execute()
            )
            questions = result.get("values", [])

            return [q[0] for q in questions]

        except HttpError as err:
            print(err)

    async def upload_student_data_and_answers(self, user_id: int, data: list[str]):
        row_index = await self._find_user_row(ANSWERS_SHEET_NAME, user_id)
        await self.update_row(row_index, data)
            

    async def update_row(self, row_index: int, values: list[str]):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            last_column = await self._index_to_column_letter(len(values))
            range_name = f'{ANSWERS_SHEET_NAME}!A{row_index}:{last_column}{row_index}'  # Adjust the range according to the number of columns
            
            service.spreadsheets().values().update(
                spreadsheetId=self.SPREADSHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body = {
                    'values': [values]  # Wrap values in another list to match the expected format
                }
            ).execute()
        except HttpError as err:
            print(err)


    async def _find_user_row(self, sheet_name: str, user_id: int):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            sheet = service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=self.SPREADSHEET_ID, range=f'{sheet_name}!A:A')
                .execute()
            )
            users = result.get("values", [])

            if not users:
                print("No data found.")
                return

            for i, user in enumerate(users):
                if user[0] == str(user_id):
                    return i + 1

            return len(users) + 1
        except HttpError as err:
            print(err)


    async def _index_to_column_letter(self, index):
        letter = ''
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            letter = chr(65 + remainder) + letter  # 65 is the ASCII value for 'A'
        return letter
    

    async def download_file(self, service, file_id, file_name, download_folder):
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=1024 * 1024)  # Set chunk size to 1 MB
        status, done = downloader.next_chunk()  
        print(f'Download {int(status.progress() * 100)}% for {file_name}.')
        
        file_path = os.path.join(download_folder, file_name)
        with open(file_path, 'wb') as f:
            f.write(fh.getvalue())
        print(f'File saved to {file_path}')

    async def download_files_from_drive(self, folder_id):
        service = build('drive', 'v3', credentials=self.creds)
        query = f"'{folder_id}' in parents"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return

        for item in items:
            file_id = item['id']
            file_name = item['name']
            await self.download_file(service, file_id, file_name, './Problems')

        print('All files downloaded successfully.')