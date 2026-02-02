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

# 3. Garante colunas na tabela CONFIG
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