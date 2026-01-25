from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import os
import sqlite3
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from database import init_db

# --- CORREÇÃO IMPORTANTE: Carregar .env do diretório atual ---
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
# -------------------------------------------------------------

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
    # Usa o caminho absoluto para garantir que ache o banco
    db_path = os.path.join(basedir, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/links')
def links():
    """Página pública de links independentes"""
    conn = get_db_connection()
    # Pega links independentes
    links = conn.execute('SELECT * FROM links ORDER BY created_at DESC').fetchall()
    # Pega produtos que também podem ser úteis
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
        products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
        conn.close()
        return render_template('admin.html', products=products)
    
    if request.method == 'POST':
        password = request.form.get('password')
        # Comparação direta da senha (simples e eficaz para este caso)
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', error='Senha incorreta!')
    
    return render_template('admin_login.html')

@app.route('/admin/links')
def admin_links():
    """Gerenciamento de Links no Admin"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
        
    conn = get_db_connection()
    links = conn.execute('SELECT * FROM links ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin_links.html', links=links)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin'))

# --- ROTAS DE PRODUTOS (ADMIN) ---

@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    category = request.form.get('category')
    tagline = (request.form.get('tagline') or '').strip()
    image_url = request.form.get('image_url', '')
    
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            import time
            timestamp = int(time.time())
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_filename = f"static/uploads/{filename}"
    
    image = image_filename if image_filename else image_url
    
    if not all([name, description, price, image, category]):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO products (name, description, price, image, category, tagline) VALUES (?, ?, ?, ?, ?, ?)',
        (name, description, price, image, category, tagline)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Produto adicionado com sucesso!'})

@app.route('/admin/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    conn = get_db_connection()
    product = conn.execute('SELECT image FROM products WHERE id = ?', (product_id,)).fetchone()
    
    if product and isinstance(product['image'], str) and product['image'].startswith('static/uploads/'):
        image_path = product['image']
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass
    
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Produto removido com sucesso!'})

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
            uploaded_path = f"static/uploads/{filename}"

    if uploaded_path:
        new_image = uploaded_path
    elif image_url:
        new_image = image_url

    conn.execute(
        'UPDATE products SET name = ?, description = ?, price = ?, image = ?, category = ?, tagline = ? WHERE id = ?',
        (name, description, price, new_image, category, tagline, product_id)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Produto atualizado com sucesso!'})

# --- ROTAS DE LINKS (ADMIN) ---

@app.route('/admin/links/add', methods=['POST'])
def add_link():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    title = request.form.get('title')
    description = request.form.get('description')
    download_link = request.form.get('download_link')
    video_link = request.form.get('video_link')
    game = request.form.get('game')
    
    if not title:
        return jsonify({'error': 'O título é obrigatório'}), 400
        
    if not download_link and not video_link:
        return jsonify({'error': 'Adicione pelo menos um link (Download ou Vídeo)'}), 400
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO links (title, description, download_link, video_link, game) VALUES (?, ?, ?, ?, ?)',
        (title, description, download_link, video_link, game)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Link adicionado com sucesso!'})

@app.route('/admin/links/delete/<int:link_id>', methods=['POST'])
def delete_link(link_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    conn = get_db_connection()
    conn.execute('DELETE FROM links WHERE id = ?', (link_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Link removido com sucesso!'})

@app.route('/admin/links/edit/<int:link_id>', methods=['POST'])
def edit_link(link_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
        
    conn = get_db_connection()
    
    title = request.form.get('title')
    description = request.form.get('description')
    download_link = request.form.get('download_link')
    video_link = request.form.get('video_link')
    game = request.form.get('game')
    
    conn.execute(
        'UPDATE links SET title = ?, description = ?, download_link = ?, video_link = ?, game = ? WHERE id = ?',
        (title, description, download_link, video_link, game, link_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Link atualizado com sucesso!'})

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)