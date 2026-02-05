import sqlite3
import os

# Caminho do banco
db_path = os.path.join('site', 'database.db')
if not os.path.exists(db_path):
    db_path = 'database.db'

print(f"🔧 Atualizando tabelas em: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Cria tabela de CHAVES (se não existir)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        key_value TEXT NOT NULL,
        is_used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
''')
print("✅ Tabela 'product_keys' verificada.")

# 2. Cria tabela de PEDIDOS (se não existir)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_reference TEXT UNIQUE,
        product_id INTEGER NOT NULL,
        customer_email TEXT NOT NULL,
        amount REAL,
        status TEXT DEFAULT 'pending',
        qr_code TEXT,
        qr_code_base64 TEXT,
        key_assigned_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (key_assigned_id) REFERENCES product_keys (id)
    )
''')
print("✅ Tabela 'orders' verificada.")

# 2.5. Cria tabela de VENDAS MANUAIS (offline)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS manual_sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        unit_price REAL NOT NULL,
        cost_per_unit_brl REAL NOT NULL,
        total_price REAL NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
''')
print("✅ Tabela 'manual_sales' criada/verificada.")

# 2.6. Cria tabela de RECARGAS DE PAINEL
cursor.execute('''
    CREATE TABLE IF NOT EXISTS panel_recharges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quantity INTEGER NOT NULL,
        cost_per_unit_usd REAL NOT NULL,
        total_cost_usd REAL NOT NULL,
        dolar_rate REAL NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
print("✅ Tabela 'panel_recharges' criada/verificada.")

# 3. Garante colunas na tabela PRODUCTS
try:
    cursor.execute('ALTER TABLE products ADD COLUMN cost_usd REAL DEFAULT 0.0')
    print("✅ Coluna 'cost_usd' adicionada à tabela 'products'.")
except Exception as e:
    if 'duplicate column' in str(e).lower():
        print("✅ Coluna 'cost_usd' já existe na tabela 'products'.")
    else:
        print(f"⚠️ Aviso ao adicionar 'cost_usd': {e}")

# 3.5 Garante flag apply_iof na tabela PRODUCTS (1 = aplicar IOF, 0 = não aplicar)
try:
    cursor.execute('ALTER TABLE products ADD COLUMN apply_iof INTEGER DEFAULT 1')
    print("✅ Coluna 'apply_iof' adicionada à tabela 'products'.")
except Exception as e:
    if 'duplicate column' in str(e).lower():
        print("✅ Coluna 'apply_iof' já existe na tabela 'products'.")
    else:
        print(f"⚠️ Aviso ao adicionar 'apply_iof': {e}")

# 4. Garante colunas na tabela CONFIG
try:
    cursor.execute('ALTER TABLE config ADD COLUMN mercado_pago_token TEXT DEFAULT ""')
except: pass
try:
    cursor.execute('ALTER TABLE config ADD COLUMN pix_key TEXT DEFAULT ""')
except: pass
try:
    cursor.execute('ALTER TABLE config ADD COLUMN contact_whatsapp TEXT DEFAULT ""')
except: pass

print("✅ Colunas de configuração verificadas.")

conn.commit()
conn.close()
print("\n🎉 Banco de dados 100% pronto para vendas!")