import os
from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, current_app
from database.models import get_db_connection

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE parent_id IS NULL ORDER BY sort_order ASC, id ASC').fetchall()
    
    catalog_ids = set()
    for p in products:
        is_cat = p['is_catalog'] if 'is_catalog' in p.keys() else 0
        if is_cat == 1: catalog_ids.add(p['id'])
            
    legacy = conn.execute('SELECT parent_id FROM products WHERE parent_id IS NOT NULL').fetchall()
    for r in legacy: catalog_ids.add(r[0])
    
    conn.close()
    return render_template('index.html', products=products, catalog_ids=catalog_ids)

@public_bp.route('/catalogo/<int:parent_id>')
def catalogo(parent_id):
    conn = get_db_connection()
    parent = conn.execute('SELECT * FROM products WHERE id = ?', (parent_id,)).fetchone()
    if not parent:
        conn.close(); return redirect(url_for('public.index'))
    children = conn.execute('SELECT * FROM products WHERE parent_id = ? ORDER BY sort_order ASC, id ASC', (parent_id,)).fetchall()
    conn.close()
    return render_template('catalogo.html', parent=parent, products=children)

@public_bp.route('/links')
def links():
    conn = get_db_connection()
    links = conn.execute('SELECT * FROM links ORDER BY created_at DESC').fetchall()
    products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('links.html', links=links, products=products)

@public_bp.route('/pagamento')
def pagamento():
    conn = get_db_connection()
    try:
        config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
    except:
        config = None
        
    produto_nome = request.args.get('produto')
    product_data = None
    if produto_nome:
        product_data = conn.execute('SELECT * FROM products WHERE name = ?', (produto_nome,)).fetchone()
    conn.close()
    return render_template('pagamento.html', product=product_data, config=config)

@public_bp.route('/seguranca')
def seguranca():
    return render_template('seguranca.html')

@public_bp.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    return send_from_directory(uploads_dir, filename)