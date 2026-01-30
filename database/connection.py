import sqlite3
import os

def get_db_path():
    basedir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(basedir, '../database.db')

def init_db():
    db_path = get_db_path()
    print(f"🔌 Verificando banco de dados em: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabelas Base
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price TEXT NOT NULL,
            image TEXT NOT NULL,
            category TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            image TEXT,
            download_link TEXT,
            video_link TEXT,
            game TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Migração: coluna image em links
    try:
        cursor.execute('SELECT image FROM links LIMIT 1')
    except sqlite3.OperationalError:
        try:
            cursor.execute('ALTER TABLE links ADD COLUMN image TEXT')
        except: pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pix_key TEXT DEFAULT '',
            binance_wallet TEXT DEFAULT '',
            whatsapp_number TEXT DEFAULT '5519989888909'
        )
    ''')

    # Seed Config
    cursor.execute('SELECT count(*) FROM config')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO config (id, pix_key, binance_wallet) VALUES (1, "", "")')

    # Migrações (Adicionar colunas novas se não existirem)
    new_columns = [
        ('tagline', 'TEXT DEFAULT ""'),
        ('sort_order', 'INTEGER DEFAULT 0'),
        ('parent_id', 'INTEGER NULL'),
        ('is_catalog', 'INTEGER DEFAULT 0'),
        ('payment_url', 'TEXT DEFAULT ""')
    ]

    for col_name, col_type in new_columns:
        try:
            cursor.execute(f'SELECT {col_name} FROM products LIMIT 1')
        except sqlite3.OperationalError:
            try:
                cursor.execute(f'ALTER TABLE products ADD COLUMN {col_name} {col_type}')
            except: pass
    
    conn.commit()
    conn.close()