"""
Keys - Gerenciamento de chaves de produtos
"""
from flask import Blueprint, request, jsonify, session
from database.models import get_db_connection

def add_keys():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    product_id = request.form.get('product_id')
    keys_text = request.form.get('keys_list')
    
    if not product_id or not keys_text:
        return jsonify({'error': 'Dados inválidos'}), 400
        
    # Separa por quebra de linha
    key_list = [k.strip() for k in keys_text.splitlines() if k.strip()]
    
    if not key_list:
        return jsonify({'error': 'Nenhuma chave válida encontrada'}), 400
        
    conn = get_db_connection()
    count = 0
    for key in key_list:
        # Verifica duplicidade
        exists = conn.execute('SELECT id FROM product_keys WHERE key_value = ?', (key,)).fetchone()
        if not exists:
            conn.execute('INSERT INTO product_keys (product_id, key_value, is_used) VALUES (?, ?, 0)', (product_id, key))
            count += 1
            
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': f'{count} chaves adicionadas com sucesso!'})


def list_keys(product_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    keys = conn.execute(
        'SELECT * FROM product_keys WHERE product_id = ? ORDER BY is_used ASC, id DESC',
        (product_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(k) for k in keys])


def delete_key(key_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    conn.execute('DELETE FROM product_keys WHERE id = ?', (key_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})


def redeem_key_admin():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    try:
        product_id = request.form.get('product_id')
        client_name = (request.form.get('client_name') or '').strip()
        client_email = (request.form.get('client_email') or '').strip().lower()
        unit_price = float(str(request.form.get('unit_price', 0)).replace('R$', '').replace(',', '.'))
        
        if not product_id or unit_price < 0:
            return jsonify({'error': 'Dados inválidos'}), 400
            
        conn = get_db_connection()
        
        # 1. Verificar se o produto existe
        product = conn.execute('SELECT name, cost_usd, cost_brl, apply_iof FROM products WHERE id = ?', (product_id,)).fetchone()
        if not product:
            conn.close()
            return jsonify({'error': 'Produto não encontrado'}), 404
            
        # 2. Buscar uma chave disponível (is_used = 0)
        key_row = conn.execute('SELECT id, key_value FROM product_keys WHERE product_id = ? AND is_used = 0 LIMIT 1', (product_id,)).fetchone()
        if not key_row:
            conn.close()
            return jsonify({'error': 'Sem chaves disponíveis em estoque para este produto. Por favor, adicione chaves primeiro.'}), 400
            
        # 3. Marcar chave como usada
        used_by = f"Admin (Resgate manual para {client_name})" if client_name else "Admin (Resgate manual)"
        if client_email:
            used_by += f" - {client_email}"
        conn.execute('UPDATE product_keys SET is_used = 1, used_by_email = ? WHERE id = ?', (used_by, key_row['id']))
        
        # 4. Calcular o custo unitário em BRL do produto
        cost_per_unit_brl = 0.0
        cost_usd = float(product['cost_usd'] or 0.0)
        cost_brl = float(product['cost_brl'] or 0.0) if 'cost_brl' in dict(product) else 0.0
        apply_iof = int(product['apply_iof']) if 'apply_iof' in dict(product) and product['apply_iof'] is not None else 1
        
        if cost_brl > 0:
            cost_per_unit_brl = round(cost_brl, 2)
        elif cost_usd > 0:
            from routes.admin.helpers import get_dolar_hoje, IOF
            dolar_rate = get_dolar_hoje()
            if apply_iof == 1:
                cost_per_unit_brl = round(cost_usd * dolar_rate * IOF, 2)
            else:
                cost_per_unit_brl = round(cost_usd * dolar_rate, 2)
                
        # 5. Inserir na tabela de manual_sales
        cursor = conn.execute('''
            INSERT INTO manual_sales (product_id, quantity, unit_price, cost_per_unit_brl, total_price, client_name, client_email)
            VALUES (?, 1, ?, ?, ?, ?, ?)
        ''', (product_id, unit_price, cost_per_unit_brl, unit_price, client_name, client_email))
        sale_id = cursor.lastrowid
        
        # 6. Atribuir pontos de fidelidade se e-mail estiver definido
        if client_email:
            points_to_add = int(unit_price)
            if points_to_add > 0:
                client_row = conn.execute('SELECT points FROM client_points WHERE email = ?', (client_email,)).fetchone()
                if client_row:
                    conn.execute('UPDATE client_points SET points = points + ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?', (points_to_add, client_email))
                else:
                    conn.execute('INSERT INTO client_points (email, points) VALUES (?, ?)', (client_email, points_to_add))
                
                conn.execute(
                    'INSERT INTO points_history (email, points_changed, action_type, description) VALUES (?, ?, ?, ?)',
                    (client_email, points_to_add, 'earn_manual', f"Resgate manual + Venda #{sale_id} - {product['name']}")
                )
                
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Chave resgatada e venda registrada com sucesso!',
            'key': key_row['key_value'],
            'sale': {
                'id': sale_id,
                'product_name': product['name'],
                'client_name': client_name,
                'unit_price': unit_price,
                'key_value': key_row['key_value']
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erro ao processar resgate: {str(e)}'}), 500


def register_keys_routes(bp):
    bp.route('/admin/keys/add', methods=['POST'])(add_keys)
    bp.route('/admin/keys/list/<int:product_id>', methods=['GET'])(list_keys)
    bp.route('/admin/keys/delete/<int:key_id>', methods=['POST'])(delete_key)
    bp.route('/admin/keys/redeem', methods=['POST'])(redeem_key_admin)

