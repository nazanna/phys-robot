import sqlite3

# Connect to the source database
source_db = 'user_responses_test.db'
target_db = 'users_test.db'

# Connect to the source and target databases
source_conn = sqlite3.connect(source_db)
target_conn = sqlite3.connect(target_db)

# Create a cursor for each database
source_cursor = source_conn.cursor()
target_cursor = target_conn.cursor()

# Create the target table if it doesn't exist
target_cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT
)
''')

# Select first and last names from the source database
source_cursor.execute('''
SELECT DISTINCT user_id FROM responses
''')

# Fetch all results
ids = source_cursor.fetchall()
# print(ids)

for id in ids:
    uid = id[0]
    source_cursor.execute(f'SELECT response FROM responses WHERE user_id = {uid} and question_index=0 ORDER BY updated_at DESC LIMIT 1')
    last_name = source_cursor.fetchone()
    source_cursor.execute(f'SELECT response FROM responses WHERE user_id = {uid} and question_index=1 ORDER BY updated_at DESC LIMIT 1')
    first_name = source_cursor.fetchone()
    if last_name:
        target_cursor.execute('''
        INSERT INTO users (user_id, first_name, last_name)
        VALUES (?, ?, ?)
        ''', (uid, first_name[0], last_name[0]))

# Commit the changes and close the connections
target_conn.commit()
source_conn.close()
target_conn.close()

print("Data transfer complete.")
