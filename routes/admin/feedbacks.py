from flask import request, jsonify, session
from database.models import get_db_connection

def list_feedbacks():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    # Busca feedbacks e opcionalmente o nome do produto se houver product_id
    feedbacks = conn.execute('''
        SELECT f.*, p.name as product_name 
        FROM feedbacks f 
        LEFT JOIN products p ON f.product_id = p.id 
        ORDER BY f.created_at DESC
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(f) for f in feedbacks])

def approve_feedback(fid):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    conn.execute("UPDATE feedbacks SET status = 'approved' WHERE id = ?", (fid,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Feedback aprovado com sucesso!'})

def reject_feedback(fid):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    conn.execute("UPDATE feedbacks SET status = 'rejected' WHERE id = ?", (fid,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Feedback rejeitado com sucesso!'})

def delete_feedback(fid):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    conn.execute("DELETE FROM feedbacks WHERE id = ?", (fid,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Feedback excluído com sucesso!'})
