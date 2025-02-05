from google_sheets_api import GoogleSheetsAPI
import sqlite3
from constants import users_db_name, responses_db_name
import logging
import asyncio

async def upload_student_answers_to_sheets(user_id: int):
    try:
        conn = sqlite3.connect(users_db_name)
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT user_id, surname, name, last_name, grade, school, contact, username
            FROM users
            WHERE user_id={user_id}
        ''')
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return False

        data = list(rows[0])
        print(data)
        conn = sqlite3.connect(responses_db_name)
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
            print(answers)
            data += answers

        api = GoogleSheetsAPI()
        success = await api.upload_personal_student_data(user_id, data)
        if not success:
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error uploading personal data to sheets: {str(e)}")
        return False

asyncio.run(upload_student_answers_to_sheets(1234))