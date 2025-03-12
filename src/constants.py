import os

workdir=os.path.dirname(os.path.abspath(__file__))
db_path=os.environ.get('DB_PATH', workdir)
DEBUG = os.environ.get('DEBUG', True)

RESPONSES_DB_NAME = f'{db_path}/user_responses{"_test" if DEBUG else ""}.db'
USERS_DB_NAME = f'{db_path}/users{"_test" if DEBUG else ""}.db'
TOKEN_KEY = f'physbot-{"test" if DEBUG else "main"}-token'
IMAGE_FOLDER_NAME = os.path.join(workdir, 'Problems')
ADMIN_USERNAMES = ['nazanna25', 'andr_zhi', 'iepholog', 'artpiv', 'valeria_chernikova']
MAX_IMAGES_PER_QUESTION = 10
UPLOAD_FREQUENCY = 20 
GOOGLE_SHEET_ANSWERS_ID = "10H3dZbEEVLgHWH3xB9t8HPxAT7tW3QP8VXGvFFSOuD8"
ANSWERS_SHEET_NAME = "Ответы"
QUESTIONS_SHEET_NAME = "Список вопросов"
GOOGLE_DRIVE_FOLDER_ID = "1JghtLbJ7MEvD-33LNtbf6Q2iiy6oEysf"