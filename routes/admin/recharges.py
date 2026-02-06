"""
Recharges - Recargas de painel
"""
from flask import request, jsonify, session
from database.models import get_db_connection
from .helpers import get_dolar_hoje


def add_panel_recharge():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    try:
        quantity = int(request.form.get('quantity', 0))
        cost_per_unit_usd = float(request.form.get('cost_per_unit_usd', 0))
        dolar_rate = float(request.form.get('dolar_rate', get_dolar_hoje()))
        notes = request.form.get('notes', '').strip()
        
        if quantity <= 0 or cost_per_unit_usd <= 0:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        total_cost_usd = quantity * cost_per_unit_usd
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO panel_recharges (quantity, cost_per_unit_usd, total_cost_usd, dolar_rate, notes) VALUES (?,?,?,?,?)',
            (quantity, cost_per_unit_usd, total_cost_usd, dolar_rate, notes)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Recarga de painel registrada!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def list_panel_recharges():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401

    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit

        conn = get_db_connection()
        
        # Total count
        total_items = conn.execute('SELECT COUNT(*) FROM panel_recharges').fetchone()[0]

        # Paginated data
        recharges = conn.execute(f'''
            SELECT * FROM panel_recharges 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset)).fetchall()
        
        conn.close()
        
        return jsonify({
            'data': [dict(r) for r in recharges],
            'total': total_items,
            'page': page,
            'limit': limit,
            'pages': (total_items + limit - 1) // limit
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def edit_panel_recharge(recharge_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    try:
        conn = get_db_connection()
        existing = conn.execute('SELECT * FROM panel_recharges WHERE id = ?', (recharge_id,)).fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': 'Recarga não encontrada'}), 404
            
        quantity = int(request.form.get('quantity', 0))
        cost_per_unit_usd = float(request.form.get('cost_per_unit_usd', 0))
        dolar_rate = float(request.form.get('dolar_rate', 0))
        notes = request.form.get('notes', '').strip()
        
        if quantity <= 0 or cost_per_unit_usd <= 0 or dolar_rate <= 0:
            conn.close()
            return jsonify({'error': 'Dados inválidos'}), 400
        
        total_cost_usd = quantity * cost_per_unit_usd
        
        conn.execute('''
            UPDATE panel_recharges 
            SET quantity=?, cost_per_unit_usd=?, total_cost_usd=?, dolar_rate=?, notes=?
            WHERE id=?
        ''', (quantity, cost_per_unit_usd, total_cost_usd, dolar_rate, notes, recharge_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Recarga atualizada com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def delete_panel_recharge(recharge_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    conn.execute('DELETE FROM panel_recharges WHERE id = ?', (recharge_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})
