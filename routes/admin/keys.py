"""
Keys - Gerenciamento de chaves de produtos
"""
from flask import request, jsonify, session
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
