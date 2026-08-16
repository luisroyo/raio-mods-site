import os
from contextlib import closing
import logging

# Configuração de log
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger('cleanup')

def run_cleanup():
    from database.db_wrappers import get_db_connection
    
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        
        logger.info("Iniciando varredura de comissões duplicadas...")
        
        # Encontra pedidos que têm mais de 1 comissão (o que indica que a race condition ocorreu)
        cursor.execute('''
            SELECT order_id, COUNT(*) as qtd
            FROM commissions
            GROUP BY order_id
            HAVING COUNT(*) > 1
        ''')
        
        duplicates = cursor.fetchall()
        if not duplicates:
            logger.info("Nenhuma comissão duplicada encontrada no banco de dados atual.")
            return

        for row in duplicates:
            order_id = row['order_id']
            qtd = row['qtd']
            logger.info(f"--- Encontrado Pedido ID {order_id} com {qtd} comissões geradas ---")
            
            # Buscar detalhes do pedido
            order = cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not order:
                logger.warning(f"Pedido {order_id} não encontrado na tabela orders. Pulando.")
                continue
                
            email = order['customer_email'].strip().lower()
            product_id = order['product_id']
            
            # 1. Corrigir Comissões (Manter apenas a primeira, apagar as outras)
            comms = cursor.execute("SELECT id, commission_amount FROM commissions WHERE order_id = ? ORDER BY id ASC", (order_id,)).fetchall()
            first_comm_id = comms[0]['id']
            
            # Deletar as outras
            for comm in comms[1:]:
                cursor.execute("DELETE FROM commissions WHERE id = ?", (comm['id'],))
                logger.info(f"  [Comissão] Deletada comissão extra ID: {comm['id']} (R$ {comm['commission_amount']})")
                
            # 2. Corrigir Pontos de Fidelidade
            amount_val = order['amount']
            points_to_add = int(amount_val)
            
            if points_to_add > 0:
                # Quantas vezes os pontos foram dados para esse pedido?
                points_given = cursor.execute(
                    "SELECT id, points_changed FROM points_history WHERE email = ? AND description LIKE ?", 
                    (email, f'%#{order_id} - %')
                ).fetchall()
                
                # Se foi dado mais de uma vez
                if len(points_given) > 1:
                    # Deletar o histórico extra
                    for p_hist in points_given[1:]:
                        cursor.execute("DELETE FROM points_history WHERE id = ?", (p_hist['id'],))
                        logger.info(f"  [Pontos] Deletado histórico de pontos extra ID: {p_hist['id']}")
                    
                    # Subtrair do saldo total do cliente
                    pontos_excedentes = (len(points_given) - 1) * points_to_add
                    
                    cursor.execute("UPDATE client_points SET points = points - ? WHERE email = ?", (pontos_excedentes, email))
                    # Garantir que não fique negativo (por segurança)
                    cursor.execute("UPDATE client_points SET points = 0 WHERE email = ? AND points < 0", (email,))
                    logger.info(f"  [Pontos] Removidos {pontos_excedentes} pontos extras do saldo do cliente {email}.")

            # 3. Corrigir Uso de Cupons
            if order['coupon_id']:
                c_id = order['coupon_id']
                # Se gerou N comissões, provavelmente usou o cupom N vezes (N-1 vezes a mais)
                usos_extras = qtd - 1
                cursor.execute("UPDATE coupons SET current_uses = current_uses - ? WHERE id = ?", (usos_extras, c_id))
                # Segurança
                cursor.execute("UPDATE coupons SET current_uses = 0 WHERE id = ? AND current_uses < 0", (c_id,))
                logger.info(f"  [Cupom] Uso do cupom ID {c_id} reduzido em {usos_extras}.")
                
                if order['coupon_code'] and str(order['coupon_code']).upper().startswith('FID-'):
                    logger.info("  [Cupom] Atenção: Cupom fidelidade foi marcado como usado. Como é de uso único, manter marcado está correto.")
                    
        conn.commit()
        logger.info("\n=== LIMPEZA E CORREÇÃO CONCLUÍDAS COM SUCESSO ===")

if __name__ == '__main__':
    # Simula o ambiente da aplicação Flask
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        run_cleanup()
    except Exception as e:
        logger.error(f"Erro ao executar limpeza: {e}")
