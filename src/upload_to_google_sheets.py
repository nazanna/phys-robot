import sqlite3
import logging
from constants import USERS_DB_NAME, RESPONSES_DB_NAME
from google_sheets_api import GoogleSheetsAPI

logger = logging.getLogger(__name__)

async def upload_student_answers_to_sheets(user_id: int, full: bool = False):
    try:
        conn = sqlite3.connect(USERS_DB_NAME)
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT user_id, last_name, name, surname, grade, school, contact, username
            FROM users
            WHERE user_id={user_id}
        ''')
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return False

        data = list(rows[0])
        conn = sqlite3.connect(RESPONSES_DB_NAME)
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT user_id, question_index, response 
            FROM responses
            WHERE user_id={user_id}
            ORDER BY question_index
        ''')
        rows = cursor.fetchall()
        conn.close()

        if rows:
            answers = [row[2] for row in rows]
            data += answers

        api = GoogleSheetsAPI()
        success = await api.upload_student_data_and_answers(user_id, data, full)
        if not success:
            logger.info(f"Uploaded student {user_id} answers to sheets")
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Error uploading personal data to sheets: {str(e)}")
        raise e
