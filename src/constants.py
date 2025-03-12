import os

WORKDIR=os.environ.get('WORKDIR', '/app')
DB_PATH=os.environ.get('DB_PATH', WORKDIR)
DEBUG = os.environ.get('DEBUG', True)

RESPONSES_DB_NAME = f'{DB_PATH}/user_responses{"_test" if DEBUG else ""}.db'
USERS_DB_NAME = f'{DB_PATH}/users{"_test" if DEBUG else ""}.db'
TOKEN_KEY = f'physbot-{"test" if DEBUG else "main"}-token'
GOOGLE_CREDENTIALS_KEY="google-credentials"
IMAGE_FOLDER_NAME = os.path.join(WORKDIR, 'Problems')
ADMIN_USERNAMES = ['nazanna25', 'andr_zhi', 'iepholog', 'artpiv', 'valeria_chernikova']
MAX_IMAGES_PER_QUESTION = 10
UPLOAD_FREQUENCY = 20 
GOOGLE_SHEET_ANSWERS_ID = "10H3dZbEEVLgHWH3xB9t8HPxAT7tW3QP8VXGvFFSOuD8"
ANSWERS_SHEET_NAME = "Ответы"
QUESTIONS_SHEET_NAME = "Список вопросов"
GOOGLE_DRIVE_FOLDER_ID = "1JghtLbJ7MEvD-33LNtbf6Q2iiy6oEysf"