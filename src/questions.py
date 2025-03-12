import logging
from src.google_sheets_api import GoogleSheetsAPI

logger = logging.getLogger(__name__)

QUESTIONS = {}
QUESTIONS_FOR_GRADE = {}

async def fetch_questions_from_sheets():
    global QUESTIONS, QUESTIONS_FOR_GRADE
    api = GoogleSheetsAPI()
    questions_enumerated = await api.fetch_questions()
    if questions_enumerated is not None:
        global QUESTIONS
        for q in questions_enumerated:
            if len(q) == 2:
                QUESTIONS[int(q[0])] = q[1]
            else:
                break
    for grade in [7, 8, 9, 10, 11]:
        global QUESTIONS_FOR_GRADE
        QUESTIONS_FOR_GRADE[grade] = await api.fetch_questions_for_grade(grade)
    logger.info('QUESTIONS successfully downloaded')
    return QUESTIONS, QUESTIONS_FOR_GRADE 

async def fetch_questions_from_sheets_during_bot_start(app):
    await fetch_questions_from_sheets()
    print('Questions are loaded!')