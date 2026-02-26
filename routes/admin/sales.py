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
    
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        # Filters
        category = request.args.get('category', '')
        date_start = request.args.get('date_start', '')
        date_end = request.args.get('date_end', '')
        
        dolar_hoje = get_dolar_hoje()
        
        # Base Query Structure
        # We use a CTE or subquery to combine them then filter/paginate
        
        query_manual = '''
            SELECT 
                'manual' as type,
                ms.id, 
                p.name as product_name, 
                p.category,
                ms.quantity, 
                ms.unit_price, 
                ms.cost_per_unit_brl, 
                ms.total_price, 
                (ms.total_price - (ms.quantity * ms.cost_per_unit_brl)) as profit,
                ms.notes as client_info,
                ms.created_at
            FROM manual_sales ms
            JOIN products p ON ms.product_id = p.id
        '''
        
        # Para online, calculamos o custo estimado com base no dólar de HOJE (como no relatório)
        # Se quiser histórico exato, precisaríamos salvar o custo histórico no pedido.
        # Assumindo cálculo dinâmico conforme regra do relatório.
        
        query_online = f'''
            SELECT 
                'online' as type,
                o.id, 
                p.name as product_name,
                p.category,
                1 as quantity,
                o.amount as unit_price,
                (p.cost_usd * {dolar_hoje} * (CASE WHEN p.apply_iof = 1 THEN {IOF} ELSE 1 END)) as cost_per_unit_brl,
                o.amount as total_price,
                (o.amount - (p.cost_usd * {dolar_hoje} * (CASE WHEN p.apply_iof = 1 THEN {IOF} ELSE 1 END))) as profit,
                o.customer_email as client_info,
                o.created_at
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.status IN ('approved', 'paid_no_key')
        '''

        combined_query = f'''
            SELECT * FROM (
                {query_manual}
                UNION ALL
                {query_online}
            ) as all_sales
            WHERE 1=1
        '''
        
        params = []
        
        if category:
            combined_query += ' AND category = ?'
            params.append(category)
            
        if date_start:
            combined_query += ' AND date(created_at) >= ?'
            params.append(date_start)
            
        if date_end:
            combined_query += ' AND date(created_at) <= ?'
            params.append(date_end)
            
        # Count total
        count_query = f'SELECT COUNT(*) FROM ({combined_query}) as counted' # nested to be safe
        # SQLite doesn't like same param list twice usually if passed directly, 
        # but here we build the string.
        # Actually proper way:
        # We need to execute the count with params, then the data select with params.
        
        conn = get_db_connection()
        total_items = conn.execute(count_query, params).fetchone()[0]
        
        # Paginate
        combined_query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        sales = conn.execute(combined_query, params).fetchall()
        conn.close()
        
        return jsonify({
            'data': [dict(s) for s in sales],
            'total': total_items,
            'page': page,
            'limit': limit,
            'pages': (total_items + limit - 1) // limit if limit > 0 else 0
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


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
    
    # --- Agregação por Produto ---
    product_stats = {}

    conn = get_db_connection()
    
    # 1. Agrega Vendas Online
    online_by_product = conn.execute('''
        SELECT p.name, COUNT(*) as qtd, 
               SUM(CAST(REPLACE(REPLACE(amount, 'R$', ''), ',', '.') AS REAL)) as total
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.status = 'approved'
        GROUP BY p.name
    ''').fetchall()
    
    for row in online_by_product:
        name = row['name']
        if name not in product_stats:
            product_stats[name] = {'qtd': 0, 'total': 0.0}
        product_stats[name]['qtd'] += row['qtd']
        product_stats[name]['total'] += row['total'] or 0

    # 2. Agrega Vendas Manuais
    manual_by_product = conn.execute('''
        SELECT p.name, SUM(ms.quantity) as qtd, SUM(ms.total_price) as total
        FROM manual_sales ms
        JOIN products p ON ms.product_id = p.id
        GROUP BY p.name
    ''').fetchall()
    
    for row in manual_by_product:
        name = row['name']
        if name not in product_stats:
            product_stats[name] = {'qtd': 0, 'total': 0.0}
        product_stats[name]['qtd'] += row['qtd']
        product_stats[name]['total'] += row['total'] or 0

    conn.close()

    # Converter para lista e ordenar por Faturamento (total)
    sorted_products = []
    for name, data in product_stats.items():
        sorted_products.append({
            'name': name,
            'quantity': data['qtd'],
            'total': round(data['total'], 2)
        })
    
    sorted_products.sort(key=lambda x: x['total'], reverse=True)

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
        'by_product': sorted_products,
        'summary': {
            'dolar_rate': round(dolar_hoje, 2),
            'total_revenue': round(total_revenue, 2),
            'total_costs': round(total_costs, 2),
            'total_profit': round(total_profit, 2),
            'profit_margin': round((total_profit / total_revenue * 100) if total_revenue > 0 else 0, 2)
        }
    })


def get_order_proof(order_id):
    """Retorna dossiê anti-fraude com todas as provas de uma venda online."""
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401

    conn = get_db_connection()
    order = conn.execute('''
        SELECT o.*, p.name as product_name, k.key_value
        FROM orders o
        JOIN products p ON o.product_id = p.id
        LEFT JOIN product_keys k ON o.key_assigned_id = k.id
        WHERE o.id = ?
    ''', (order_id,)).fetchone()
    conn.close()

    if not order:
        return jsonify({'error': 'Pedido não encontrado'}), 404

    d = dict(order)
    return jsonify({
        'success': True,
        'proof': {
            'order_id': d.get('id'),
            'external_reference': d.get('external_reference', ''),
            'product_name': d.get('product_name', ''),
            'amount': d.get('amount', 0),
            'status': d.get('status', ''),
            'customer_name': d.get('customer_name', ''),
            'customer_cpf': d.get('customer_cpf', ''),
            'customer_email': d.get('customer_email', ''),
            'customer_phone': d.get('customer_phone', ''),
            'ip_purchase': d.get('ip_purchase', ''),
            'ip_delivery': d.get('ip_delivery', ''),
            'terms_accepted_at': d.get('terms_accepted_at', ''),
            'delivered_at': d.get('delivered_at', ''),
            'key_delivered': d.get('key_value', ''),
            'created_at': d.get('created_at', ''),
            'updated_at': d.get('updated_at', ''),
        }
    })
