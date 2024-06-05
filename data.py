import sqlite3

conn = sqlite3.connect('C:/Users/USER/Desktop/db_isuku/isukura')
cursor = conn.cursor()

cursor.execute('SELECT * FROM users')
users = cursor.fetchall()

for user in users:
    print(user)

conn.close()
