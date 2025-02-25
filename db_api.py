import sqlite3
import logging
from telegram.ext import ContextTypes
from constants import users_db_name

class NoGradeException(Exception):
    pass

async def get_users_grade(user_id: int, context: ContextTypes.DEFAULT_TYPE = None, force_db: bool = False):
    if context and 'grade' in context.user_data and not force_db:
        return context.user_data['grade']
    conn = sqlite3.connect(users_db_name)
    cursor = conn.cursor()
    cursor.execute(f'SELECT grade FROM users WHERE user_id={user_id}')
    rows = cursor.fetchall()
    conn.close()
    if len(rows) == 0:
        logging.error(f"User {user_id} doesn't have grade specified")
        raise NoGradeException(f"User {user_id} doesn't have grade specified")
    grade = rows[0][0]
    if context:
        context.user_data['grade'] = grade
    return grade

