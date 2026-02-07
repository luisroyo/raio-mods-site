"""
Products - CRUD de produtos
"""
from flask import request, jsonify, session
from database.models import get_db_connection
from .helpers import handle_image_upload, IOF, get_dolar_hoje
import sqlite3


def add_product():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    name = request.form.get('name')
    desc = request.form.get('description')
    price = request.form.get('price')
    cat = request.form.get('category')
    tagline = (request.form.get('tagline') or '').strip()
    payment_url = (request.form.get('payment_url') or '').strip()
    promo_price = (request.form.get('promo_price') or '').strip()
    promo_label = (request.form.get('promo_label') or '').strip()
    
    # cost_usd
    try:
        cost_usd = float(request.form.get('cost_usd', 0) or 0)
    except:
        cost_usd = 0.0
    
    # apply_iof checkbox
    try:
        vals = request.form.getlist('apply_iof')
        if vals:
            apply_iof = int(vals[-1])
        else:
            apply_iof = int(request.form.get('apply_iof', 1) or 1)
    except:
        apply_iof = 1

    # is_active checkbox
    try:
        vals_active = request.form.getlist('is_active')
        if vals_active:
            is_active = int(vals_active[-1])
        else:
            is_active = int(request.form.get('is_active', 1) or 1)
    except:
        is_active = 1
    
    try:
        is_catalog = int(request.form.get('is_catalog', 0))
    except:
        is_catalog = 0
    try:
        sort_order = int(request.form.get('sort_order') or 0)
    except:
        sort_order = 0
    
    parent_id = request.form.get('parent_id')
    if not parent_id or str(parent_id).strip() == '':
        parent_id = None
    
    image = handle_image_upload(request)
    
    if not all([name, desc, price, image, cat]):
        return jsonify({'error': 'Faltam dados'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO products (name, description, price, image, category, tagline, sort_order, parent_id, is_catalog, payment_url, promo_price, promo_label, cost_usd, apply_iof, is_active) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (name, desc, price, image, cat, tagline, sort_order, parent_id, is_catalog, payment_url, promo_price, promo_label, cost_usd, apply_iof, is_active)
        )
        conn.commit()
    except sqlite3.OperationalError as e:
        conn.close()
        return jsonify({'error': 'Erro no banco de dados: ' + str(e)}), 500
        
    conn.close()
    return jsonify({'success': True, 'message': 'Adicionado!'})


def delete_product(pid):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    conn = get_db_connection()
    conn.execute('UPDATE products SET parent_id = NULL WHERE parent_id = ?', (pid,))
    conn.execute('DELETE FROM products WHERE id = ?', (pid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Removido!'})


def edit_product(pid):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    try:
        conn = get_db_connection()
        row = conn.execute('SELECT * FROM products WHERE id = ?', (pid,)).fetchone()
        if not row:
            conn.close()
            return jsonify({'error': '404'}), 404
        
        existing = dict(row)
        name = request.form.get('name') or existing.get('name', '')
        desc = request.form.get('description') or existing.get('description', '')
        price = request.form.get('price') or existing.get('price', '')
        cat = request.form.get('category') or existing.get('category', '')
        tagline = request.form.get('tagline', existing.get('tagline', '')).strip()
        payment_url = request.form.get('payment_url', existing.get('payment_url', '')).strip()
        promo_price = (request.form.get('promo_price') or existing.get('promo_price') or '').strip()
        promo_label = (request.form.get('promo_label') or existing.get('promo_label') or '').strip()
        
        # cost_usd
        try:
            cost_usd = float(request.form.get('cost_usd') or existing.get('cost_usd', 0) or 0)
        except:
            cost_usd = float(existing.get('cost_usd', 0) or 0)
        
        # apply_iof
        try:
            vals = request.form.getlist('apply_iof')
            if vals:
                apply_iof = int(vals[-1])
            else:
                apply_iof = int(request.form.get('apply_iof', existing.get('apply_iof', 1)) or 1)
        except:
            apply_iof = int(existing.get('apply_iof', 1) or 1)

        # is_active
        try:
            vals_active = request.form.getlist('is_active')
            if vals_active:
                is_active = int(vals_active[-1])
            else:
                is_active = int(request.form.get('is_active', existing.get('is_active', 1)) or 1)
        except:
            is_active = int(existing.get('is_active', 1) or 1)
        
        try:
            is_catalog = int(request.form.get('is_catalog', existing.get('is_catalog', 0)))
        except:
            is_catalog = 0
        try:
            sort = int(request.form.get('sort_order') or existing.get('sort_order', 0))
        except:
            sort = 0
        
        pid_val = request.form.get('parent_id')
        
        # Se for catálogo, não pode ter pai
        if is_catalog == 1:
            pid_val = None
        elif pid_val == str(pid) or not pid_val or str(pid_val).strip() == '':
            pid_val = None
        
        img = handle_image_upload(request, existing.get('image', ''))

        conn.execute(
            'UPDATE products SET name=?, description=?, price=?, image=?, category=?, tagline=?, sort_order=?, parent_id=?, is_catalog=?, payment_url=?, promo_price=?, promo_label=?, cost_usd=?, apply_iof=?, is_active=? WHERE id=?',
            (name, desc, price, img, cat, tagline, sort, pid_val, is_catalog, payment_url, promo_price, promo_label, cost_usd, apply_iof, is_active, pid)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Atualizado!'})
        
    except sqlite3.OperationalError as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'Erro ao atualizar: {str(e)}'}), 500
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


def product_info(pid):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    try:
        conn = get_db_connection()
        row = conn.execute('SELECT id, cost_usd, apply_iof, is_active FROM products WHERE id = ?', (pid,)).fetchone()
        conn.close()
        if not row:
            return jsonify({'error': '404'}), 404

        dolar_rate = get_dolar_hoje()

        cost_usd = float(row['cost_usd'] or 0)
        apply_iof = int(row['apply_iof']) if 'apply_iof' in row.keys() and row['apply_iof'] is not None else 1

        calculated_cost_brl = 0.0
        if cost_usd > 0:
            if apply_iof == 1:
                calculated_cost_brl = round(cost_usd * dolar_rate * IOF, 2)
            else:
                calculated_cost_brl = round(cost_usd * dolar_rate, 2)

        return jsonify({
            'id': row['id'],
            'cost_usd': round(cost_usd, 2),
            'apply_iof': apply_iof,
            'is_active': int(row['is_active']) if 'is_active' in row.keys() and row['is_active'] is not None else 1,
            'dolar_rate': round(dolar_rate, 4),
            'calculated_cost_brl': calculated_cost_brl
        })
    except Exception as e:
        print(f"Erro product_info: {e}")
        return jsonify({'error': str(e)}), 500
