from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
import logging

logger = logging.getLogger(__name__)

from constants import WORKDIR, GOOGLE_SHEET_ANSWERS_ID, QUESTIONS_SHEET_NAME
from db_api import get_users_grade

class GoogleSheetsAPI:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    def __init__(self, id=GOOGLE_SHEET_ANSWERS_ID):
        creds = None
        self.SPREADSHEET_ID = id
        if not creds:
            creds = service_account.Credentials.from_service_account_file(f"{WORKDIR}/secrets/credentials.json").with_scopes(self.SCOPES)
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
                logger.info("No questions found.")
                return
            return questions

        except HttpError as err:
            logger.error(err)
            raise err

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
            logger.error(err)
            raise err

    async def upload_student_data_and_answers(self, user_id: int, data: list[str], full: bool = False):
        grade = await get_users_grade(user_id)
        sheet_name = f'Ответы {grade} класс'
        if full:
            sheet_name += ' full'
        row_index = await self._find_user_row(sheet_name, user_id)
        await self.update_row(sheet_name, row_index, data)
    
    async def update_row(self, sheet_name: str, row_index: int, values: list[str]):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            last_column = await self._index_to_column_letter(len(values))
            range_name = f'{sheet_name}!A{row_index}:{last_column}{row_index}' 
            
            service.spreadsheets().values().update(
                spreadsheetId=self.SPREADSHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body = {
                    'values': [values]
                }
            ).execute()
        except HttpError as err:
            logger.error(err)
            raise err


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
                logger.info("No data found.")
                return 1

            for i, user in enumerate(users):
                if user[0] == str(user_id):
                    return i + 1

            return len(users) + 1
        except HttpError as err:
            logger.error(err)
            raise err


    async def _index_to_column_letter(self, index):
        letter = ''
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            letter = chr(65 + remainder) + letter  # 65 is the ASCII value for 'A'
        return letter
    