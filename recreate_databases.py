import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute('''
DROP TABLE users;
CREATE TABLE users (
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


conn = sqlite3.connect('user_responses.db')
cursor = conn.cursor()
cursor.execute('''
DROP TABLE responses;
CREATE TABLE responses (
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