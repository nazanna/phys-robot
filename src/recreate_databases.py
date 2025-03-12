import sqlite3
import os
from constants import RESPONSES_DB_NAME, USERS_DB_NAME
print("Checking if /app/data exists:", os.path.exists("/app/data"))

with open(RESPONSES_DB_NAME, "a"):
    pass
with open(USERS_DB_NAME, "a"):
    pass
conn = sqlite3.connect(USERS_DB_NAME)
cursor = conn.cursor()

# cursor.execute('''
# DROP TABLE users;
# ''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    surname TEXT,
    name TEXT,
    last_name TEXT,
    grade INTEGER,
    school TEXT,
    contact TEXT,
    username TEXT UNIQUE,
    user_id INTEGER UNIQUE PRIMARY KEY,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
''')
conn.commit()
conn.close()


conn = sqlite3.connect(RESPONSES_DB_NAME)
cursor = conn.cursor()
# cursor.execute('''
# DROP TABLE responses;
# ''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    question_index INTEGER,
    response TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, question_index)
);
''')
conn.commit()
conn.close()