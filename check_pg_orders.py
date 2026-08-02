import os
import psycopg2
from dotenv import load_dotenv
import json

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def check():
    print(f"DATABASE_URL: {DATABASE_URL}")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT id, status, external_reference, created_at, key_assigned_id FROM orders ORDER BY id DESC LIMIT 10")
    orders = cursor.fetchall()
    print("Orders in PG:", orders)
    
    cursor.execute("SELECT mercado_pago_token FROM config WHERE id = 1")
    config = cursor.fetchone()
    print("MP Token in PG:", config)
    
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    print(f"db_path: {db_path}")
    if os.path.exists(db_path):
        conn_sq = sqlite3.connect(db_path)
        cur_sq = conn_sq.cursor()
        cur_sq.execute("SELECT id, status, external_reference, created_at, key_assigned_id FROM orders ORDER BY id DESC LIMIT 10")
        print("Orders in SQLite:", cur_sq.fetchall())
    
if __name__ == '__main__':
    check()
