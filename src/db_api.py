import sqlite3
import logging
from telegram.ext import ContextTypes
from constants import USERS_DB_NAME

class NoGradeException(Exception):
    pass

async def get_users_grade(user_id: int, context: ContextTypes.DEFAULT_TYPE = None, force_db: bool = False): # type: ignore
    if context and 'grade' in context.user_data and not force_db: # type: ignore
        return context.user_data['grade'] # type: ignore
    conn = sqlite3.connect(USERS_DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f'SELECT grade FROM users WHERE user_id={user_id}')
    rows = cursor.fetchall()
    conn.close()
    if len(rows) == 0:
        logging.error(f"User {user_id} doesn't have grade specified")
        raise NoGradeException(f"User {user_id} doesn't have grade specified")
    grade = rows[0][0]
    if context:
        context.user_data['grade'] = grade # type: ignore
    return grade

async def run_select(query: str, db: str):
    assert query.upper().startswith('SELECT')
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

async def get_all_user_ids() -> list[int]:
    query = "SELECT user_id FROM users"
    rows = await run_select(query, USERS_DB_NAME)
    return [row[0] for row in rows]
