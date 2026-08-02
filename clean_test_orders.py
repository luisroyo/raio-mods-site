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
                
                # Devolve a chave ao estoque
                if key_id:
                    conn.execute("UPDATE product_keys SET is_used = 0 WHERE id = ?", (key_id,))
                    print(f" -> Chave {key_id} restaurada no estoque.")
                    
                # Deleta o pedido
                conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
                
            conn.commit()
            print(f"Sucesso! {len(orders)} pedido(s) removido(s) e chaves devolvidas.")

if __name__ == '__main__':
    clean_tests('luisroyo25@gmail.com')
