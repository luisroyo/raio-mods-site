import sqlite3
conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row

# Verifica o schema da tabela products
cols = conn.execute("PRAGMA table_info(products)").fetchall()
print("Colunas de 'products':")
for c in cols:
    print(f"  {c['cid']}: {c['name']} ({c['type']})")

has_dl = any(c['name'] == 'download_link' for c in cols)
print(f"\nColuna download_link existe: {has_dl}")
conn.close()
