"""
Sales - Vendas manuais e relatório de vendas
"""
from flask import request, jsonify, session
from database.models import get_db_connection
from .helpers import get_dolar_hoje, IOF


def add_manual_sale():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    try:
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))
        unit_price = float(str(request.form.get('unit_price', 0)).replace('R$', '').replace(',', '.'))
        
        raw_cost = request.form.get('cost_per_unit_brl', '')
        if raw_cost is None or str(raw_cost).strip() == '':
            cost_per_unit_brl = 0.0
        else:
            cost_per_unit_brl = float(str(raw_cost).replace('R$', '').replace(',', '.'))
        notes = request.form.get('notes', '').strip()
        
        if not product_id or quantity <= 0 or unit_price <= 0:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        total_price = quantity * unit_price

        # Se custo não foi fornecido, calcular a partir do produto
        if not cost_per_unit_brl or cost_per_unit_brl <= 0:
            try:
                conn = get_db_connection()
                prod = conn.execute('SELECT cost_usd, apply_iof FROM products WHERE id = ?', (product_id,)).fetchone()
                conn.close()
                dolar_rate = get_dolar_hoje()
                if prod:
                    cost_usd = float(prod['cost_usd'] or 0)
                    apply_iof = int(prod['apply_iof']) if 'apply_iof' in prod.keys() and prod['apply_iof'] is not None else 1
                    if cost_usd > 0:
                        if apply_iof == 1:
                            cost_per_unit_brl = round(cost_usd * dolar_rate * IOF, 2)
                        else:
                            cost_per_unit_brl = round(cost_usd * dolar_rate, 2)
            except Exception as e:
                print(f"Erro ao calcular custo automático: {e}")
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO manual_sales (product_id, quantity, unit_price, cost_per_unit_brl, total_price, notes) VALUES (?,?,?,?,?,?)',
            (product_id, quantity, unit_price, cost_per_unit_brl, total_price, notes)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Venda manual registrada!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def list_manual_sales():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    sales = conn.execute('''
        SELECT ms.*, p.name as product_name
        FROM manual_sales ms
        JOIN products p ON ms.product_id = p.id
        ORDER BY ms.created_at DESC
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(s) for s in sales])


def edit_manual_sale(sale_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    try:
        conn = get_db_connection()
        existing = conn.execute('SELECT * FROM manual_sales WHERE id = ?', (sale_id,)).fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': 'Venda não encontrada'}), 404
            
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))
        unit_price = float(str(request.form.get('unit_price', 0)).replace('R$', '').replace(',', '.'))
        cost_per_unit_brl = float(str(request.form.get('cost_per_unit_brl', 0)).replace('R$', '').replace(',', '.'))
        notes = request.form.get('notes', '').strip()
        
        if not product_id or quantity <= 0 or unit_price <= 0:
            conn.close()
            return jsonify({'error': 'Dados inválidos'}), 400
        
        total_price = quantity * unit_price
        
        conn.execute('''
            UPDATE manual_sales 
            SET product_id=?, quantity=?, unit_price=?, cost_per_unit_brl=?, total_price=?, notes=?
            WHERE id=?
        ''', (product_id, quantity, unit_price, cost_per_unit_brl, total_price, notes, sale_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Venda atualizada com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def delete_manual_sale(sale_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    conn.execute('DELETE FROM manual_sales WHERE id = ?', (sale_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})


def sales_report():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    dolar_hoje = get_dolar_hoje()
    
    conn = get_db_connection()
    
    # Vendas Online
    approved_orders = conn.execute('''
        SELECT SUM(CAST(REPLACE(REPLACE(amount, 'R$', ''), ',', '.') AS REAL)) as total,
               COUNT(*) as count
        FROM orders WHERE status = 'approved'
    ''').fetchone()
    
    online_revenue = float(approved_orders['total'] or 0) if approved_orders['total'] else 0
    online_count = approved_orders['count'] or 0
    
    # Vendas Manuais
    manual_sales = conn.execute('''
        SELECT SUM(total_price) as total, COUNT(*) as count
        FROM manual_sales
    ''').fetchone()
    
    manual_revenue = float(manual_sales['total'] or 0) if manual_sales['total'] else 0
    manual_count = manual_sales['count'] or 0
    
    # Custo de vendas online
    online_costs = conn.execute('''
        SELECT 
            SUM(CASE WHEN p.apply_iof = 1 THEN p.cost_usd ELSE 0 END) as total_usd_iof,
            SUM(CASE WHEN p.apply_iof = 0 THEN p.cost_usd ELSE 0 END) as total_usd_noiof
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.status = 'approved'
    ''').fetchone()

    total_usd_iof = float(online_costs['total_usd_iof'] or 0) if online_costs['total_usd_iof'] else 0
    total_usd_noiof = float(online_costs['total_usd_noiof'] or 0) if online_costs['total_usd_noiof'] else 0

    online_cost_brl = (total_usd_iof * dolar_hoje * IOF) + (total_usd_noiof * dolar_hoje)
    
    # Custo de vendas manuais
    manual_costs = conn.execute('''
        SELECT SUM(cost_per_unit_brl * quantity) as total
        FROM manual_sales
    ''').fetchone()
    
    manual_cost_brl = float(manual_costs['total'] or 0) if manual_costs['total'] else 0
    
    # Custo de recargas de painel
    recharges = conn.execute('''
        SELECT SUM(total_cost_usd) as total_usd,
               SUM(total_cost_usd * dolar_rate) as total_brl
        FROM panel_recharges
    ''').fetchone()
    
    total_recharged_usd = float(recharges['total_usd'] or 0) if recharges['total_usd'] else 0
    total_recharged_brl = float(recharges['total_brl'] or 0) if recharges['total_brl'] else 0
    
    conn.close()
    
    # Totais
    total_revenue = online_revenue + manual_revenue
    
    # CORREÇÃO: Usar apenas o custo de recargas (Regime de Caixa) para evitar contagem dupla
    # O usuário considera o 'Custo' como o investimento feito na compra dos painéis (Recargas)
    # Se somarmos o custo por venda, estaremos duplicando o valor já contabilizado na recarga.
    # total_costs = online_cost_brl + manual_cost_brl + total_recharged_brl
    total_costs = total_recharged_brl
    
    total_profit = total_revenue - total_costs
    
    return jsonify({
        'online': {
            'revenue': round(online_revenue, 2),
            'count': online_count,
            'cost_brl': round(online_cost_brl, 2),
            'cost_usd_with_iof': round(total_usd_iof, 2),
            'cost_usd_no_iof': round(total_usd_noiof, 2)
        },
        'manual': {
            'revenue': round(manual_revenue, 2),
            'count': manual_count,
            'cost_brl': round(manual_cost_brl, 2)
        },
        'panel': {
            'total_cost_usd': round(total_recharged_usd, 2),
            'total_cost_brl': round(total_recharged_brl, 2)
        },
        'summary': {
            'dolar_rate': round(dolar_hoje, 2),
            'total_revenue': round(total_revenue, 2),
            'total_costs': round(total_costs, 2),
            'total_profit': round(total_profit, 2),
            'profit_margin': round((total_profit / total_revenue * 100) if total_revenue > 0 else 0, 2)
        }
    })
