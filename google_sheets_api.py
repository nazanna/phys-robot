from datetime import datetime
import asyncio
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from constants import workdir, GOOGLE_SHEET_ANSWERS_ID
from google.oauth2 import service_account

class GoogleSheetsAPI:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    RANGE_OF_NAMES = "A:B"

    def __init__(self, id=GOOGLE_SHEET_ANSWERS_ID):
        creds = None
        self.SPREADSHEET_ID = id
        if not creds:
            creds = service_account.Credentials.from_service_account_file(f"{workdir}/credentials.json").with_scopes(self.SCOPES)
            if not creds.valid:
                creds.refresh(Request())
        self.creds = creds

    async def get_list_of_students(self, group_name: str):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            sheet = service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=self.SPREADSHEET_ID, range=f'{group_name}!{self.RANGE_OF_NAMES}')
                .execute()
            )
            students = result.get("values", [])

            if not students:
                print("No data found.")
                return

            return [f'{student[0]} {student[1]}' for student in students[1:]]
        except HttpError as err:
            print(err)

    async def get_timetable(self):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            sheet = service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=self.SPREADSHEET_ID, range=f'Sheet1!A:D')
                .execute()
            )
            students = result.get("values", [])

            if not students:
                print("No data found.")
                return

            return students[1:]
        except HttpError as err:
            print(err)

    async def upload_answers(self, answers: list[list[str]]):
        try:
            sheet_name = 'Ответы'
            service = build("sheets", "v4", credentials=self.creds)
            attendance_range = f'{sheet_name}!A:{await self._index_to_column_letter(4)}'
            service.spreadsheets().values().update(
                spreadsheetId=self.SPREADSHEET_ID,
                range=attendance_range,
                valueInputOption='RAW',
                body={
                    'values': answers
                }
            ).execute()
        except HttpError as err:
            print(err)

    async def upload_personal_data(self, data: list[list[str]]):
        try:
            sheet_name = 'Школьники'
            service = build("sheets", "v4", credentials=self.creds)
            attendance_range = f'{sheet_name}!A:{await self._index_to_column_letter(7)}'
            service.spreadsheets().values().update(
                spreadsheetId=self.SPREADSHEET_ID,
                range=attendance_range,
                valueInputOption='RAW',
                body={
                    'values': data
                }
            ).execute()
        except HttpError as err:
            print(err)

    async def upload_personal_student_data(self, user_id: int, data: list[str]):
        sheet_name = 'Школьники'
        row_index = await self._find_user_row(sheet_name, user_id)
        await self.update_row(row_index, data)
            


    async def update_row(self, row_index: int, values: list[str]):
        try:
            sheet_name = 'Школьники'  # Specify the sheet name where the row needs to be updated
            service = build("sheets", "v4", credentials=self.creds)
            last_column = await self._index_to_column_letter(len(values))
            print(last_column)
            range_name = f'{sheet_name}!A{row_index}:{last_column}{row_index}'  # Adjust the range according to the number of columns
            
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


    async def _get_first_empty_column_index(self, group_name: str):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            # Call the Sheets API
            result = service.spreadsheets().values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range=f"{group_name}!1:1"
            ).execute()

            row_values = result.get('values', [])[0] if 'values' in result else []

            return len(row_values) + 1

        except HttpError as err:
            print(err)


    async def _get_last_filled_column(self, group_name: str):
        return await self._index_to_column_letter(await self._get_first_empty_column_index(group_name) - 1)
