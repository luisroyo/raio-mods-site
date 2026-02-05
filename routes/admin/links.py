"""
Links - CRUD de links úteis
"""
from flask import request, jsonify, session
from database.models import get_db_connection
from .helpers import handle_image_upload


def add_link():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    title = (request.form.get('title') or '').strip()
    description = (request.form.get('description') or '').strip()
    download_link = (request.form.get('download_link') or '').strip()
    video_link = (request.form.get('video_link') or '').strip()
    game = (request.form.get('game') or '').strip()
    
    if not title:
        return jsonify({'error': 'Título obrigatório'}), 400
    if not download_link and not video_link:
        return jsonify({'error': 'Pelo menos um link necessário'}), 400
    
    image = handle_image_upload(request)
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO links (title, description, image, download_link, video_link, game) VALUES (?,?,?,?,?,?)',
        (title, description, image, download_link, video_link, game)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})


def delete_link(lid):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    conn = get_db_connection()
    conn.execute('DELETE FROM links WHERE id = ?', (lid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


def edit_link(lid):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM links WHERE id = ?', (lid,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': '404'}), 404
    
    existing = dict(existing)
    title = (request.form.get('title') or existing.get('title', '')).strip()
    description = (request.form.get('description') or '').strip()
    download_link = (request.form.get('download_link') or '').strip()
    video_link = (request.form.get('video_link') or '').strip()
    game = (request.form.get('game') or '').strip()
    
    if not download_link and not video_link:
        conn.close()
        return jsonify({'error': 'Pelo menos um link'}), 400
    
    image = handle_image_upload(request, existing.get('image', ''))
    
    conn.execute(
        'UPDATE links SET title=?, description=?, image=?, download_link=?, video_link=?, game=? WHERE id=?',
        (title, description, image, download_link, video_link, game, lid)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})
