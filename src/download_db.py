import asyncio, sqlite3
from src.constants import USERS_DB_NAME
from src.upload_to_google_sheets import upload_student_answers_to_sheets

async def update_all_answers():
    conn = sqlite3.connect(USERS_DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT user_id, last_name, name, surname, grade, school, contact, username
        FROM users
    ''')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return False
    data = [list(rows[i]) for i in range(len(rows))]
    for user_index in range(len(data)):
        user_id = data[user_index][0]
        if data[user_index][4] in range(7,12):
            await upload_student_answers_to_sheets(user_id, full=True)

asyncio.run(update_all_answers())