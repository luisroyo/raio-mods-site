from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from database import init_db

load_dotenv()

app = Flask(__name__)

# Configuração via Variáveis de Ambiente (mais profissional/seguro)
# Windows (PowerShell):
#   setx ADMIN_PASSWORD "sua_senha_forte"
#   setx SECRET_KEY "uma_secret_key_longa"
#   setx DATABASE_PATH "C:\caminho\para\database.db"
#
# Linux/macOS:
#   export ADMIN_PASSWORD="sua_senha_forte"
#   export SECRET_KEY="uma_secret_key_longa"
#   export DATABASE_PATH="/caminho/para/database.db"

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY não configurada. Defina no .env.")
app.secret_key = SECRET_KEY

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não configurada. Defina no .env (Neon PostgreSQL).")

# Configurações de upload
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Criar pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    """Conecta ao banco de dados"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@app.route('/')
def index():
    """Rota principal - lista todos os produtos"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM products ORDER BY id DESC')
            products = cursor.fetchall()
    finally:
        conn.close()
    return render_template('index.html', products=products)

@app.route('/pagamento')
def pagamento():
    """Página de métodos de pagamento"""
    return render_template('pagamento.html')

@app.route('/seguranca')
def seguranca():
    """Página de dicas de segurança"""
    return render_template('seguranca.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Rota de administração - protegida por senha"""
    # Verificar se já está logado
    if request.method == 'GET' and session.get('admin_logged_in'):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM products ORDER BY id DESC')
                products = cursor.fetchall()
        finally:
            conn.close()
        return render_template('admin.html', products=products)
    
    # Processar login
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', error='Senha incorreta!')
    
    # Mostrar página de login
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Logout do admin"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin'))

@app.route('/admin/add', methods=['POST'])
def add_product():
    """Adiciona um novo produto"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    category = request.form.get('category')
    image_url = request.form.get('image_url', '')  # URL alternativa
    
    # Processar upload de imagem
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Adicionar timestamp para evitar conflitos
            import time
            timestamp = int(time.time())
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_filename = f"static/uploads/{filename}"
    
    # Usar URL se não houver upload, ou usar arquivo enviado
    image = image_filename if image_filename else image_url
    
    if not all([name, description, price, image, category]):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO products (name, description, price, image, category) VALUES (%s, %s, %s, %s, %s)',
                (name, description, price, image, category),
            )
        conn.commit()
    finally:
        conn.close()
    
    return jsonify({'success': True, 'message': 'Produto adicionado com sucesso!'})

@app.route('/admin/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    """Remove um produto"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT image FROM products WHERE id = %s', (product_id,))
            product = cursor.fetchone()
    
        # Deletar arquivo de imagem se existir e for local
        if product and isinstance(product.get('image'), str) and product['image'].startswith('static/uploads/'):
            image_path = product['image']
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except:
                    pass  # Ignora erro se arquivo não existir
    
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
        conn.commit()
    finally:
        conn.close()
    
    return jsonify({'success': True, 'message': 'Produto removido com sucesso!'})

@app.route('/admin/edit/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    """Edita um produto existente"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
            existing = cursor.fetchone()
        if not existing:
            return jsonify({'error': 'Produto não encontrado'}), 404

        name = (request.form.get('name') or existing['name']).strip()
        description = (request.form.get('description') or existing['description']).strip()
        price = (request.form.get('price') or existing['price']).strip()
        category = (request.form.get('category') or existing['category']).strip()
        image_url = (request.form.get('image_url') or '').strip()

        # Imagem: por padrão, mantém a atual
        new_image = existing['image']

        # Upload de nova imagem (opcional)
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

        if not all([name, description, price, category, new_image]):
            return jsonify({'error': 'Nome, descrição, preço, categoria e imagem são obrigatórios'}), 400

        # Se a imagem mudou e a antiga era local, remove arquivo antigo
        old_image = existing['image']
        if new_image != old_image and isinstance(old_image, str) and old_image.startswith('static/uploads/'):
            if os.path.exists(old_image):
                try:
                    os.remove(old_image)
                except:
                    pass

        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE products SET name = %s, description = %s, price = %s, image = %s, category = %s WHERE id = %s',
                (name, description, price, new_image, category, product_id),
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'message': 'Produto atualizado com sucesso!'})

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    """Serve arquivos de upload"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Inicializar banco (idempotente)
    init_db()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
