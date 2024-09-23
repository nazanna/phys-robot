-- SQLite
SELECT username, max(question_index) as answered FROM responses GROUP BY username ORDER BY answered DESC;
-- DELETE from users where 1=1