import sys
import os
import sqlite3

# Adiciona o diretório atual ao sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.models import get_db_connection

def fix_dates():
    print("Iniciando correção das datas das comissões retroativas...")
    conn = get_db_connection()
    
    try:
        # Corrige as datas das comissões baseadas em Vendas Online (orders)
        # Copia o created_at da tabela orders para a tabela commissions
        cursor = conn.execute('''
            UPDATE commissions
            SET created_at = (
                SELECT created_at 
                FROM orders 
                WHERE orders.id = commissions.order_id
            )
            WHERE order_id IS NOT NULL;
        ''')
        print(f"✅ {cursor.rowcount} comissões de vendas online tiveram suas datas corrigidas.")
        
        # Corrige as datas das comissões baseadas em Vendas Manuais (se houver alguma)
        # A tabela manual_sales usa 'date_sold', então copiamos de lá
        cursor = conn.execute('''
            UPDATE commissions
            SET created_at = (
                SELECT date_sold 
                FROM manual_sales 
                WHERE manual_sales.id = commissions.manual_sale_id
            )
            WHERE manual_sale_id IS NOT NULL;
        ''')
        print(f"✅ {cursor.rowcount} comissões de vendas manuais tiveram suas datas corrigidas.")
        
        conn.commit()
        print("\nPronto! Todas as datas foram corrigidas com sucesso no banco de dados.")
        
    except Exception as e:
        print(f"❌ Erro ao corrigir as datas: {e}")
        
    finally:
        conn.close()

if __name__ == '__main__':
    fix_dates()
