import sqlite3

# Создаем или открываем базу данных
conn = sqlite3.connect('users_test.db')
cursor = conn.cursor()

# Создаем таблицу, если она не существует

# cursor.execute('''
# CREATE TABLE IF NOT EXISTS responses (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     user_id INTEGER,
#     question_index INTEGER,
#     response TEXT,
#     username TEXT,
#     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# )
# ''')

cursor.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username INTEGER UNIQUE,
    surname TEXT,
    name TEXT,
    last_name TEXT,
    grade INTEGER,
    school TEXT,
    contact TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()