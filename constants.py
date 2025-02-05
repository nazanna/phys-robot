import os

workdir=os.path.dirname(os.path.abspath(__file__))
DEBUG = 'andrew' in workdir

responses_db_name = f'{workdir}/user_responses{"_test" if DEBUG else ""}.db'
users_db_name = f'{workdir}/users{"_test" if DEBUG else ""}.db'
token_key = f"physbot-{"test" if DEBUG else "main"}-token"
IMAGE_FOLDER_NAME = 'Problems'
ADMIN_USERNAMES = ['nazanna25', 'andr_zhi', 'IEPHOlog', 'artpiv', 'valeria_chernikova']
MAX_IMAGES_PER_QUESTION = 10
UPLOAD_FREQUENCY = 10 # uploads student's answers to google sheets every UPLOAD_FREQUENCY questions

GOOGLE_SHEET_ANSWERS_ID = "10H3dZbEEVLgHWH3xB9t8HPxAT7tW3QP8VXGvFFSOuD8"
ANSWERS_SHEET_NAME = "Ответы"
QUESTIONS_SHEET_NAME = "Список вопросов"