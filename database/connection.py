import sqlite3
import os

from database.schema import create_tables
from database.migrations_schema import run_schema_migrations
from database.migrations_data import run_data_migrations
from database.models import get_db_connection, PostgreSQLConnectionWrapper

def get_db_path():
    basedir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(basedir, '../database.db')

def init_db():
    DATABASE_URL = os.getenv('DATABASE_URL')
    is_postgres_configured = DATABASE_URL and (DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://'))
    
    if is_postgres_configured:
        print("[BD] Verificando banco de dados em: PostgreSQL (Neon)")
    else:
        db_path = get_db_path()
        print(f"[BD] Verificando banco de dados em: {db_path}")
    
    conn = get_db_connection()
    is_real_postgres = isinstance(conn, PostgreSQLConnectionWrapper)
    
    if is_real_postgres:
        conn.conn.autocommit = True
    cursor = conn.cursor()
    
    if is_real_postgres:
        # Criar funções customizadas de compatibilidade com SQLite date(...)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION date(time_val timestamp, mod1 text)
        RETURNS date AS $$
        BEGIN
            RETURN (time_val + mod1::interval)::date;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION date(time_val timestamp, mod1 text, mod2 text)
        RETURNS date AS $$
        BEGIN
            RETURN (time_val + mod1::interval + mod2::interval)::date;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION date(time_str text, mod1 text)
        RETURNS date AS $$
        DECLARE
            ts timestamp;
        BEGIN
            IF time_str = 'now' THEN
                ts := CURRENT_TIMESTAMP;
            ELSE
                ts := time_str::timestamp;
            END IF;
            RETURN (ts + mod1::interval)::date;
        END;
        $$ LANGUAGE plpgsql STABLE;
        """)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION date(time_str text, mod1 text, mod2 text)
        RETURNS date AS $$
        DECLARE
            ts timestamp;
        BEGIN
            IF time_str = 'now' THEN
                ts := CURRENT_TIMESTAMP;
            ELSE
                ts := time_str::timestamp;
            END IF;
            RETURN (ts + mod1::interval + mod2::interval)::date;
        END;
        $$ LANGUAGE plpgsql STABLE;
        """)

        # Criar funções customizadas de compatibilidade com SQLite datetime(...)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION datetime(time_val timestamp)
        RETURNS timestamp AS $$
        BEGIN
            RETURN time_val;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION datetime(time_str text)
        RETURNS timestamp AS $$
        BEGIN
            IF time_str = 'now' THEN
                RETURN CURRENT_TIMESTAMP;
            ELSE
                RETURN time_str::timestamp;
            END IF;
        END;
        $$ LANGUAGE plpgsql STABLE;
        """)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION datetime(time_str text, mod1 text)
        RETURNS timestamp AS $$
        DECLARE
            ts timestamp;
        BEGIN
            IF time_str = 'now' THEN
                ts := CURRENT_TIMESTAMP;
            ELSE
                ts := time_str::timestamp;
            END IF;
            RETURN ts + mod1::interval;
        END;
        $$ LANGUAGE plpgsql STABLE;
        """)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION datetime(time_val timestamp, mod1 text)
        RETURNS timestamp AS $$
        BEGIN
            RETURN time_val + mod1::interval;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """)
    

    # 1. Criação do Schema Base
    create_tables(cursor)

    # 2. Migrações Estruturais (Schema)
    run_schema_migrations(cursor, is_real_postgres)

    # 3. Migrações de Dados (Data)
    run_data_migrations(cursor)

    conn.commit()
    conn.close()
    print("[OK] Banco de dados inicializado/atualizado com sucesso!")