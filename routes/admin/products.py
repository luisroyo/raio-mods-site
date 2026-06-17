"""
Products - CRUD de produtos
"""
from flask import Blueprint, request, jsonify, session
from database.models import get_db_connection
from database.orm import db
from database.models_orm import Product
from .helpers import handle_image_upload, IOF, get_dolar_hoje
import sqlite3

def add_product():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    name = request.form.get('name')
    desc = request.form.get('description') or ''
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
        
    # cost_brl
    try:
        cost_brl = float(request.form.get('cost_brl', 0) or 0)
    except:
        cost_brl = 0.0
    
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
    
    supplier = (request.form.get('supplier') or '').strip()
    image = handle_image_upload(request) or ''
    
    if not all([name, price, cat]):
        return jsonify({'error': 'Faltam dados'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO products (name, description, price, image, category, tagline, sort_order, parent_id, is_catalog, payment_url, promo_price, promo_label, cost_usd, cost_brl, apply_iof, is_active, supplier) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (name, desc, price, image, cat, tagline, sort_order, parent_id, is_catalog, payment_url, promo_price, promo_label, cost_usd, cost_brl, apply_iof, is_active, supplier)
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
    
    try:
        # 1. Update subproducts parent_id to NULL
        Product.query.filter_by(parent_id=pid).update({Product.parent_id: None})
        
        # 2. Retrieve and delete product
        prod = Product.query.get(pid)
        if prod:
            db.session.delete(prod)
            db.session.commit()
            
        return jsonify({'success': True, 'message': 'Removido!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover produto: {str(e)}'}), 500


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
        
        desc = request.form.get('description')
        if desc is None:
            desc = existing.get('description', '')
            
        price = request.form.get('price') or existing.get('price', '')
        cat = request.form.get('category') or existing.get('category', '')
        
        tagline = request.form.get('tagline')
        if tagline is not None:
            tagline = tagline.strip()
        else:
            tagline = existing.get('tagline', '')

        payment_url = request.form.get('payment_url')
        if payment_url is not None:
            payment_url = payment_url.strip()
        else:
            payment_url = existing.get('payment_url', '')

        promo_price = request.form.get('promo_price')
        if promo_price is not None:
            promo_price = promo_price.strip()
        else:
            promo_price = existing.get('promo_price', '')

        promo_label = request.form.get('promo_label')
        if promo_label is not None:
            promo_label = promo_label.strip()
        else:
            promo_label = existing.get('promo_label', '')

        # Se o preço da promoção for vazio, limpa a promoção inteira
        if not promo_price:
            promo_price = ""
            promo_label = ""
        
        # cost_usd
        try:
            cost_usd = float(request.form.get('cost_usd') or existing.get('cost_usd', 0) or 0)
        except:
            cost_usd = float(existing.get('cost_usd', 0) or 0)
            
        # cost_brl
        try:
            cost_brl = float(request.form.get('cost_brl') or existing.get('cost_brl', 0) or 0)
        except:
            cost_brl = float(existing.get('cost_brl', 0) or 0)
        
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
        
        # Opcional ter pai, mesmo se for catalogo
        if pid_val == str(pid) or not pid_val or str(pid_val).strip() == '':
            pid_val = None
        
        supplier = request.form.get('supplier')
        if supplier is None:
            supplier = existing.get('supplier', '')
        supplier = supplier.strip()
        
        img = handle_image_upload(request, existing.get('image', '')) or ''

        conn.execute(
            'UPDATE products SET name=?, description=?, price=?, image=?, category=?, tagline=?, sort_order=?, parent_id=?, is_catalog=?, payment_url=?, promo_price=?, promo_label=?, cost_usd=?, cost_brl=?, apply_iof=?, is_active=?, supplier=? WHERE id=?',
            (name, desc, price, img, cat, tagline, sort, pid_val, is_catalog, payment_url, promo_price, promo_label, cost_usd, cost_brl, apply_iof, is_active, supplier, pid)
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
        prod = Product.query.get(pid)
        if not prod:
            return jsonify({'error': '404'}), 404

        dolar_rate = get_dolar_hoje()

        cost_usd = float(prod.cost_usd or 0)
        cost_brl = float(prod.cost_brl or 0)
        apply_iof = int(prod.apply_iof) if prod.apply_iof is not None else 1

        calculated_cost_brl = 0.0
        if cost_brl > 0:
            calculated_cost_brl = round(cost_brl, 2)
        elif cost_usd > 0:
            if apply_iof == 1:
                calculated_cost_brl = round(cost_usd * dolar_rate * IOF, 2)
            else:
                calculated_cost_brl = round(cost_usd * dolar_rate, 2)

        return jsonify({
            'id': prod.id,
            'cost_usd': round(cost_usd, 2),
            'cost_brl': round(cost_brl, 2),
            'apply_iof': apply_iof,
            'is_active': int(prod.is_active) if prod.is_active is not None else 1,
            'dolar_rate': round(dolar_rate, 4),
            'calculated_cost_brl': calculated_cost_brl
        })
    except Exception as e:
        print(f"Erro product_info: {e}")
        return jsonify({'error': str(e)}), 500


def register_products_routes(bp):
    bp.route('/admin/add', methods=['POST'])(add_product)
    bp.route('/admin/delete/<int:pid>', methods=['POST'])(delete_product)
    bp.route('/admin/edit/<int:pid>', methods=['POST'])(edit_product)
    bp.route('/admin/product/info/<int:pid>', methods=['GET'])(product_info)

