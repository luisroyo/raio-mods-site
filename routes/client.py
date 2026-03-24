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

    return render_template('client/dashboard.html', orders=orders, email=email)

@client_bp.route('/cliente/logout')
def logout():
    session.pop('client_email', None)
    return redirect(url_for('client.login_page'))
