from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from werkzeug.utils import secure_filename
from database.models import get_db_connection
from database.connection import init_db
from utils.image_utils import process_upload_image, get_base_filename
import os
import sqlite3
import time

admin_bp = Blueprint('admin', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@admin_bp.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET' and session.get('admin_logged_in'):
        conn = get_db_connection()
        try:
            # Busca produtos
            all_products = conn.execute('SELECT * FROM products ORDER BY sort_order ASC, id ASC').fetchall()
            all_links = conn.execute('SELECT * FROM links ORDER BY created_at DESC').fetchall()
            config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
            
            # --- CONTAGEM DE ESTOQUE ---
            # Conta quantas chaves livres (is_used=0) cada produto tem
            stock_query = conn.execute('SELECT product_id, COUNT(*) as total FROM product_keys WHERE is_used = 0 GROUP BY product_id').fetchall()
            stock_map = {row['product_id']: row['total'] for row in stock_query}
            
        except sqlite3.OperationalError:
            conn.close()
            init_db()
            return redirect(url_for('admin.admin'))

        # Lógica de Catálogos vs Produtos Simples
        legacy_rows = conn.execute('SELECT parent_id FROM products WHERE parent_id IS NOT NULL').fetchall()
        legacy_catalog_ids = set(r[0] for r in legacy_rows)
        
        catalogs, simple_products, subproducts_by_parent, parent_products = [], [], {}, []
        
        for p in all_products:
            # Adiciona a contagem de estoque ao objeto do produto
            p_dict = dict(p)
            p_dict['stock'] = stock_map.get(p['id'], 0) # Se não tiver chave, é 0
            
            keys = p.keys()
            pid = p['parent_id'] if 'parent_id' in keys else None
            is_cat = p['is_catalog'] if 'is_catalog' in keys else 0

            if pid is None and (is_cat == 1 or p['id'] in legacy_catalog_ids): parent_products.append(p_dict)

            if pid is None:
                if is_cat == 1 or p['id'] in legacy_catalog_ids:
                    catalogs.append(p_dict)
                    if p['id'] not in subproducts_by_parent: subproducts_by_parent[p['id']] = []
                else:
                    simple_products.append(p_dict) 
            else:
                if pid not in subproducts_by_parent: subproducts_by_parent[pid] = []
                subproducts_by_parent[pid].append(p_dict)
        
        stats = {
            'total_products': len(all_products),
            'total_catalogs': len(catalogs),
            'total_links': len(all_links),
            'total_simple': len(simple_products),
        }
        conn.close()
        return render_template('admin.html', catalogs=catalogs, simple_products=simple_products, 
                             subproducts_by_parent=subproducts_by_parent, parent_products=parent_products, 
                             links=all_links, config=config, stats=stats)
    
    if request.method == 'POST':
        if request.form.get('password') == current_app.config['ADMIN_PASSWORD']:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.admin'))
        return render_template('admin_login.html', error='Senha incorreta!')
    return render_template('admin_login.html')

@admin_bp.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.admin'))

# --- ROTAS DE PRODUTOS ---

@admin_bp.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    name = request.form.get('name')
    desc = request.form.get('description')
    price = request.form.get('price')
    cat = request.form.get('category')
    tagline = (request.form.get('tagline') or '').strip()
    payment_url = (request.form.get('payment_url') or '').strip()
    promo_price = (request.form.get('promo_price') or '').strip()
    promo_label = (request.form.get('promo_label') or '').strip()
    
    try: is_catalog = int(request.form.get('is_catalog', 0))
    except: is_catalog = 0
    try: sort_order = int(request.form.get('sort_order') or 0)
    except: sort_order = 0
    
    parent_id = request.form.get('parent_id')
    if not parent_id or str(parent_id).strip() == '':
        parent_id = None
    
    image = request.form.get('image_url', '')
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            base_name = get_base_filename(secure_filename(file.filename))
            uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            img_path, ok = process_upload_image(file.stream, uploads_dir, base_name)
            if ok: image = img_path
            else:
                fname = f"{int(time.time())}_{secure_filename(file.filename)}"
                file.seek(0); file.save(os.path.join(uploads_dir, fname))
                image = f"/static/uploads/{fname}"
    
    if not all([name, desc, price, image, cat]): return jsonify({'error': 'Faltam dados'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO products (name, description, price, image, category, tagline, sort_order, parent_id, is_catalog, payment_url, promo_price, promo_label) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                     (name, desc, price, image, cat, tagline, sort_order, parent_id, is_catalog, payment_url, promo_price, promo_label))
        conn.commit()
    except sqlite3.OperationalError as e:
        conn.close()
        return jsonify({'error': 'Erro no banco de dados: ' + str(e)}), 500
        
    conn.close()
    return jsonify({'success': True, 'message': 'Adicionado!'})

@admin_bp.route('/admin/delete/<int:pid>', methods=['POST'])
def delete_product(pid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    conn = get_db_connection()
    conn.execute('UPDATE products SET parent_id = NULL WHERE parent_id = ?', (pid,))
    conn.execute('DELETE FROM products WHERE id = ?', (pid,)); conn.commit(); conn.close()
    return jsonify({'success': True, 'message': 'Removido!'})

@admin_bp.route('/admin/edit/<int:pid>', methods=['POST'])
def edit_product(pid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM products WHERE id = ?', (pid,)).fetchone()
    if not row: conn.close(); return jsonify({'error': '404'}), 404
    
    existing = dict(row)
    name = request.form.get('name') or existing.get('name', '')
    desc = request.form.get('description') or existing.get('description', '')
    price = request.form.get('price') or existing.get('price', '')
    cat = request.form.get('category') or existing.get('category', '')
    tagline = request.form.get('tagline', existing.get('tagline', '')).strip()
    payment_url = request.form.get('payment_url', existing.get('payment_url', '')).strip()
    promo_price = (request.form.get('promo_price') or existing.get('promo_price') or '').strip()
    promo_label = (request.form.get('promo_label') or existing.get('promo_label') or '').strip()
    
    try: is_catalog = int(request.form.get('is_catalog', existing.get('is_catalog', 0)))
    except: is_catalog = 0
    try: sort = int(request.form.get('sort_order') or existing.get('sort_order', 0))
    except: sort = 0
    
    pid_val = request.form.get('parent_id')
    
    # --- CORREÇÃO DE LÓGICA DO PAI/CATÁLOGO ---
    # Se for marcado como catálogo, NÃO pode ter pai.
    if is_catalog == 1:
        pid_val = None
    # Se o pai for ele mesmo ou string vazia, anula
    elif pid_val == str(pid) or not pid_val or str(pid_val).strip() == '':
        pid_val = None
    
    img = request.form.get('image_url') or ''
    if not img: img = existing.get('image', '')
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            base_name = get_base_filename(secure_filename(file.filename))
            uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            img_path, ok = process_upload_image(file.stream, uploads_dir, base_name)
            if ok: img = img_path
            else:
                fname = f"{int(time.time())}_{secure_filename(file.filename)}"
                file.seek(0); file.save(os.path.join(uploads_dir, fname))
                img = f"/static/uploads/{fname}"

    try:
        conn.execute('UPDATE products SET name=?, description=?, price=?, image=?, category=?, tagline=?, sort_order=?, parent_id=?, is_catalog=?, payment_url=?, promo_price=?, promo_label=? WHERE id=?',
                     (name, desc, price, img, cat, tagline, sort, pid_val, is_catalog, payment_url, promo_price, promo_label, pid))
        conn.commit()
    except sqlite3.OperationalError as e:
        conn.close()
        # Removido o init_db() aqui pois é perigoso durante update
        return jsonify({'error': 'Erro ao atualizar: ' + str(e)}), 500
        
    conn.close()
    return jsonify({'success': True, 'message': 'Atualizado!'})

# --- ROTA DE CONFIGURAÇÃO ---

@admin_bp.route('/admin/config', methods=['POST'])
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
            conn.execute('INSERT INTO config (id, pix_key, pix_copia_cola, contact_whatsapp, mercado_pago_token) VALUES (1, ?, ?, ?, ?)',
                         (pix_key, pix_copia_cola, contact_whatsapp, mercado_pago_token or ''))
        else:
            # Não sobrescrever o token se o campo foi enviado vazio (manter o valor atual)
            if not mercado_pago_token and 'mercado_pago_token' in config.keys():
                mercado_pago_token = config['mercado_pago_token'] or ''
            conn.execute('UPDATE config SET pix_key = ?, pix_copia_cola = ?, contact_whatsapp = ?, mercado_pago_token = ? WHERE id = 1',
                         (pix_key, pix_copia_cola, contact_whatsapp, mercado_pago_token))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500
    conn.close()
    return jsonify({'success': True})

# --- ROTAS DE CHAVES (ESTOQUE) ---

@admin_bp.route('/admin/keys/add', methods=['POST'])
def add_keys():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    product_id = request.form.get('product_id')
    keys_text = request.form.get('keys_list') # Texto com várias chaves
    
    if not product_id or not keys_text:
        return jsonify({'error': 'Dados inválidos'}), 400
        
    # Separa por quebra de linha
    key_list = [k.strip() for k in keys_text.splitlines() if k.strip()]
    
    if not key_list:
        return jsonify({'error': 'Nenhuma chave válida encontrada'}), 400
        
    conn = get_db_connection()
    count = 0
    for key in key_list:
        # Verifica duplicidade simples antes de inserir
        exists = conn.execute('SELECT id FROM product_keys WHERE key_value = ?', (key,)).fetchone()
        if not exists:
            conn.execute('INSERT INTO product_keys (product_id, key_value, is_used) VALUES (?, ?, 0)', (product_id, key))
            count += 1
            
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': f'{count} chaves adicionadas com sucesso!'})

# --- ROTAS DE LINKS ---

@admin_bp.route('/admin/links/add', methods=['POST'])
def add_link():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    title = (request.form.get('title') or '').strip()
    description = (request.form.get('description') or '').strip()
    download_link = (request.form.get('download_link') or '').strip()
    video_link = (request.form.get('video_link') or '').strip()
    game = (request.form.get('game') or '').strip()
    image_url = (request.form.get('image_url') or '').strip()
    
    if not title: return jsonify({'error': 'Título obrigatório'}), 400
    if not download_link and not video_link: return jsonify({'error': 'Pelo menos um link necessário'}), 400
    
    image = image_url
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            base_name = get_base_filename(secure_filename(file.filename))
            uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            img_path, ok = process_upload_image(file.stream, uploads_dir, base_name)
            if ok: image = img_path
            else:
                fname = f"{int(time.time())}_{secure_filename(file.filename)}"
                file.seek(0); file.save(os.path.join(uploads_dir, fname))
                image = f"/static/uploads/{fname}"
    
    conn = get_db_connection()
    conn.execute('INSERT INTO links (title, description, image, download_link, video_link, game) VALUES (?,?,?,?,?,?)',
                 (title, description, image, download_link, video_link, game))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@admin_bp.route('/admin/links/delete/<int:lid>', methods=['POST'])
def delete_link(lid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    conn = get_db_connection(); conn.execute('DELETE FROM links WHERE id = ?', (lid,)); conn.commit(); conn.close()
    return jsonify({'success': True})

@admin_bp.route('/admin/links/edit/<int:lid>', methods=['POST'])
def edit_link(lid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM links WHERE id = ?', (lid,)).fetchone()
    if not existing: conn.close(); return jsonify({'error': '404'}), 404
    
    existing = dict(existing)
    title = (request.form.get('title') or existing.get('title', '')).strip()
    description = (request.form.get('description') or '').strip()
    download_link = (request.form.get('download_link') or '').strip()
    video_link = (request.form.get('video_link') or '').strip()
    game = (request.form.get('game') or '').strip()
    image_url = (request.form.get('image_url') or '').strip()
    
    if not download_link and not video_link: conn.close(); return jsonify({'error': 'Pelo menos um link'}), 400
    
    image = existing.get('image')
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            base_name = get_base_filename(secure_filename(file.filename))
            uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            img_path, ok = process_upload_image(file.stream, uploads_dir, base_name)
            if ok: image = img_path
            else:
                fname = f"{int(time.time())}_{secure_filename(file.filename)}"
                file.seek(0); file.save(os.path.join(uploads_dir, fname))
                image = f"/static/uploads/{fname}"
    elif image_url: image = image_url
    
    conn.execute('UPDATE links SET title=?, description=?, image=?, download_link=?, video_link=?, game=? WHERE id=?',
                 (title, description, image, download_link, video_link, game, lid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

# --- ROTAS DE GERENCIAMENTO DE CHAVES ---

@admin_bp.route('/admin/keys/list/<int:product_id>', methods=['GET'])
def list_keys(product_id):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    # Pega chaves não usadas primeiro, depois as usadas
    keys = conn.execute('SELECT * FROM product_keys WHERE product_id = ? ORDER BY is_used ASC, id DESC', (product_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(k) for k in keys])

@admin_bp.route('/admin/keys/delete/<int:key_id>', methods=['POST'])
def delete_key(key_id):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    conn.execute('DELETE FROM product_keys WHERE id = ?', (key_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})