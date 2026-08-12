import sys
import os

# Adiciona o diretório atual ao sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.db import get_db_connection
from routes.payment import process_approved_payment

def approve_all_pending():
    print("Iniciando verificação de pedidos pendentes...")
    conn = get_db_connection()
    
    # Busca todos os pedidos pendentes
    pendings = conn.execute("SELECT id, external_reference, product_id, customer_email, created_at FROM orders WHERE status = 'pending' ORDER BY id ASC").fetchall()
    
    if not pendings:
        print("✅ Nenhum pedido pendente encontrado no banco de dados.")
        conn.close()
        return

    print(f"Encontrados {len(pendings)} pedidos pendentes.")
    
    for order in pendings:
        print(f"\n-> Processando Pedido ID: {order['id']}")
        print(f"   Cliente: {order['customer_email']} | Referência: {order['external_reference']}")
        print(f"   Data: {order['created_at']}")
        
        try:
            process_approved_payment(order['external_reference'], order['product_id'])
            print(f"   ✅ Pedido {order['id']} processado com sucesso!")
        except Exception as e:
            print(f"   ❌ Erro ao processar pedido {order['id']}: {e}")
            
    conn.close()
    print("\nFinalizado!")

if __name__ == '__main__':
    approve_all_pending()
