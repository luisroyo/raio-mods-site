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
    
    conn = get_db_connection()
    recharges = conn.execute('SELECT * FROM panel_recharges ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return jsonify([dict(r) for r in recharges])


def delete_panel_recharge(recharge_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    conn.execute('DELETE FROM panel_recharges WHERE id = ?', (recharge_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})
