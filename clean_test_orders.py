import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from database.models import get_db_connection
from contextlib import closing

def clean_tests(email):
    print(f"Buscando testes com o email: {email}")

    with closing(get_db_connection()) as conn:
        orders = conn.execute("SELECT id, key_assigned_id, external_reference FROM orders WHERE customer_email = ?", (email,)).fetchall()
        if not orders:
            print("Nenhum pedido de teste encontrado!")
        else:
            for order in orders:
                order_id = order['id']
                key_id = order['key_assigned_id']
                ext_ref = order['external_reference']
                print(f"Limpando pedido {ext_ref}...")
                
                # As chaves eram fakes, então vamos deletá-las do banco também
                if key_id:
                    conn.execute("DELETE FROM product_keys WHERE id = ?", (key_id,))
                    print(f" -> Chave fake (ID: {key_id}) deletada definitivamente do estoque.")
                    
                # Deleta o pedido
                conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
                
            conn.commit()
            print(f"Sucesso! {len(orders)} pedido(s) e suas chaves fakes foram removidos do sistema.")

if __name__ == '__main__':
    clean_tests('luisroyo25@gmail.com')
