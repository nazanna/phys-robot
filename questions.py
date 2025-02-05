from google_sheets_api import GoogleSheetsAPI
import asyncio
QUESTIONS = []
QUESTIONS_FOR_GRADE = {}

async def fetch_questions_from_sheets():
    global QUESTIONS, QUESTIONS_FOR_GRADE
    api = GoogleSheetsAPI()
    QUESTIONS = await api.fetch_questions()
    for grade in [7,8,9,10,11]:
        QUESTIONS_FOR_GRADE[grade] = await api.fetch_questions_for_grade(grade)

asyncio.run(fetch_questions_from_sheets())
