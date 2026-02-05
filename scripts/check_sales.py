"""
Verificar quantas vendas manuais existem no banco de produção.
"""
import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Contar total de vendas manuais
cursor.execute('SELECT COUNT(*) as total FROM manual_sales')
total = cursor.fetchone()[0]

print(f"\n📊 Total de vendas manuais: {total}")

# Mostrar as últimas 10 vendas inseridas
print("\n📋 Últimas 10 vendas manuais:")
print("-" * 80)

cursor.execute('''
    SELECT 
        id,
        product_id,
        quantity,
        unit_price,
        total_price,
        notes,
        created_at
    FROM manual_sales
    ORDER BY id DESC
    LIMIT 10
''')

for row in cursor.fetchall():
    sale_id, product_id, qty, unit_price, total, notes, created_at = row
    print(f"ID {sale_id}: Produto {product_id} | Qtd: {qty} | R$ {unit_price:.2f} | Total: R$ {total:.2f}")
    if notes:
        print(f"         Notas: {notes}")
    if created_at:
        print(f"         Data: {created_at}")

# Estatísticas por produto
print("\n\n💰 Vendas por Produto:")
print("-" * 80)

cursor.execute('''
    SELECT 
        p.id,
        p.name,
        COUNT(m.id) as quantidade_vendas,
        SUM(m.total_price) as total_vendido
    FROM manual_sales m
    JOIN products p ON m.product_id = p.id
    GROUP BY p.id, p.name
    ORDER BY quantidade_vendas DESC
''')

for row in cursor.fetchall():
    prod_id, prod_name, qty_sales, total_sold = row
    print(f"Produto {prod_id}: {prod_name}")
    print(f"  → {qty_sales} vendas | Total: R$ {total_sold:.2f}\n")

conn.close()
