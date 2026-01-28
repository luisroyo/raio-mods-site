from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import os
import sqlite3
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from database import init_db

# --- Configuração de Ambiente ---
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)

# Configurações
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
app.secret_key = SECRET_KEY
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# Configurações de upload
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    """Conecta ao SQLite local e permite acessar colunas pelo nome"""
    db_path = os.path.join(basedir, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# --- ROTAS PÚBLICAS ---

@app.route('/')
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

@app.route('/catalogo/<int:parent_id>')
def catalogo(parent_id):
    conn = get_db_connection()
    parent = conn.execute('SELECT * FROM products WHERE id = ?', (parent_id,)).fetchone()
    if not parent:
        conn.close(); return redirect(url_for('index'))
    children = conn.execute('SELECT * FROM products WHERE parent_id = ? ORDER BY sort_order ASC, id ASC', (parent_id,)).fetchall()
    conn.close()
    return render_template('catalogo.html', parent=parent, products=children)

@app.route('/links')
def links():
    conn = get_db_connection()
    links = conn.execute('SELECT * FROM links ORDER BY created_at DESC').fetchall()
    products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('links.html', links=links, products=products)

@app.route('/pagamento')
def pagamento():
    conn = get_db_connection()
    # Tenta buscar config, se não existir cria uma dummy para não quebrar
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

@app.route('/seguranca')
def seguranca(): return render_template('seguranca.html')

# --- ADMIN ---

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET' and session.get('admin_logged_in'):
        conn = get_db_connection()
        try:
            all_products = conn.execute('SELECT * FROM products ORDER BY sort_order ASC, id ASC').fetchall()
            all_links = conn.execute('SELECT * FROM links ORDER BY created_at DESC').fetchall()
            config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
        except sqlite3.OperationalError:
            conn.close(); init_db(); return redirect(url_for('admin'))

        legacy_rows = conn.execute('SELECT parent_id FROM products WHERE parent_id IS NOT NULL').fetchall()
        legacy_catalog_ids = set(r[0] for r in legacy_rows)
        
        catalogs, simple_products, subproducts_by_parent, parent_products = [], [], {}, []
        
        for p in all_products:
            keys = p.keys()
            pid = p['parent_id'] if 'parent_id' in keys else None
            is_cat = p['is_catalog'] if 'is_catalog' in keys else 0

            if pid is None and (is_cat == 1 or p['id'] in legacy_catalog_ids): parent_products.append(p)

            if pid is None:
                if is_cat == 1 or p['id'] in legacy_catalog_ids:
                    catalogs.append(p)
                    if p['id'] not in subproducts_by_parent: subproducts_by_parent[p['id']] = []
                else: simple_products.append(p) 
            else:
                if pid not in subproducts_by_parent: subproducts_by_parent[pid] = []
                subproducts_by_parent[pid].append(p)
        
        conn.close()
        return render_template('admin.html', catalogs=catalogs, simple_products=simple_products, 
                             subproducts_by_parent=subproducts_by_parent, parent_products=parent_products, 
                             links=all_links, config=config)
    
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        return render_template('admin_login.html', error='Senha incorreta!')
    return render_template('admin_login.html')

@app.route('/admin/config/update', methods=['POST'])
def update_config():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    pix = request.form.get('pix_key')
    binance = request.form.get('binance_wallet')
    whatsapp = request.form.get('whatsapp_number')
    
    conn = get_db_connection()
    conn.execute('UPDATE config SET pix_key=?, binance_wallet=?, whatsapp_number=? WHERE id=1', (pix, binance, whatsapp))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Configurações salvas!'})

@app.route('/admin/logout')
def admin_logout(): session.pop('admin_logged_in', None); return redirect(url_for('admin'))

@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    name = request.form.get('name')
    desc = request.form.get('description')
    price = request.form.get('price')
    cat = request.form.get('category')
    tagline = (request.form.get('tagline') or '').strip()
    payment_url = (request.form.get('payment_url') or '').strip()
    try: is_catalog = int(request.form.get('is_catalog', 0))
    except: is_catalog = 0
    try: sort_order = int(request.form.get('sort_order') or 0)
    except: sort_order = 0
    parent_id = request.form.get('parent_id') or None
    if parent_id and str(parent_id).strip() == '': parent_id = None
    else:
        try: parent_id = int(parent_id) if parent_id else None
        except: parent_id = None
            
    image = request.form.get('image_url', '')
    
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            fname = secure_filename(file.filename)
            import time
            fname = f"{int(time.time())}_{fname}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            image = f"/static/uploads/{fname}"
    
    if not all([name, desc, price, image, cat]): return jsonify({'error': 'Faltam dados'}), 400
    
    conn = get_db_connection()
    conn.execute('INSERT INTO products (name, description, price, image, category, tagline, sort_order, parent_id, is_catalog, payment_url) VALUES (?,?,?,?,?,?,?,?,?,?)',
                 (name, desc, price, image, cat, tagline, sort_order, parent_id, is_catalog, payment_url))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'message': 'Adicionado!'})

@app.route('/admin/delete/<int:pid>', methods=['POST'])
def delete_product(pid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    conn = get_db_connection()
    p = conn.execute('SELECT image FROM products WHERE id = ?', (pid,)).fetchone()
    if p and p['image'] and '/static/uploads/' in p['image']:
        try: os.remove(p['image'].lstrip('/'))
        except: pass
    conn.execute('UPDATE products SET parent_id = NULL WHERE parent_id = ?', (pid,))
    conn.execute('DELETE FROM products WHERE id = ?', (pid,)); conn.commit(); conn.close()
    return jsonify({'success': True, 'message': 'Removido!'})

@app.route('/admin/edit/<int:pid>', methods=['POST'])
def edit_product(pid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM products WHERE id = ?', (pid,)).fetchone()
    if not row: conn.close(); return jsonify({'error': '404'}), 404
    
    # --- CORREÇÃO: Converter Row para Dict para usar .get() com segurança ---
    existing = dict(row) 
    
    name = request.form.get('name') or existing.get('name', '')
    desc = request.form.get('description') or existing.get('description', '')
    price = request.form.get('price') or existing.get('price', '')
    cat = request.form.get('category') or existing.get('category', '')
    tagline = request.form.get('tagline', existing.get('tagline', '')).strip()
    payment_url = request.form.get('payment_url', existing.get('payment_url', '')).strip()
    
    is_catalog = existing.get('is_catalog', 0)
    if 'is_catalog' in request.form:
        try: is_catalog = int(request.form.get('is_catalog'))
        except: pass

    try: sort = int(request.form.get('sort_order') or existing.get('sort_order', 0))
    except: sort = 0
        
    pid_val = request.form.get('parent_id')
    if pid_val == str(pid) or not pid_val or pid_val == '': pid_val = None
    
    img = request.form.get('image_url') or ''
    if not img: img = existing.get('image', '')
    
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            fname = secure_filename(file.filename)
            import time
            fname = f"{int(time.time())}_{fname}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            img = f"/static/uploads/{fname}"

    conn.execute('UPDATE products SET name=?, description=?, price=?, image=?, category=?, tagline=?, sort_order=?, parent_id=?, is_catalog=?, payment_url=? WHERE id=?',
                 (name, desc, price, img, cat, tagline, sort, pid_val, is_catalog, payment_url, pid))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'message': 'Atualizado!'})

# --- CRUD LINKS ---
@app.route('/admin/links/add', methods=['POST'])
def add_link():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    conn = get_db_connection()
    conn.execute('INSERT INTO links (title, description, download_link, video_link, game) VALUES (?,?,?,?,?)',
                 (request.form.get('title'), request.form.get('description'), request.form.get('download_link'), request.form.get('video_link'), request.form.get('game')))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/links/delete/<int:lid>', methods=['POST'])
def delete_link(lid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    conn = get_db_connection(); conn.execute('DELETE FROM links WHERE id = ?', (lid,)); conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/links/edit/<int:lid>', methods=['POST'])
def edit_link(lid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    conn = get_db_connection()
    conn.execute('UPDATE links SET title=?, description=?, download_link=?, video_link=?, game=? WHERE id=?',
                 (request.form.get('title'), request.form.get('description'), request.form.get('download_link'), request.form.get('video_link'), request.form.get('game'), lid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/static/uploads/<filename>')
def uploaded_file(filename): return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)