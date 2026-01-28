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
    # Só itens principais (sem pai), ordenados pela ordem de exibição
    products = conn.execute(
        'SELECT * FROM products WHERE parent_id IS NULL ORDER BY sort_order ASC, id ASC'
    ).fetchall()
    
    # --- LÓGICA DE CAPA DE JOGO ---
    catalog_ids = set()
    for p in products:
        # Verifica se tem a flag is_catalog=1 (Novo) ou se já tem filhos (Legado)
        is_cat = p['is_catalog'] if 'is_catalog' in p.keys() else 0
        if is_cat == 1:
            catalog_ids.add(p['id'])
            
    # Compatibilidade: adiciona itens que já têm filhos
    legacy = conn.execute('SELECT parent_id FROM products WHERE parent_id IS NOT NULL').fetchall()
    for r in legacy:
        catalog_ids.add(r[0])
    
    conn.close()
    return render_template('index.html', products=products, catalog_ids=catalog_ids)


@app.route('/catalogo/<int:parent_id>')
@app.route('/catalogo/<int:parent_id>/')
def catalogo(parent_id):
    conn = get_db_connection()
    parent = conn.execute('SELECT * FROM products WHERE id = ?', (parent_id,)).fetchone()
    if not parent:
        conn.close()
        return redirect(url_for('index'))
    children = conn.execute(
        'SELECT * FROM products WHERE parent_id = ? ORDER BY sort_order ASC, id ASC',
        (parent_id,)
    ).fetchall()
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
    return render_template('pagamento.html')

@app.route('/seguranca')
def seguranca():
    return render_template('seguranca.html')

# --- ÁREA ADMINISTRATIVA ---

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET' and session.get('admin_logged_in'):
        conn = get_db_connection()
        
        try:
            all_products = conn.execute('SELECT * FROM products ORDER BY sort_order ASC, id ASC').fetchall()
            all_links = conn.execute('SELECT * FROM links ORDER BY created_at DESC').fetchall()
        except sqlite3.OperationalError:
            conn.close()
            init_db() 
            return redirect(url_for('admin'))

        legacy_rows = conn.execute('SELECT parent_id FROM products WHERE parent_id IS NOT NULL').fetchall()
        legacy_catalog_ids = set(r[0] for r in legacy_rows)
        
        catalogs = []
        simple_products = []
        subproducts_by_parent = {}
        parent_products = [] 
        
        for product in all_products:
            keys = product.keys()
            pid = product['parent_id'] if 'parent_id' in keys else None
            is_cat = product['is_catalog'] if 'is_catalog' in keys else 0

            if pid is None and (is_cat == 1 or product['id'] in legacy_catalog_ids):
                parent_products.append(product)

            if pid is None:
                if is_cat == 1 or product['id'] in legacy_catalog_ids:
                    catalogs.append(product) 
                    if product['id'] not in subproducts_by_parent:
                        subproducts_by_parent[product['id']] = []
                else:
                    simple_products.append(product) 
            else:
                if pid not in subproducts_by_parent:
                    subproducts_by_parent[pid] = []
                subproducts_by_parent[pid].append(product)
        
        conn.close()
        return render_template('admin.html', 
                             catalogs=catalogs,
                             simple_products=simple_products,
                             subproducts_by_parent=subproducts_by_parent,
                             parent_products=parent_products,
                             links=all_links)
    
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', error='Senha incorreta!')
    
    return render_template('admin_login.html')

@app.route('/admin/links')
def admin_links_legacy():
    return redirect(url_for('admin'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin'))

# --- ROTAS DE PRODUTOS (CRUD) ---

@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    category = request.form.get('category')
    tagline = (request.form.get('tagline') or '').strip()
    
    try: is_catalog = int(request.form.get('is_catalog', 0))
    except: is_catalog = 0

    try: sort_order = int(request.form.get('sort_order') or 0)
    except ValueError: sort_order = 0
        
    parent_id = request.form.get('parent_id') or None
    if parent_id is not None and str(parent_id).strip() == '':
        parent_id = None
    else:
        try: parent_id = int(parent_id) if parent_id else None
        except: parent_id = None
            
    image_url = request.form.get('image_url', '')
    image = image_url
    
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            import time
            timestamp = int(time.time())
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # --- CORREÇÃO AQUI: Adicionado a barra / no início ---
            image = f"/static/uploads/{filename}"
    
    if not all([name, description, price, image, category]):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO products (name, description, price, image, category, tagline, sort_order, parent_id, is_catalog) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (name, description, price, image, category, tagline, sort_order, parent_id, is_catalog)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Item adicionado!'})

@app.route('/admin/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    conn = get_db_connection()
    product = conn.execute('SELECT image FROM products WHERE id = ?', (product_id,)).fetchone()
    
    # Tenta limpar imagem (opcional)
    if product and isinstance(product['image'], str) and '/static/uploads/' in product['image']:
        try:
            # Remove a barra inicial para achar o arquivo no sistema
            clean_path = product['image'].lstrip('/')
            if os.path.exists(clean_path):
                os.remove(clean_path)
        except:
            pass
    
    conn.execute('UPDATE products SET parent_id = NULL WHERE parent_id = ?', (product_id,))
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Removido com sucesso!'})

@app.route('/admin/edit/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401

    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    
    if not existing:
        conn.close()
        return jsonify({'error': 'Produto não encontrado'}), 404

    name = (request.form.get('name') or existing['name']).strip()
    description = (request.form.get('description') or existing['description']).strip()
    price = (request.form.get('price') or existing['price']).strip()
    category = (request.form.get('category') or existing['category']).strip()
    tagline = (request.form.get('tagline') or (existing['tagline'] if 'tagline' in existing.keys() else '') or '').strip()
    
    is_catalog = existing['is_catalog'] if 'is_catalog' in existing.keys() else 0
    if 'is_catalog' in request.form:
        try: is_catalog = int(request.form.get('is_catalog'))
        except: pass

    try: sort_order = int(request.form.get('sort_order') or (existing['sort_order'] if 'sort_order' in existing.keys() else 0))
    except: sort_order = 0
        
    raw_parent = request.form.get('parent_id')
    parent_id = None
    if raw_parent and str(raw_parent).strip() != '':
        try:
            parent_id = int(raw_parent)
            if parent_id == product_id: parent_id = None
        except: parent_id = None
            
    image_url = (request.form.get('image_url') or '').strip()
    new_image = existing['image']
    uploaded_path = None
    
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            import time
            timestamp = int(time.time())
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # --- CORREÇÃO AQUI TAMBÉM ---
            uploaded_path = f"/static/uploads/{filename}"

    if uploaded_path:
        new_image = uploaded_path
    elif image_url:
        new_image = image_url

    conn.execute(
        'UPDATE products SET name=?, description=?, price=?, image=?, category=?, tagline=?, sort_order=?, parent_id=?, is_catalog=? WHERE id=?',
        (name, description, price, new_image, category, tagline, sort_order, parent_id, is_catalog, product_id)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Atualizado com sucesso!'})

# --- ROTAS DE LINKS ---

@app.route('/admin/links/add', methods=['POST'])
def add_link():
    if not session.get('admin_logged_in'): return jsonify({'error': 'Não autorizado'}), 401
    conn = get_db_connection()
    conn.execute('INSERT INTO links (title, description, download_link, video_link, game) VALUES (?, ?, ?, ?, ?)',
                 (request.form.get('title'), request.form.get('description'), request.form.get('download_link'), request.form.get('video_link'), request.form.get('game')))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Link adicionado!'})

@app.route('/admin/links/delete/<int:link_id>', methods=['POST'])
def delete_link(link_id):
    if not session.get('admin_logged_in'): return jsonify({'error': 'Não autorizado'}), 401
    conn = get_db_connection()
    conn.execute('DELETE FROM links WHERE id = ?', (link_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Link removido!'})

@app.route('/admin/links/edit/<int:link_id>', methods=['POST'])
def edit_link(link_id):
    if not session.get('admin_logged_in'): return jsonify({'error': 'Não autorizado'}), 401
    conn = get_db_connection()
    conn.execute('UPDATE links SET title=?, description=?, download_link=?, video_link=?, game=? WHERE id=?',
                 (request.form.get('title'), request.form.get('description'), request.form.get('download_link'), request.form.get('video_link'), request.form.get('game'), link_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Link atualizado!'})

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)