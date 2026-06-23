from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database.models import get_db_connection
import hashlib
import uuid

reseller_bp = Blueprint('reseller', __name__)

@reseller_bp.route('/revendedor', methods=['GET'])
def index():
    if session.get('reseller_logged_in'):
        return redirect(url_for('reseller.dashboard'))
    return redirect(url_for('reseller.login'))

@reseller_bp.route('/revendedor/login', methods=['GET', 'POST'])
def login():
    if session.get('reseller_logged_in'):
        return redirect(url_for('reseller.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        
        conn = get_db_connection()
        try:
            client = conn.execute('SELECT * FROM clients WHERE email = ? AND is_reseller = 1', (email,)).fetchone()
            if client:
                # Verificando a senha. Importando werkzeug caso seja usado
                try:
                    from werkzeug.security import check_password_hash
                    # Tenta check_password_hash primeiro
                    valid = check_password_hash(client['password_hash'], password)
                except:
                    valid = False
                    
                if not valid:
                    # Fallback para SHA256 (que usamos no cadastro manual)
                    if client['password_hash'] == hashlib.sha256(password.encode()).hexdigest():
                        valid = True
                
                if valid:
                    session['reseller_logged_in'] = True
                    session['reseller_id'] = client['id']
                    session['reseller_name'] = client['name']
                    return redirect(url_for('reseller.dashboard'))
                    
            error = "E-mail ou senha inválidos, ou você não tem permissão de revendedor."
            return render_template('reseller/login.html', error=error)
        except Exception as e:
            return render_template('reseller/login.html', error=f"Erro interno: {e}")
        finally:
            conn.close()
            
    return render_template('reseller/login.html')

@reseller_bp.route('/revendedor/logout', methods=['GET'])
def logout():
    session.pop('reseller_logged_in', None)
    session.pop('reseller_id', None)
    session.pop('reseller_name', None)
    return redirect(url_for('reseller.login'))

@reseller_bp.route('/revendedor/dashboard', methods=['GET'])
def dashboard():
    if not session.get('reseller_logged_in'):
        return redirect(url_for('reseller.login'))
        
    reseller_id = session.get('reseller_id')
    conn = get_db_connection()
    try:
        # Pega o saldo
        client = conn.execute('SELECT wallet_balance, name FROM clients WHERE id = ?', (reseller_id,)).fetchone()
        balance = client['wallet_balance'] or 0.0
        
        # Pega os produtos disponiveis
        # Conta chaves em estoque para cada produto e traz o reseller_price
        products = conn.execute('''
            SELECT p.id, p.name, p.image, p.category, p.reseller_price, COUNT(k.id) as stock
            FROM products p
            LEFT JOIN product_keys k ON k.product_id = p.id AND k.is_used = 0
            WHERE p.is_active = 1 AND p.is_catalog = 0
            GROUP BY p.id
        ''').fetchall()
        
        # Pega o historico
        history = conn.execute('SELECT * FROM reseller_transactions WHERE client_id = ? ORDER BY created_at DESC LIMIT 10', (reseller_id,)).fetchall()
        
        return render_template('reseller/dashboard.html', 
                               balance=balance, 
                               name=client['name'],
                               products=[dict(p) for p in products],
                               history=[dict(h) for h in history])
    except Exception as e:
        return f"Erro: {e}", 500
    finally:
        conn.close()

@reseller_bp.route('/revendedor/api/redeem', methods=['POST'])
def redeem():
    if not session.get('reseller_logged_in'):
        return jsonify({'error': 'Não logado'}), 401
        
    reseller_id = session.get('reseller_id')
    data = request.json or {}
    product_id = data.get('product_id')
    
    if not product_id:
        return jsonify({'error': 'Produto inválido'}), 400
        
    conn = get_db_connection()
    try:
        # Iniciar transacao
        conn.execute('BEGIN TRANSACTION')
        
        # Pega preco do produto e estoque
        product = conn.execute('SELECT name, reseller_price FROM products WHERE id = ?', (product_id,)).fetchone()
        if not product:
            return jsonify({'error': 'Produto não encontrado'}), 404
            
        reseller_price = product['reseller_price']
        if not reseller_price or reseller_price <= 0:
            return jsonify({'error': 'Este produto não está disponível para revenda.'}), 400
            
        # Verifica chave em estoque
        key_row = conn.execute('SELECT id, key_value FROM product_keys WHERE product_id = ? AND is_used = 0 LIMIT 1', (product_id,)).fetchone()
        if not key_row:
            return jsonify({'error': 'Sem estoque para este produto.'}), 400
            
        # Verifica saldo
        client = conn.execute('SELECT wallet_balance FROM clients WHERE id = ?', (reseller_id,)).fetchone()
        balance = client['wallet_balance'] or 0.0
        
        if balance < reseller_price:
            return jsonify({'error': f'Saldo insuficiente. Você tem R$ {balance:.2f} e o produto custa R$ {reseller_price:.2f}.'}), 400
            
        # Processa compra
        new_balance = balance - reseller_price
        conn.execute('UPDATE clients SET wallet_balance = ? WHERE id = ?', (new_balance, reseller_id))
        conn.execute("UPDATE product_keys SET is_used = 1, used_by_email = 'Resgatado por Revendedor' WHERE id = ?", (key_row['id'],))
        
        # Registra no historico do revendedor
        conn.execute(
            'INSERT INTO reseller_transactions (client_id, transaction_type, amount, description) VALUES (?, ?, ?, ?)',
            (reseller_id, 'purchase', reseller_price, f'Resgate: {product["name"]}')
        )
        
        conn.commit()
        return jsonify({
            'success': True,
            'key': key_row['key_value'],
            'new_balance': new_balance,
            'message': 'Chave resgatada com sucesso!'
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
