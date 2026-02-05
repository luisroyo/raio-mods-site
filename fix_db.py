import sqlite3
import os

# Tenta achar o banco de dados
db_paths = [
    os.path.join('site', 'database.db'),
    'database.db'
]

db_path = None
for p in db_paths:
    if os.path.exists(p):
        db_path = p
        break

if not db_path:
    print("❌ Erro: Não encontrei o arquivo database.db")
    exit()

print(f"🔧 Corrigindo banco de dados em: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Adiciona coluna contact_whatsapp se não existir
try:
    cursor.execute('ALTER TABLE config ADD COLUMN contact_whatsapp TEXT DEFAULT ""')
    print("✅ Coluna contact_whatsapp criada.")
except sqlite3.OperationalError:
    print("ℹ️ Coluna contact_whatsapp já existe.")

# 2. Adiciona coluna mercado_pago_token se não existir
try:
    cursor.execute('ALTER TABLE config ADD COLUMN mercado_pago_token TEXT DEFAULT ""')
    print("✅ Coluna mercado_pago_token criada.")
except sqlite3.OperationalError:
    print("ℹ️ Coluna mercado_pago_token já existe.")

# 3. Adiciona pix_copia_cola se não existir
try:
    cursor.execute('ALTER TABLE config ADD COLUMN pix_copia_cola TEXT DEFAULT ""')
    print("✅ Coluna pix_copia_cola criada.")
except sqlite3.OperationalError:
    print("ℹ️ Coluna pix_copia_cola já existe.")

# 4. Adiciona promo_price na tabela products se não existir
try:
    cursor.execute('ALTER TABLE products ADD COLUMN promo_price TEXT DEFAULT ""')
    print("✅ Coluna promo_price criada.")
except sqlite3.OperationalError:
    print("ℹ️ Coluna promo_price já existe.")

# 5. Adiciona promo_label na tabela products se não existir
try:
    cursor.execute('ALTER TABLE products ADD COLUMN promo_label TEXT DEFAULT ""')
    print("✅ Coluna promo_label criada.")
except sqlite3.OperationalError:
    print("ℹ️ Coluna promo_label já existe.")

conn.commit()
conn.close()

print("\n🎉 Tudo pronto! Pode rodar 'python app.py' novamente.")