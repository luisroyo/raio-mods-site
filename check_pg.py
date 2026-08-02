import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def check():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT id, status, external_reference, created_at, key_assigned_id FROM orders ORDER BY id DESC LIMIT 5")
    for row in cursor.fetchall():
        print(row)

if __name__ == '__main__':
    check()
