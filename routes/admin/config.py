"""
Config - Configurações do projeto
"""
from flask import request, jsonify, session, send_file
from database.models import get_db_connection
from database.connection import get_db_path
import os
import time


def update_config():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    pix_key = request.form.get('pix_key') or ''
    pix_copia_cola = request.form.get('pix_copia_cola') or ''
    contact_whatsapp = request.form.get('contact_whatsapp') or ''
    mercado_pago_token = (request.form.get('mercado_pago_token') or '').strip()

    conn = get_db_connection()
    config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
    try:
        if not config:
            conn.execute(
                'INSERT INTO config (id, pix_key, pix_copia_cola, contact_whatsapp, mercado_pago_token) VALUES (1, ?, ?, ?, ?)',
                (pix_key, pix_copia_cola, contact_whatsapp, mercado_pago_token or '')
            )
        else:
            # Não sobrescrever token se vazio
            if not mercado_pago_token and 'mercado_pago_token' in config.keys():
                mercado_pago_token = config['mercado_pago_token'] or ''
            conn.execute(
                'UPDATE config SET pix_key = ?, pix_copia_cola = ?, contact_whatsapp = ?, mercado_pago_token = ? WHERE id = 1',
                (pix_key, pix_copia_cola, contact_whatsapp, mercado_pago_token)
            )
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500
    conn.close()
    return jsonify({'success': True})


def backup_database():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    try:
        db_path = get_db_path()
        if not os.path.exists(db_path):
            return jsonify({'error': 'Arquivo de banco de dados não encontrado'}), 404
            
        timestamp = int(time.time())
        filename = f"backup_database_{timestamp}.db"
        
        return send_file(
            db_path, 
            as_attachment=True, 
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
