import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from database.models import get_db_connection
from contextlib import closing

def clean_orders():
    print("Iniciando limpeza de pedidos...")

    with closing(get_db_connection()) as conn:
        # Busca pedidos pelo e-mail do admin E pelo código específico do cliente que comprou errado
        orders = conn.execute('''
            SELECT id, key_assigned_id, external_reference, customer_email 
            FROM orders 
            WHERE customer_email = 'luisroyo25@gmail.com' 
               OR external_reference = 'ORD-533d0f657831'
        ''').fetchall()
        
        if not orders:
            print("Nenhum pedido encontrado para limpeza!")
        else:
            for order in orders:
                order_id = order['id']
                key_id = order['key_assigned_id']
                ext_ref = order['external_reference']
                email = order['customer_email']
                
                print(f"Limpando pedido {ext_ref} ({email})...")
                
                if key_id:
                    if email == 'luisroyo25@gmail.com':
                        # Se for teste do admin, deleta a chave falsa
                        conn.execute("DELETE FROM product_keys WHERE id = ?", (key_id,))
                        print(f" -> Chave fake (ID: {key_id}) deletada definitivamente do estoque.")
                    else:
                        # Se for de cliente (ORD-25003956dfe7) e a chave ainda estiver vinculada,
                        # apenas devolve ao estoque
                        conn.execute("UPDATE product_keys SET is_used = 0 WHERE id = ?", (key_id,))
                        print(f" -> Chave (ID: {key_id}) desvinculada e devolvida ao estoque.")
                    
                # Deleta o pedido em si
                conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
                print(f" -> Pedido {ext_ref} deletado do banco de dados.")
                
            conn.commit()
            print(f"\nSucesso! {len(orders)} pedido(s) foram removidos do sistema.")

if __name__ == '__main__':
    clean_orders()
