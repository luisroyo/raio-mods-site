import sqlite3
import os

# Caminho do banco de dados (ajuste se necessário)
DB_PATH = 'database.db'

def get_connection():
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco de dados não encontrado em: {os.path.abspath(DB_PATH)}")
        return None
    return sqlite3.connect(DB_PATH)

def list_products():
    conn = get_connection()
    if not conn: return

    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, cost_usd, apply_iof FROM products ORDER BY id")
    products = cursor.fetchall()
    
    print("\n📋 --- PRODUTOS ATUAIS (Copie o dicionário abaixo para editar) ---\n")
    print("products_data = [")
    for p in products:
        p_id, name, price, cost, iof = p
        # Formata para facilitar a cópia
        print(f"    {{'id': {p_id}, 'name': {repr(name)}, 'price': {repr(price)}, 'cost_usd': {cost}, 'apply_iof': {iof}}},")
    print("]")
    print("\n--------------------------------------------------------------")
    conn.close()

def update_products(data):
    conn = get_connection()
    if not conn: return
    
    cursor = conn.cursor()
    print(f"\n🔄 Atualizando {len(data)} produtos...")
    
    for item in data:
        try:
            cursor.execute("""
                UPDATE products 
                SET name = ?, price = ?, cost_usd = ?, apply_iof = ?
                WHERE id = ?
            """, (item['name'], item['price'], item['cost_usd'], item['apply_iof'], item['id']))
            print(f"✅ Produto {item['id']} atualizado.")
        except Exception as e:
            print(f"❌ Erro ao atualizar ID {item['id']}: {e}")
            
    conn.commit()
    conn.close()
    print("\n✨ Atualização concluída!")

# --- COMO USAR ---
# 1. Execute este script primeiro para ver a lista: python mass_update_products.py
# 2. Copie a lista 'products_data' gerada no terminal.
# 3. Cole abaixo em 'NOVOS_DADOS', altere os valores que quiser.
# 4. Descomente a linha 'update_products(NOVOS_DADOS)' no final do arquivo.
# 5. Execute novamente.

if __name__ == "__main__":
    # Passo 1: Listar (Sempre executa para mostrar IDs)
    list_products()

    # Passo 2: Colar dados modificados aqui
    NOVOS_DADOS = [
        # Exemplo:
        # {'id': 1, 'name': 'Produto Exemplo', 'price': 'R$ 20,00', 'cost_usd': 5.0, 'apply_iof': 1},
    ]

    # Passo 3: Descomentar para aplicar
    if NOVOS_DADOS:
         update_products(NOVOS_DADOS)
    else:
         print("\n⚠️  Nenhuma alteração definida em 'NOVOS_DADOS'. Edite o script para aplicar mudanças.")
