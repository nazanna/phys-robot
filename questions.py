from google_sheets_api import GoogleSheetsAPI

QUESTIONS = []
QUESTIONS_FOR_GRADE = {}

async def fetch_questions_from_sheets():
    global QUESTIONS, QUESTIONS_FOR_GRADE
    api = GoogleSheetsAPI()
    questions_enumerated = await api.fetch_questions()
    if questions_enumerated is not None:
        global QUESTIONS
        QUESTIONS = [q[1] for q in questions_enumerated]

    for grade in [7, 8, 9, 10, 11]:
        global QUESTIONS_FOR_GRADE
        QUESTIONS_FOR_GRADE[grade] = await api.fetch_questions_for_grade(grade)
    
    return QUESTIONS, QUESTIONS_FOR_GRADE 