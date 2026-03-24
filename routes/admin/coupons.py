from flask import request, jsonify, session
from database.models import get_db_connection

def list_coupons():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    coupons = conn.execute('SELECT * FROM coupons ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return jsonify([dict(c) for c in coupons])

def add_coupon():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401

    try:
        code = request.form.get('code', '').strip().upper()
        discount_type = request.form.get('discount_type', 'percent')
        discount_value = float(request.form.get('discount_value', 0))
        max_uses = int(request.form.get('max_uses', 0))
        valid_until = request.form.get('valid_until')

        if not code or discount_value <= 0:
            return jsonify({'error': 'Dados inválidos'}), 400
            
        if valid_until:
            valid_until = valid_until.replace('T', ' ')
            if len(valid_until) == 10:
                valid_until += " 23:59:59"
        else:
            valid_until = None

        conn = get_db_connection()
        # Verificar duplicidade
        exist = conn.execute('SELECT 1 FROM coupons WHERE code = ?', (code,)).fetchone()
        if exist:
            conn.close()
            return jsonify({'error': 'Já existe um cupom com este código!'}), 400

        conn.execute('''
            INSERT INTO coupons (code, discount_type, discount_value, max_uses, valid_until)
            VALUES (?, ?, ?, ?, ?)
        ''', (code, discount_type, discount_value, max_uses, valid_until))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Cupom criado!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def delete_coupon(coupon_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401

    conn = get_db_connection()
    conn.execute('DELETE FROM coupons WHERE id = ?', (coupon_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})
