import sqlite3
import os

from database.schema import create_tables
from database.migrations_schema import run_schema_migrations
from database.migrations_data import run_data_migrations
from database.models import get_db_connection

def get_db_path():
    basedir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(basedir, '../database.db')

def init_db():
    db_path = get_db_path()
    print(f"[BD] Verificando banco de dados em: {db_path}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Criação do Schema Base
    create_tables(cursor)

    # 2. Migrações Estruturais (Schema)
    run_schema_migrations(cursor)

    # 3. Migrações de Dados (Data)
    run_data_migrations(cursor)

    conn.commit()
    conn.close()
    print("[OK] Banco de dados inicializado/atualizado com sucesso!")