import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def check():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'orders'")
    for row in cursor.fetchall():
        print(row)

if __name__ == '__main__':
    check()
