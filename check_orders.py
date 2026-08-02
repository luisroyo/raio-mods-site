import sqlite3
def check():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, status, external_reference, created_at FROM orders ORDER BY id DESC LIMIT 5")
    for row in cursor.fetchall():
        print(row)
if __name__ == '__main__':
    check()
