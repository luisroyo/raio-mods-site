import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from database.models import get_db_connection
from contextlib import closing

def alter_schema():
    with closing(get_db_connection()) as conn:
        try:
            # 1. Add platform to products
            print("Adicionando coluna 'platform' na tabela 'products'...")
            conn.execute('ALTER TABLE products ADD COLUMN platform TEXT')
        except Exception as e:
            print(f"Aviso (platform em products): {e}")

        try:
            # 2. Add product_platform to orders
            print("Adicionando coluna 'product_platform' na tabela 'orders'...")
            conn.execute('ALTER TABLE orders ADD COLUMN product_platform TEXT')
        except Exception as e:
            print(f"Aviso (product_platform em orders): {e}")

        try:
            # 3. Add platform_confirmed to orders
            print("Adicionando coluna 'platform_confirmed' na tabela 'orders'...")
            # SQLite does not support BOOLEAN directly, so we use INTEGER (0 or 1). 
            # In Postgres BOOLEAN works, but since we support both, INTEGER or BOOLEAN is fine.
            # Using BOOLEAN for Postgres compatibility or just TEXT/INTEGER.
            # We'll use BOOLEAN DEFAULT FALSE
            conn.execute('ALTER TABLE orders ADD COLUMN platform_confirmed BOOLEAN DEFAULT FALSE')
        except Exception as e:
            print(f"Aviso (platform_confirmed em orders): {e}")

        conn.commit()
        print("Alterações concluídas com sucesso!")

if __name__ == '__main__':
    alter_schema()
