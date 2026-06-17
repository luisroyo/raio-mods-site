import os
import re
import sqlite3
import psycopg2
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '../.env'))

DATABASE_URL = os.getenv('DATABASE_URL')

class PostgreSQLRow(dict):
    """A row object that acts like sqlite3.Row (both dict and tuple-like access)."""
    def __init__(self, cursor, row):
        super().__init__(zip([col[0] for col in cursor.description], row))
        self._row = row

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._row[key]
        return super().__getitem__(key)

    def keys(self):
        return list(super().keys())

class PostgreSQLCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        self._lastrowid = None

    def execute(self, query, params=None):
        # Translate empty double quotes "" to single quotes '' for Postgres SQL string compatibility
        query = query.replace('""', "''")

        # 1. Translate AUTOINCREMENT to SERIAL for table creation
        if "AUTOINCREMENT" in query.upper():
            query = re.sub(r'(?i)\bINTEGER PRIMARY KEY AUTOINCREMENT\b', 'SERIAL PRIMARY KEY', query)

        # 2. Check if it's an INSERT statement to simulate lastrowid
        is_insert = query.strip().upper().startswith('INSERT')
        if is_insert and 'RETURNING' not in query.upper():
            query += ' RETURNING id'

        # 3. Convert sqlite parameter style '?' to postgres '%s'
        if params is not None:
            if not isinstance(params, (list, tuple, dict)):
                params = (params,)
            elif isinstance(params, list):
                params = tuple(params)
            
            if isinstance(params, (list, tuple)) and len(params) == 0:
                params = None
            elif isinstance(params, dict) and len(params) == 0:
                params = None
        
        if params is not None:
            query = query.replace('?', '%s')

        # 4. Execute and convert psycopg2 exceptions to sqlite3 exceptions
        try:
            if params is not None:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            if is_insert:
                try:
                    row = self.cursor.fetchone()
                    if row:
                        self._lastrowid = row[0]
                except Exception:
                    self._lastrowid = None
        except Exception as e:
            raise sqlite3.OperationalError(str(e)) from e

        return self

    def fetchone(self):
        try:
            row = self.cursor.fetchone()
        except Exception as e:
            raise sqlite3.OperationalError(str(e)) from e
            
        if row is None:
            return None
        return PostgreSQLRow(self.cursor, row)

    def fetchall(self):
        try:
            rows = self.cursor.fetchall()
        except Exception as e:
            raise sqlite3.OperationalError(str(e)) from e
            
        return [PostgreSQLRow(self.cursor, r) for r in rows]

    def close(self):
        self.cursor.close()

    @property
    def lastrowid(self):
        return self._lastrowid

    def __iter__(self):
        return self

    def __next__(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row

    def __getattr__(self, name):
        return getattr(self.cursor, name)

class PostgreSQLConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        try:
            return PostgreSQLCursorWrapper(self.conn.cursor())
        except Exception as e:
            raise sqlite3.OperationalError(str(e)) from e

    def execute(self, query, params=None):
        cursor = self.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self):
        try:
            self.conn.commit()
        except Exception as e:
            raise sqlite3.OperationalError(str(e)) from e

    def rollback(self):
        try:
            self.conn.rollback()
        except Exception:
            pass

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()

def get_db_connection():
    if DATABASE_URL and (DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://')):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return PostgreSQLConnectionWrapper(conn)
        except Exception as e:
            print(f"[BD Wrapper] Erro ao conectar ao PostgreSQL, fallback para SQLite: {e}")
            
    # Fallback to SQLite
    db_path = os.path.join(basedir, '../database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn