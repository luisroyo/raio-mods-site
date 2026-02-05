import os
from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, current_app
from database.models import get_db_connection

public_bp = Blueprint('public', __name__)


def _get_stock_map(conn, product_ids):
    """Retorna dict product_id -> quantidade de chaves disponíveis (is_used=0)."""
    if not product_ids:
        return {}
    placeholders = ','.join('?' * len(product_ids))
    rows = conn.execute(
        'SELECT product_id, COUNT(*) as total FROM product_keys WHERE is_used = 0 AND product_id IN ({}) GROUP BY product_id'.format(placeholders),
        list(product_ids)
    ).fetchall()
    return {row['product_id']: row['total'] for row in rows}


def _get_whatsapp_from_config(conn):
    """Retorna número WhatsApp para contato (contact_whatsapp ou whatsapp_number)."""
    try:
        config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
    except Exception:
        return ''
    if not config:
        return ''
    # sqlite3.Row não tem .get(); converter para dict ou acessar por índice
    d = dict(config)
    num = (d.get('contact_whatsapp') or d.get('whatsapp_number') or '').strip()
    return num if num else ''


def _safe_page_param():
    """Retorna o parâmetro page da URL como int, ou 1 se inválido."""
    try:
        return max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        return 1


@public_bp.route('/')
def index():
    page = _safe_page_param()
    per_page = 20
    offset = (page - 1) * per_page

    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM products WHERE parent_id IS NULL').fetchone()[0]
    products = conn.execute(
        'SELECT * FROM products WHERE parent_id IS NULL ORDER BY sort_order ASC, id ASC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()

    catalog_ids = set()
    for p in products:
        is_cat = p['is_catalog'] if 'is_catalog' in p.keys() else 0
        if is_cat == 1: catalog_ids.add(p['id'])

    legacy = conn.execute('SELECT parent_id FROM products WHERE parent_id IS NOT NULL').fetchall()
    for r in legacy: catalog_ids.add(r[0])

    # Estoque só para produtos “soltos” (que têm botão Comprar)
    standalone_ids = [p['id'] for p in products if p['id'] not in catalog_ids]
    stock_map = _get_stock_map(conn, standalone_ids)
    whatsapp_contact = _get_whatsapp_from_config(conn)

    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    conn.close()
    return render_template('index.html', products=products, catalog_ids=catalog_ids,
                          stock_map=stock_map, whatsapp_contact=whatsapp_contact,
                          page=page, total_pages=total_pages, total=total)


@public_bp.route('/busca')
def busca():
    q = (request.args.get('q') or '').strip()
    if not q:
        return redirect(url_for('public.index'))
    term = f'%{q}%'
    conn = get_db_connection()
    results = conn.execute(
        'SELECT * FROM products WHERE (name LIKE ? OR description LIKE ? OR category LIKE ?) ORDER BY sort_order ASC, name ASC',
        (term, term, term)
    ).fetchall()
    # Buscar nomes das capas para produtos que têm parent_id
    parent_ids = set(p['parent_id'] for p in results if p['parent_id'] is not None)
    parents = {}
    if parent_ids:
        for pid in parent_ids:
            row = conn.execute('SELECT id, name FROM products WHERE id = ?', (pid,)).fetchone()
            if row: parents[pid] = row['name']
    result_ids = [p['id'] for p in results]
    stock_map = _get_stock_map(conn, result_ids)
    whatsapp_contact = _get_whatsapp_from_config(conn)
    conn.close()
    return render_template('busca.html', q=q, results=results, parents=parents,
                          stock_map=stock_map, whatsapp_contact=whatsapp_contact)

@public_bp.route('/catalogo/<int:parent_id>')
def catalogo(parent_id):
    page = _safe_page_param()
    per_page = 20
    offset = (page - 1) * per_page

    conn = get_db_connection()
    parent = conn.execute('SELECT * FROM products WHERE id = ?', (parent_id,)).fetchone()
    if not parent:
        conn.close()
        return redirect(url_for('public.index'))
    total = conn.execute('SELECT COUNT(*) FROM products WHERE parent_id = ?', (parent_id,)).fetchone()[0]
    children = conn.execute(
        'SELECT * FROM products WHERE parent_id = ? ORDER BY sort_order ASC, id ASC LIMIT ? OFFSET ?',
        (parent_id, per_page, offset)
    ).fetchall()
    child_ids = [p['id'] for p in children]
    stock_map = _get_stock_map(conn, child_ids)
    whatsapp_contact = _get_whatsapp_from_config(conn)
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    
    # Agrupar produtos por categoria
    products_by_category = {}
    for product in children:
        product_dict = dict(product)
        category = product_dict.get('category', 'Sem categoria') or 'Sem categoria'
        if category not in products_by_category:
            products_by_category[category] = []
        products_by_category[category].append(product)
    
    conn.close()
    return render_template('catalogo.html', parent=parent, products=children,
                          products_by_category=products_by_category,
                          stock_map=stock_map, whatsapp_contact=whatsapp_contact,
                          page=page, total_pages=total_pages, total=total)

@public_bp.route('/links')
def links():
    page = _safe_page_param()
    per_page = 20
    offset = (page - 1) * per_page

    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM links').fetchone()[0]
    links_data = conn.execute(
        'SELECT * FROM links ORDER BY created_at DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    conn.close()
    return render_template('links.html', links=links_data, products=products,
                          page=page, total_pages=total_pages, total=total)

@public_bp.route('/pagamento')
def pagamento():
    conn = get_db_connection()
    try:
        config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
    except Exception:
        config = None

    pix_key = ''
    pix_copia_cola = ''
    if config:
        pix_key = (config['pix_key'] or '') if 'pix_key' in config.keys() else ''
        pix_copia_cola = (config['pix_copia_cola'] or '').strip() if 'pix_copia_cola' in config.keys() and (config['pix_copia_cola'] or '').strip() else ''
    pix_qr_data = {'pix_key': pix_key, 'pix_copia_cola': pix_copia_cola}

    produto_nome = request.args.get('produto')
    product_data = None
    product_stock = 0
    if produto_nome:
        product_data = conn.execute('SELECT * FROM products WHERE name = ?', (produto_nome,)).fetchone()
        if product_data:
            row = conn.execute('SELECT COUNT(*) as total FROM product_keys WHERE product_id = ? AND is_used = 0', (product_data['id'],)).fetchone()
            product_stock = row['total'] if row else 0
    whatsapp_contact = _get_whatsapp_from_config(conn)
    conn.close()
    return render_template('pagamento.html', product=product_data, config=config, pix_qr_data=pix_qr_data,
                          product_stock=product_stock, whatsapp_contact=whatsapp_contact)

@public_bp.route('/seguranca')
def seguranca():
    return render_template('seguranca.html')

@public_bp.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    return send_from_directory(uploads_dir, filename)