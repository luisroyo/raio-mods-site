from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database.models import get_db_connection
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import random

client_bp = Blueprint('client', __name__)

def send_otp_email(config, to_email, code):
    smtp_server = config['smtp_server']
    smtp_port = config['smtp_port']
    smtp_user = config['smtp_user']
    smtp_password = config['smtp_password']

    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        return False, "SMTP não configurado no painel Admin."

    msg = MIMEMultipart("alternative")
    msg['Subject'] = "Seu código de acesso - RAIO MODS"
    msg['From'] = f"RAIO MODS <{smtp_user}>"
    msg['To'] = to_email

    html = f"""\
    <html>
      <body style="background-color: #050505; color: #fff; font-family: Arial, sans-serif; padding: 20px;">
        <div style="background-color: #111; border: 1px solid #333; border-radius: 8px; max-width: 600px; margin: 0 auto; padding: 30px; text-align: center;">
            <h1 style="color: #06b6d4;">RAIO MODS</h1>
            <h2 style="color: #fff;">Seu Código de Acesso</h2>
            <p style="color: #ccc; font-size: 16px;">
                Use o código abaixo para entrar no Painel do Cliente.
            </p>
            <div style="margin: 30px 0;">
                <span style="background-color: #06b6d4; color: #000; padding: 15px 30px; border-radius: 5px; font-weight: bold; font-size: 24px; letter-spacing: 5px;">
                    {code}
                </span>
            </div>
            <p style="color: #666; font-size: 12px;">Este código expira em 10 minutos. Se você não solicitou, ignore.</p>
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        return True, "Email enviado."
    except Exception as e:
        return False, str(e)

@client_bp.route('/cliente/cadastro')
def cadastro_page():
    if session.get('client_email'):
        return redirect(url_for('client.dashboard_page'))
    return render_template('client/cadastro.html')

@client_bp.route('/api/client/register', methods=['POST'])
def register_client():
    from werkzeug.security import generate_password_hash
    data = request.json or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')

    if not all([name, email, phone, password]):
        return jsonify({'error': 'Todos os campos são obrigatórios.'}), 400

    conn = get_db_connection()
    try:
        # Verifica se e-mail já existe
        existing = conn.execute('SELECT 1 FROM clients WHERE email = ?', (email,)).fetchone()
        if existing:
            return jsonify({'error': 'Este e-mail já está cadastrado.'}), 400

        # Cria usuário
        pwd_hash = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO clients (name, email, phone, password_hash) VALUES (?, ?, ?, ?)',
            (name, email, phone, pwd_hash)
        )
        insert_id = cursor.lastrowid
        
        # Gera o ID Único
        client_id = f"CL{insert_id:06d}"
        cursor.execute('UPDATE clients SET client_id = ? WHERE id = ?', (client_id, insert_id))
        
        # Cria registro de pontos se não existir
        pts_row = conn.execute('SELECT 1 FROM client_points WHERE email = ?', (email,)).fetchone()
        if not pts_row:
            conn.execute('INSERT INTO client_points (email, points) VALUES (?, 0)', (email,))

        conn.commit()

        # Inicia a sessão
        session['client_email'] = email
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Erro ao registrar: {str(e)}'}), 500
    finally:
        conn.close()

@client_bp.route('/api/client/login-password', methods=['POST'])
def login_password():
    from werkzeug.security import check_password_hash
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'E-mail e senha são obrigatórios.'}), 400

    conn = get_db_connection()
    try:
        client = conn.execute('SELECT * FROM clients WHERE email = ?', (email,)).fetchone()
        if not client:
            return jsonify({'error': 'E-mail ou senha incorretos.'}), 400

        if not check_password_hash(client['password_hash'], password):
            return jsonify({'error': 'E-mail ou senha incorretos.'}), 400

        session['client_email'] = email
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f'Erro de login: {str(e)}'}), 500
    finally:
        conn.close()

@client_bp.route('/cliente/login')
def login_page():
    if session.get('client_email'):
        return redirect(url_for('client.dashboard_page'))
    return render_template('client/login.html')

@client_bp.route('/api/client/request-code', methods=['POST'])
def request_code():
    data = request.json
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'E-mail inválido.'}), 400

    conn = get_db_connection()
    config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
    
    # Gera um código numérico de 6 dígitos
    code = f"{random.randint(100000, 999999)}"
    expires_at = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')

    try:
        conn.execute(
            'INSERT INTO otp_codes (email, code, expires_at) VALUES (?, ?, ?)',
            (email, code, expires_at)
        )
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({'error': 'Erro ao gerar código no banco de dados.'}), 500

    success, msg = send_otp_email(config, email, code)
    conn.close()

    if success:
        return jsonify({'success': True, 'message': 'Código enviado para ' + email})
    else:
        return jsonify({'error': 'Erro ao enviar e-mail: ' + msg}), 500

@client_bp.route('/api/client/verify-code', methods=['POST'])
def verify_code():
    data = request.json
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()

    conn = get_db_connection()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    otp = conn.execute(
        '''SELECT * FROM otp_codes 
           WHERE email = ? AND code = ? AND used = 0 AND expires_at > ?
           ORDER BY created_at DESC LIMIT 1''',
        (email, code, now)
    ).fetchone()

    if not otp:
        conn.close()
        return jsonify({'error': 'Código inválido, expirado ou já utilizado.'}), 400

    # Marcar como usado
    conn.execute('UPDATE otp_codes SET used = 1 WHERE id = ?', (otp['id'],))
    conn.commit()
    conn.close()

    session['client_email'] = email
    
    return jsonify({'success': True})

@client_bp.route('/cliente/painel')
def dashboard_page():
    email = session.get('client_email')
    if not email:
        return redirect(url_for('client.login_page'))

    conn = get_db_connection()
    
    # Carrega dados cadastrais do cliente
    client = conn.execute('SELECT * FROM clients WHERE email = ?', (email,)).fetchone()
    
    orders = conn.execute('''
        SELECT o.id, o.external_reference, o.amount, o.status, o.created_at, o.qr_code, o.qr_code_base64,
               p.name as product_name, p.image as product_image,
               k.key_value
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN product_keys k ON o.key_assigned_id = k.id
        WHERE o.customer_email = ?
        ORDER BY o.created_at DESC
    ''', (email,)).fetchall()
    conn.close()

    client_info = {
        'name': client['name'] if client else 'Cliente',
        'client_id': client['client_id'] if client else 'Sem ID (Cadastre-se)',
        'phone': client['phone'] if client else '—'
    }

    return render_template('client/dashboard.html', orders=orders, email=email, client_info=client_info)

@client_bp.route('/api/client/loyalty/redeem-points-coupon', methods=['POST'])
def redeem_points_coupon():
    email = session.get('client_email')
    if not email:
        return jsonify({'error': 'Não autorizado'}), 401

    data = request.json or {}
    coupon_code = data.get('code', '').strip().upper()

    if not coupon_code:
        return jsonify({'error': 'Código do cupom é obrigatório.'}), 400

    conn = get_db_connection()
    try:
        # Buscar cupom de pontos
        coupon = conn.execute('SELECT * FROM points_coupons WHERE code = ?', (coupon_code,)).fetchone()
        if not coupon:
            return jsonify({'error': 'Cupom inválido ou inexistente.'}), 404

        # Validar data
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if coupon['valid_until'] and coupon['valid_until'] < now:
            return jsonify({'error': 'Este cupom já expirou.'}), 400

        # Validar limite global de usos
        if coupon['max_uses_global'] > 0 and coupon['current_uses'] >= coupon['max_uses_global']:
            return jsonify({'error': 'Este cupom atingiu o limite máximo de usos.'}), 400

        # Validar limite de usos por cliente
        redemptions_count = conn.execute(
            'SELECT COUNT(*) FROM points_coupon_redemptions WHERE coupon_id = ? AND client_email = ?',
            (coupon['id'], email)
        ).fetchone()[0]

        if coupon['max_uses_per_client'] > 0 and redemptions_count >= coupon['max_uses_per_client']:
            return jsonify({'error': 'Você já resgatou este cupom.'}), 400

        # Registrar o resgate
        conn.execute(
            'INSERT INTO points_coupon_redemptions (coupon_id, client_email) VALUES (?, ?)',
            (coupon['id'], email)
        )

        # Atualizar usos do cupom
        conn.execute(
            'UPDATE points_coupons SET current_uses = current_uses + 1 WHERE id = ?',
            (coupon['id'],)
        )

        # Atualizar saldo de pontos
        pts_row = conn.execute('SELECT points FROM client_points WHERE email = ?', (email,)).fetchone()
        if pts_row:
            conn.execute(
                'UPDATE client_points SET points = points + ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?',
                (coupon['points_value'], email)
            )
            new_points = pts_row['points'] + coupon['points_value']
        else:
            conn.execute(
                'INSERT INTO client_points (email, points) VALUES (?, ?)',
                (email, coupon['points_value'])
            )
            new_points = coupon['points_value']

        # Registrar histórico de pontos
        conn.execute(
            '''INSERT INTO points_history (email, points_changed, action_type, description)
               VALUES (?, ?, 'admin_adjust', ?)''',
            (email, coupon['points_value'], f"Resgate de Cupom de Pontos: {coupon_code}")
        )

        conn.commit()
        return jsonify({
            'success': True,
            'message': f'Sucesso! Você ganhou {coupon["points_value"]} pontos.',
            'new_points': new_points
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Erro ao resgatar cupom: {str(e)}'}), 500
    finally:
        conn.close()

@client_bp.route('/cliente/logout')
def logout():
    session.pop('client_email', None)
    return redirect(url_for('client.login_page'))

@client_bp.route('/api/client/loyalty/info')
def loyalty_info():
    email = session.get('client_email')
    if not email:
        return jsonify({'error': 'Não autorizado'}), 401
    
    conn = get_db_connection()
    try:
        # Saldo de pontos
        pts_row = conn.execute('SELECT points FROM client_points WHERE email = ?', (email,)).fetchone()
        points = pts_row['points'] if pts_row else 0
        
        # Histórico de pontos
        history = conn.execute('''
            SELECT points_changed, action_type, description, created_at 
            FROM points_history 
            WHERE email = ? 
            ORDER BY created_at DESC LIMIT 15
        ''', (email,)).fetchall()
        
        # Cupons ativos de fidelidade
        coupons = conn.execute('''
            SELECT coupon_code, discount_value, created_at 
            FROM loyalty_coupons 
            WHERE email = ? AND is_used = 0
            ORDER BY created_at DESC
        ''', (email,)).fetchall()
        
        return jsonify({
            'points': points,
            'history': [dict(h) for h in history],
            'coupons': [dict(c) for c in coupons]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@client_bp.route('/api/client/loyalty/redeem', methods=['POST'])
def loyalty_redeem():
    email = session.get('client_email')
    if not email:
        return jsonify({'error': 'Não autorizado'}), 401
        
    data = request.json or {}
    points_required = data.get('points')
    
    # Validações de pontos exigidos
    reward_map = {
        100: 5.0,
        200: 12.0,
        500: 35.0
    }
    
    if points_required not in reward_map:
        return jsonify({'error': 'Opção de resgate inválida.'}), 400
        
    discount_value = reward_map[points_required]
    
    conn = get_db_connection()
    try:
        # Check current points
        pts_row = conn.execute('SELECT points FROM client_points WHERE email = ?', (email,)).fetchone()
        current_points = pts_row['points'] if pts_row else 0
        
        if current_points < points_required:
            return jsonify({'error': 'Pontos insuficientes.'}), 400
            
        # Deduct points
        new_points = current_points - points_required
        conn.execute('UPDATE client_points SET points = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?', (new_points, email))
        
        # Log history
        conn.execute('''
            INSERT INTO points_history (email, points_changed, action_type, description)
            VALUES (?, ?, 'redeem', ?)
        ''', (email, -points_required, f"Resgate de cupom de R$ {discount_value:.2f}"))
        
        # Generate random unique coupon code
        import string
        coupon_code = ""
        while True:
            code_rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            coupon_code = f"FID-{code_rand}"
            # Check uniqueness in coupons
            dup = conn.execute('SELECT 1 FROM coupons WHERE code = ?', (coupon_code,)).fetchone()
            if not dup:
                break
                
        # Insert into coupons (usable in checkout)
        valid_until = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute('''
            INSERT INTO coupons (code, discount_type, discount_value, max_uses, current_uses, valid_until)
            VALUES (?, 'fixed', ?, 1, 0, ?)
        ''', (coupon_code, discount_value, valid_until))
        
        # Insert into loyalty_coupons (tracked for client)
        conn.execute('''
            INSERT INTO loyalty_coupons (email, coupon_code, discount_value, is_used)
            VALUES (?, ?, ?, 0)
        ''', (email, coupon_code, discount_value))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'coupon_code': coupon_code,
            'discount_value': discount_value,
            'new_points': new_points
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
