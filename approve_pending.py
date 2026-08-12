import sys
import os

# Adiciona o diretório atual ao sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.db import get_db_connection
from routes.payment import process_approved_payment

def approve_specific_pending():
    order_ref = sys.argv[1] if len(sys.argv) > 1 else 'ORD-4f4394daa27d'
    
    print(f"Buscando o pedido pendente com referência: {order_ref}...")
    conn = get_db_connection()
    
    # Busca apenas o pedido específico
    order = conn.execute("SELECT id, external_reference, product_id, customer_email, created_at, status FROM orders WHERE external_reference = ?", (order_ref,)).fetchone()
    
    if not order:
        print(f"❌ Pedido {order_ref} não encontrado no banco de dados.")
        conn.close()
        return
        
    if order['status'] != 'pending':
        print(f"⚠️ Atenção: O pedido {order_ref} já está com status '{order['status']}'.")
        # Mas vamos forçar a re-execução se necessário? Depende, deixei a validação original dentro do process_approved_payment tratar.

    print(f"\n-> Processando Pedido ID: {order['id']}")
    print(f"   Cliente: {order['customer_email']}")
    print(f"   Data: {order['created_at']}")
    
    try:
        process_approved_payment(order['external_reference'], order['product_id'])
        print(f"   ✅ Pedido {order['id']} processado e aprovado com sucesso!")
    except Exception as e:
        print(f"   ❌ Erro ao processar pedido {order['id']}: {e}")
            
    conn.close()
    print("\nFinalizado!")

if __name__ == '__main__':
    approve_specific_pending()
