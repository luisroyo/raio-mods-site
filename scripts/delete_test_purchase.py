import sys
import os

# Adiciona o diretório raiz ao path do python para poder importar os módulos do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.models import get_db_connection

def delete_test_purchase():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE customer_email = 'luisroyo25@gmail.com'")
        conn.commit()
        print("Compras de teste com o email luisroyo25@gmail.com deletadas com sucesso!")
    except Exception as e:
        print(f"Erro ao deletar: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    delete_test_purchase()
