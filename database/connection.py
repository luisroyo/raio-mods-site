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
    
    # --- TABELAS BASE DO SISTEMA ---
    
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pix_key TEXT DEFAULT '',
            binance_wallet TEXT DEFAULT '',
            whatsapp_number TEXT DEFAULT '5519989888909'
        )
    ''')

    # --- NOVAS TABELAS PARA AUTOMAÇÃO (MERCADO PAGO) ---
    
    # 1. Tabela de Chaves (O Estoque de produtos digitais)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            key_value TEXT NOT NULL,
            is_used INTEGER DEFAULT 0, -- 0 = Disponível, 1 = Vendida
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    # 2. Tabela de Pedidos (Histórico de vendas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_reference TEXT UNIQUE, -- ID do Pedido no Mercado Pago
            product_id INTEGER NOT NULL,
            customer_email TEXT NOT NULL,
            amount REAL,
            status TEXT DEFAULT 'pending', -- pending, approved, refunded
            key_assigned_id INTEGER, -- Qual chave foi entregue
            qr_code TEXT,
            qr_code_base64 TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (key_assigned_id) REFERENCES product_keys (id)
        )
    ''')
    
    # --- MIGRAÇÕES E ATUALIZAÇÕES ---

    # Seed Config (Insere configuração padrão se vazio)
    cursor.execute('SELECT count(*) FROM config')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO config (id, pix_key, binance_wallet) VALUES (1, "", "")')

    # Lista de colunas para verificar/adicionar em PRODUCTS
    new_columns_products = [
        ('tagline', 'TEXT DEFAULT ""'),
        ('sort_order', 'INTEGER DEFAULT 0'),
        ('parent_id', 'INTEGER NULL'),
        ('is_catalog', 'INTEGER DEFAULT 0'),
        ('payment_url', 'TEXT DEFAULT ""')
    ]

    for col_name, col_type in new_columns_products:
        try:
            cursor.execute(f'SELECT {col_name} FROM products LIMIT 1')
        except sqlite3.OperationalError:
            try:
                print(f"--> Adicionando coluna {col_name} em products...")
                cursor.execute(f'ALTER TABLE products ADD COLUMN {col_name} {col_type}')
            except: pass

    # Migração config: PIX Copia e Cola
    try:
        cursor.execute('SELECT pix_copia_cola FROM config LIMIT 1')
    except sqlite3.OperationalError:
        try:
            cursor.execute('ALTER TABLE config ADD COLUMN pix_copia_cola TEXT DEFAULT ""')
        except: pass

    # Migração config: Token do Mercado Pago (NOVO)
    try:
        cursor.execute('SELECT mercado_pago_token FROM config LIMIT 1')
    except sqlite3.OperationalError:
        try:
            print("--> Adicionando suporte a Mercado Pago na config...")
            cursor.execute('ALTER TABLE config ADD COLUMN mercado_pago_token TEXT DEFAULT ""')
        except: pass

    # Migração config: WhatsApp Suporte
    try:
        cursor.execute('SELECT contact_whatsapp FROM config LIMIT 1')
    except sqlite3.OperationalError:
        try:
            cursor.execute('ALTER TABLE config ADD COLUMN contact_whatsapp TEXT DEFAULT ""')
        except: pass

    # Migração links: Imagem
    try:
        cursor.execute('SELECT image FROM links LIMIT 1')
    except sqlite3.OperationalError:
        try:
            cursor.execute('ALTER TABLE links ADD COLUMN image TEXT')
        except: pass

    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado/atualizado com sucesso!")