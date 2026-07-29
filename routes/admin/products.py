"""
Products - CRUD de produtos
"""
from flask import Blueprint, request, jsonify, session
from database.models import get_db_connection
from database.orm import db
from database.models_orm import Product
from .helpers import handle_image_upload, IOF, get_dolar_hoje
import sqlite3
from telegram_app.repositories.product_repository import ProductRepository

def add_product():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    name = request.form.get('name')
    desc = request.form.get('description') or ''
    price = request.form.get('price')
    cat = request.form.get('category', '').strip()
    tagline = (request.form.get('tagline') or '').strip()
    payment_url = (request.form.get('payment_url') or '').strip()
    promo_price = (request.form.get('promo_price') or '').strip()
    promo_label = (request.form.get('promo_label') or '').strip()
    link_id_val = request.form.get('link_id', '').strip()
    link_id = int(link_id_val) if link_id_val and link_id_val.isdigit() else None
    download_link = (request.form.get('download_link') or '').strip()
    
    try:
        rp_val = request.form.get('reseller_price')
        reseller_price = float(str(rp_val).replace(',', '.') if rp_val else 0.0)
    except:
        reseller_price = 0.0
    
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
    
    # Novas propriedades de i18n e multi-moeda
    name_pt = (request.form.get('name_pt') or name or '').strip()
    name_en = (request.form.get('name_en') or '').strip()
    name_es = (request.form.get('name_es') or '').strip()
    
    description_pt = (request.form.get('description_pt') or desc or '').strip()
    description_en = (request.form.get('description_en') or '').strip()
    description_es = (request.form.get('description_es') or '').strip()
    
    try:
        p_brl = request.form.get('price_brl')
        price_brl = float(str(p_brl).replace(',', '.') if p_brl else 0.0)
    except:
        price_brl = 0.0
        
    try:
        p_usd = request.form.get('price_usd')
        price_usd = float(str(p_usd).replace(',', '.') if p_usd else 0.0)
    except:
        price_usd = 0.0
        
    # Se price_brl nao foi enviado mas price sim, tenta fazer parse de price
    if not price_brl and price:
        cleaned = price.replace('R$', '').replace('$', '').strip()
        if ',' in cleaned and '.' not in cleaned:
            cleaned = cleaned.replace(',', '.')
        elif ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace('.', '').replace(',', '.')
        try:
            price_brl = float(cleaned)
        except:
            price_brl = 0.0
            
    default_currency = (request.form.get('default_currency') or 'BRL').strip().upper()
    if default_currency not in ['BRL', 'USD']:
        default_currency = 'BRL'
        
    translation_status = (request.form.get('translation_status') or 'draft').strip().lower()
    if translation_status not in ['draft', 'partial', 'complete']:
        translation_status = 'draft'

    if not all([name, price, cat]):
        return jsonify({'error': 'Faltam dados'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute(
            '''INSERT INTO products (
                name, description, price, image, category, tagline, sort_order, parent_id, is_catalog, 
                payment_url, promo_price, promo_label, cost_usd, cost_brl, apply_iof, is_active, supplier, 
                reseller_price, download_link, name_pt, name_en, name_es, description_pt, description_en, 
                description_es, price_brl, price_usd, default_currency, translation_status, link_id
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (
                name, desc, price, image, cat, tagline, sort_order, parent_id, is_catalog, 
                payment_url, promo_price, promo_label, cost_usd, cost_brl, apply_iof, is_active, supplier, 
                reseller_price, download_link, name_pt, name_en, name_es, description_pt, description_en, 
                description_es, price_brl, price_usd, default_currency, translation_status, link_id
            )
        )
        conn.commit()
    except sqlite3.OperationalError as e:
        conn.close()
        return jsonify({'error': 'Erro no banco de dados: ' + str(e)}), 500
        
    conn.close()
    ProductRepository.clear_cache()
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
            
        ProductRepository.clear_cache()
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
            
        download_link = request.form.get('download_link')
        if download_link is not None:
            download_link = download_link.strip()
        else:
            download_link = existing.get('download_link', '')
            
        link_id_val = request.form.get('link_id')
        if link_id_val is not None:
            link_id_val = link_id_val.strip()
            link_id = int(link_id_val) if link_id_val.isdigit() else None
        else:
            link_id = existing.get('link_id')

        # Se o preço da promoção for vazio, limpa a promoção inteira
        if not promo_price:
            promo_price = ""
            promo_label = ""
        
        # reseller_price
        try:
            rp_val = request.form.get('reseller_price')
            if rp_val:
                reseller_price = float(str(rp_val).replace(',', '.'))
            else:
                reseller_price = float(existing.get('reseller_price', 0) or 0)
        except:
            reseller_price = float(existing.get('reseller_price', 0) or 0)
            
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

        # Novas propriedades de i18n e multi-moeda
        name_pt = request.form.get('name_pt')
        if name_pt is None:
            name_pt = existing.get('name_pt', '')
        name_pt = name_pt.strip()

        name_en = request.form.get('name_en')
        if name_en is None:
            name_en = existing.get('name_en', '')
        name_en = name_en.strip()

        name_es = request.form.get('name_es')
        if name_es is None:
            name_es = existing.get('name_es', '')
        name_es = name_es.strip()

        description_pt = request.form.get('description_pt')
        if description_pt is None:
            description_pt = existing.get('description_pt', '')
        description_pt = description_pt.strip()

        description_en = request.form.get('description_en')
        if description_en is None:
            description_en = existing.get('description_en', '')
        description_en = description_en.strip()

        description_es = request.form.get('description_es')
        if description_es is None:
            description_es = existing.get('description_es', '')
        description_es = description_es.strip()

        try:
            p_brl = request.form.get('price_brl')
            if p_brl is not None:
                price_brl = float(str(p_brl).replace(',', '.'))
            else:
                price_brl = float(existing.get('price_brl', 0) or 0)
        except:
            price_brl = float(existing.get('price_brl', 0) or 0)

        try:
            p_usd = request.form.get('price_usd')
            if p_usd is not None:
                price_usd = float(str(p_usd).replace(',', '.'))
            else:
                price_usd = float(existing.get('price_usd', 0) or 0)
        except:
            price_usd = float(existing.get('price_usd', 0) or 0)

        default_currency = request.form.get('default_currency')
        if default_currency is None:
            default_currency = existing.get('default_currency', 'BRL')
        default_currency = default_currency.strip().upper()
        if default_currency not in ['BRL', 'USD']:
            default_currency = 'BRL'

        translation_status = request.form.get('translation_status')
        if translation_status is None:
            translation_status = existing.get('translation_status', 'draft')
        translation_status = translation_status.strip().lower()
        if translation_status not in ['draft', 'partial', 'complete']:
            translation_status = 'draft'

        conn.execute(
            '''UPDATE products SET 
                name=?, description=?, price=?, image=?, category=?, tagline=?, sort_order=?, parent_id=?, 
                is_catalog=?, payment_url=?, promo_price=?, promo_label=?, cost_usd=?, cost_brl=?, apply_iof=?, 
                is_active=?, supplier=?, reseller_price=?, download_link=?,
                name_pt=?, name_en=?, name_es=?, description_pt=?, description_en=?, description_es=?,
                price_brl=?, price_usd=?, default_currency=?, translation_status=?, link_id=?
            WHERE id=?''',
            (
                name, desc, price, img, cat, tagline, sort, pid_val, 
                is_catalog, payment_url, promo_price, promo_label, cost_usd, cost_brl, apply_iof, 
                is_active, supplier, reseller_price, download_link,
                name_pt, name_en, name_es, description_pt, description_en, description_es,
                price_brl, price_usd, default_currency, translation_status, link_id,
                pid
            )
        )
        conn.commit()
        conn.close()
        ProductRepository.clear_cache()
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

        # Buscar estoque de chaves disponíveis
        conn = get_db_connection()
        stock_row = conn.execute('SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = 0', (pid,)).fetchone()
        stock_count = stock_row[0] if stock_row else 0
        conn.close()

        return jsonify({
            'id': prod.id,
            'name': prod.name,
            'price': prod.price,
            'promo_price': prod.promo_price,
            'cost_usd': round(cost_usd, 2),
            'cost_brl': round(cost_brl, 2),
            'apply_iof': apply_iof,
            'is_active': int(prod.is_active) if prod.is_active is not None else 1,
            'dolar_rate': round(dolar_rate, 4),
            'calculated_cost_brl': calculated_cost_brl,
            'stock': stock_count,
            'download_link': prod.download_link or '',
            'name_pt': prod.name_pt or '',
            'name_en': prod.name_en or '',
            'name_es': prod.name_es or '',
            'description_pt': prod.description_pt or '',
            'description_en': prod.description_en or '',
            'description_es': prod.description_es or '',
            'price_brl': float(prod.price_brl or 0.0),
            'price_usd': float(prod.price_usd or 0.0),
            'default_currency': prod.default_currency or 'BRL',
            'translation_status': prod.translation_status or 'draft',
            'link_id': prod.link_id
        })
    except Exception as e:
        print(f"Erro product_info: {e}")
        return jsonify({'error': str(e)}), 500


def register_products_routes(bp):
    bp.route('/admin/add', methods=['POST'])(add_product)
    bp.route('/admin/delete/<int:pid>', methods=['POST'])(delete_product)
    bp.route('/admin/edit/<int:pid>', methods=['POST'])(edit_product)
    bp.route('/admin/product/info/<int:pid>', methods=['GET'])(product_info)

