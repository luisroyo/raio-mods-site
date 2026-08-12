from database.db_wrappers import get_db_connection
import sys

def recalculate_retroactive_commissions():
    try:
        with get_db_connection() as conn:
            # Pegar todos os cupons de vendedor que tem comissão configurada > 0
            seller_coupons = conn.execute('SELECT code, commission_percentage FROM coupons WHERE is_seller = TRUE AND commission_percentage > 0').fetchall()
            
            if not seller_coupons:
                print("Nenhum cupom de vendedor com comissão configurada encontrado.")
                return
                
            for coupon in seller_coupons:
                code = coupon['code']
                perc = float(coupon['commission_percentage'])
                print(f"\n--- Processando Retroativo para Cupom: {code} ({perc}%) ---")
                
                # Vendas Manuais
                manual_sales = conn.execute('''
                    SELECT ms.id, ms.total_price, COALESCE(p.pays_commission, 1) as pays_commission
                    FROM manual_sales ms
                    LEFT JOIN products p ON ms.product_id = p.id
                    WHERE ms.coupon_code = ?
                ''', (code,)).fetchall()
                
                for sale in manual_sales:
                    if int(sale['pays_commission']) == 0:
                        continue
                    # Verifica se já existe comissão para não duplicar
                    exists = conn.execute('SELECT 1 FROM commissions WHERE manual_sale_id = ?', (sale['id'],)).fetchone()
                    if not exists:
                        com_amt = round(sale['total_price'] * (perc / 100.0), 2)
                        conn.execute('''
                            INSERT INTO commissions (seller_coupon, manual_sale_id, sale_amount, commission_amount, status)
                            VALUES (?, ?, ?, ?, 'pending')
                        ''', (code, sale['id'], sale['total_price'], com_amt))
                        print(f"Comissão gerada (Manual #{sale['id']}): R$ {com_amt}")
                        
                # Vendas Online
                online_sales = conn.execute('''
                    SELECT o.id, o.amount, COALESCE(p.pays_commission, 1) as pays_commission
                    FROM orders o
                    LEFT JOIN products p ON o.product_id = p.id
                    WHERE (o.seller_coupon = ? OR o.coupon_code = ?) AND o.status IN ('approved', 'paid_no_key')
                ''', (code, code)).fetchall()
                
                for order in online_sales:
                    if int(order['pays_commission']) == 0:
                        continue
                    # Verifica se já existe comissão
                    exists = conn.execute('SELECT 1 FROM commissions WHERE order_id = ?', (order['id'],)).fetchone()
                    if not exists:
                        com_amt = round(order['amount'] * (perc / 100.0), 2)
                        conn.execute('''
                            INSERT INTO commissions (seller_coupon, order_id, sale_amount, commission_amount, status)
                            VALUES (?, ?, ?, ?, 'pending')
                        ''', (code, order['id'], order['amount'], com_amt))
                        print(f"Comissão gerada (Online #{order['id']}): R$ {com_amt}")

            print("\nProcesso de comissões retroativas finalizado!")

    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)

from database.connection import init_db

if __name__ == '__main__':
    print("Inicializando banco de dados para aplicar migrações...")
    init_db()
    recalculate_retroactive_commissions()
