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
    supplier = request.args.get('supplier', '').strip()

    conn = get_db_connection()
    
    # Busca lista de fornecedores ativos gerais
    suppliers_query = conn.execute('''
        SELECT DISTINCT p.supplier 
        FROM products p 
        WHERE p.is_active = 1 AND p.supplier IS NOT NULL AND p.supplier != ""
    ''').fetchall()
    suppliers = sorted(list(set(row['supplier'] for row in suppliers_query)))

    if supplier:
        query_total = '''
            SELECT COUNT(DISTINCT p.id) 
            FROM products p
            LEFT JOIN products child ON child.parent_id = p.id
            WHERE p.parent_id IS NULL AND p.is_active = 1
              AND (
                p.supplier = ? 
                OR (p.is_catalog = 1 AND child.supplier = ? AND child.is_active = 1)
              )
        '''
        total = conn.execute(query_total, (supplier, supplier)).fetchone()[0]
        
        query_products = '''
            SELECT DISTINCT p.* 
            FROM products p
            LEFT JOIN products child ON child.parent_id = p.id
            WHERE p.parent_id IS NULL AND p.is_active = 1
              AND (
                p.supplier = ? 
                OR (p.is_catalog = 1 AND child.supplier = ? AND child.is_active = 1)
              )
            ORDER BY p.sort_order ASC, p.id ASC LIMIT ? OFFSET ?
        '''
        products = conn.execute(query_products, (supplier, supplier, per_page, offset)).fetchall()
    else:
        total = conn.execute('SELECT COUNT(*) FROM products WHERE parent_id IS NULL AND is_active = 1').fetchone()[0]
        products = conn.execute(
            'SELECT * FROM products WHERE parent_id IS NULL AND is_active = 1 ORDER BY sort_order ASC, id ASC LIMIT ? OFFSET ?',
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

    # Buscar feedbacks aprovados para exibir na home
    try:
        feedbacks = conn.execute('''
            SELECT f.*, p.name as product_name 
            FROM feedbacks f 
            LEFT JOIN products p ON f.product_id = p.id 
            WHERE f.status = 'approved' 
            ORDER BY f.created_at DESC LIMIT 10
        ''').fetchall()
    except Exception:
        feedbacks = []

    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    conn.close()
    return render_template('index.html', products=products, catalog_ids=catalog_ids,
                          stock_map=stock_map, whatsapp_contact=whatsapp_contact,
                          page=page, total_pages=total_pages, total=total,
                          suppliers=suppliers, supplier=supplier, feedbacks=feedbacks)


@public_bp.route('/busca')
def busca():
    q = (request.args.get('q') or '').strip()
    if not q:
        return redirect(url_for('public.index'))
    term = f'%{q}%'
    conn = get_db_connection()
    results = conn.execute(
        'SELECT * FROM products WHERE (name LIKE ? OR description LIKE ? OR category LIKE ?) AND is_active = 1 ORDER BY sort_order ASC, name ASC',
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
    supplier = request.args.get('supplier', '').strip()

    conn = get_db_connection()
    parent = conn.execute('SELECT * FROM products WHERE id = ?', (parent_id,)).fetchone()
    if not parent:
        conn.close()
        return redirect(url_for('public.index'))

    # Busca fornecedores ativos deste catálogo específico
    suppliers_query = conn.execute('''
        SELECT DISTINCT supplier 
        FROM products 
        WHERE parent_id = ? AND is_active = 1 AND supplier IS NOT NULL AND supplier != ""
    ''', (parent_id,)).fetchall()
    suppliers = sorted(list(set(row['supplier'] for row in suppliers_query)))

    if supplier:
        total = conn.execute('SELECT COUNT(*) FROM products WHERE parent_id = ? AND is_active = 1 AND supplier = ?', (parent_id, supplier)).fetchone()[0]
        children = conn.execute(
            'SELECT * FROM products WHERE parent_id = ? AND is_active = 1 AND supplier = ? ORDER BY sort_order ASC, id ASC LIMIT ? OFFSET ?',
            (parent_id, supplier, per_page, offset)
        ).fetchall()
    else:
        total = conn.execute('SELECT COUNT(*) FROM products WHERE parent_id = ? AND is_active = 1', (parent_id,)).fetchone()[0]
        children = conn.execute(
            'SELECT * FROM products WHERE parent_id = ? AND is_active = 1 ORDER BY sort_order ASC, id ASC LIMIT ? OFFSET ?',
            (parent_id, per_page, offset)
        ).fetchall()

    catalog_ids = set()
    for p in children:
        is_cat = p['is_catalog'] if 'is_catalog' in p.keys() else 0
        if is_cat == 1: catalog_ids.add(p['id'])
        
    child_ids = [p['id'] for p in children if p['id'] not in catalog_ids]
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
        
    # Ordena categorias pelo menor sort_order de seus produtos
    products_by_category = {k: v for k, v in sorted(
        products_by_category.items(),
        key=lambda item: min(dict(p).get('sort_order', 0) for p in item[1]) if item[1] else 0
    )}
    
    conn.close()
    
    # SEO Variables
    seo_title = f"{parent['name']} - RAIO MODS"
    seo_description = parent['description'] or f"Confira os produtos de {parent['name']} na RAIO MODS."
    seo_image = parent['image'] if parent['image'] else None
    
    return render_template('catalogo.html', parent=parent, products=children,
                          products_by_category=products_by_category,
                          stock_map=stock_map, whatsapp_contact=whatsapp_contact,
                          page=page, total_pages=total_pages, total=total,
                          seo_title=seo_title, seo_description=seo_description, seo_image=seo_image, catalog_ids=catalog_ids,
                          suppliers=suppliers, supplier=supplier)

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

    # Suporta duas formas de link:
    # 1) /pagamento?product_id=123  (recomendado para link direto ao cliente)
    # 2) /pagamento?produto=Nome   (legado, por nome)
    product_data = None
    product_stock = 0

    product_id = request.args.get('product_id', type=int)
    produto_nome = request.args.get('produto')

    if product_id:
        product_data = conn.execute(
            'SELECT * FROM products WHERE id = ? AND is_active = 1',
            (product_id,)
        ).fetchone()
    elif produto_nome:
        product_data = conn.execute(
            'SELECT * FROM products WHERE name = ? AND is_active = 1',
            (produto_nome,)
        ).fetchone()

    if product_data:
        row = conn.execute(
            'SELECT COUNT(*) as total FROM product_keys WHERE product_id = ? AND is_used = 0',
            (product_data['id'],)
        ).fetchone()
        product_stock = row['total'] if row else 0
    whatsapp_contact = _get_whatsapp_from_config(conn)
    whatsapp_contact = _get_whatsapp_from_config(conn)
    conn.close()
    
    # SEO Variables
    seo_title = None
    seo_description = None
    seo_image = None
    
    if product_data:
        seo_title = f"Comprar {product_data['name']} - RAIO MODS"
        seo_description = f"Adquira {product_data['name']} agora! {product_data['description']}"
        seo_image = product_data['image'] if product_data['image'] else None
        
    return render_template('pagamento.html', product=product_data, config=config, pix_qr_data=pix_qr_data,
                          product_stock=product_stock, whatsapp_contact=whatsapp_contact,
                          seo_title=seo_title, seo_description=seo_description, seo_image=seo_image)

@public_bp.route('/pedido/<order_ref>')
def pedido_status(order_ref):
    """Página de status do pedido - destino do redirect após pagamento no Mercado Pago."""
    mp_status = request.args.get('collection_status') or request.args.get('status', '')
    
    conn = get_db_connection()
    whatsapp_contact = _get_whatsapp_from_config(conn)
    
    order = conn.execute('''
        SELECT p.name as product_name
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.external_reference = ?
    ''', (order_ref,)).fetchone()
    
    product_name = order['product_name'] if order else "Produto"
    conn.close()
    
    return render_template('pedido.html', order_ref=order_ref, mp_status=mp_status, 
                           whatsapp_contact=whatsapp_contact, product_name=product_name)

@public_bp.route('/seguranca')
def seguranca():
    return render_template('seguranca.html')

@public_bp.route('/termos')
def termos():
    return render_template('termos.html')

@public_bp.route('/privacidade')
def privacidade():
    return render_template('privacidade.html')

@public_bp.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    return send_from_directory(uploads_dir, filename)

@public_bp.route('/sw.js')
def service_worker():
    response = send_from_directory(os.path.join(current_app.root_path, 'static'), 'sw.js')
    response.headers['Cache-Control'] = 'no-cache'
    return response

@public_bp.route('/manifest.json')
def manifest():
    return send_from_directory(os.path.join(current_app.root_path, 'static'), 'manifest.json')

@public_bp.route('/offline.html')
def offline():
    return render_template('offline.html')


def send_spin_coupon_email(config, to_email, discount_value, coupon_code):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    smtp_server = config.get('smtp_server')
    smtp_port = config.get('smtp_port')
    smtp_user = config.get('smtp_user')
    smtp_password = config.get('smtp_password')

    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        return False, "Serviço SMTP não está totalmente configurado."

    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"Seu cupom de {discount_value}% de desconto chegou! 🎉 - RAIO MODS"
    msg['From'] = f"RAIO MODS <{smtp_user}>"
    msg['To'] = to_email

    html = f"""\
    <html>
      <body style="background-color: #050505; color: #fff; font-family: Arial, sans-serif; padding: 20px;">
        <div style="background-color: #111; border: 1px solid #333; border-radius: 8px; max-width: 600px; margin: 0 auto; padding: 30px; text-align: center;">
            <h1 style="color: #06b6d4; font-size: 28px; margin-bottom: 10px;">RAIO MODS</h1>
            <h2 style="color: #fff; font-size: 20px;">Parabéns! Você ganhou {discount_value}% de desconto!</h2>
            <p style="color: #ccc; font-size: 15px; margin-top: 15px;">
                Use o código abaixo na tela de pagamento da nossa loja para garantir seu desconto.
            </p>
            <div style="margin: 25px 0;">
                <span style="background-color: #06b6d4; color: #000; padding: 12px 25px; border-radius: 6px; font-weight: bold; font-size: 22px; letter-spacing: 2px; display: inline-block;">
                    {coupon_code}
                </span>
            </div>
            <p style="color: #ef4444; font-size: 13px; font-weight: bold; margin-top: 20px;">
                Atenção: Este cupom é de uso único e expira em 24 horas!
            </p>
            <hr style="border-color: #222; margin: 25px 0;">
            <p style="color: #666; font-size: 11px;">
                Se você não solicitou este e-mail no Giro da Sorte da nossa loja, pode desconsiderá-lo com segurança.
            </p>
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
        return True, "E-mail de desconto enviado com sucesso."
    except Exception as e:
        return False, str(e)


@public_bp.route('/api/spin', methods=['POST'])
def lucky_spin():
    import random
    import string
    from datetime import datetime, timedelta
    from flask import jsonify

    data = request.json or {}
    email = data.get('email', '').strip().lower()

    if not email or '@' not in email:
        return jsonify({'error': 'Por favor, insira um e-mail válido.'}), 400

    # Bloqueio de domínios de e-mails temporários/descartáveis comuns
    disposable_domains = {
        'yopmail.com', 'mailinator.com', 'tempmail.com', 'guerrillamail.com', 
        'sharklasers.com', '10minutemail.com', 'temp-mail.org', 'dispostable.com', 
        'getairmail.com', 'throwawaymail.com', 'tempmailaddress.com', 'boun.cr', 
        'tempinbox.com', 'trashmail.com', 'maildrop.cc', 'temp-mail.io', 
        'temp-mail.ru', 'tempmail.net', '10minutemail.net', '10minutemail.co.uk',
        'guerrillamailblock.com', 'guerrillamail.net', 'guerrillamail.org', 
        'guerrillamail.biz', 'grr.la', 'pokemail.net', 'generator.email', 
        'moakt.cc', 'disposable.com', 'crazymailing.com', 'zillamail.com',
        'tempmail.net', 'fakeinbox.com', 'mailnesia.com', 'mailcatch.com'
    }
    email_domain = email.split('@')[-1]
    if email_domain in disposable_domains:
        return jsonify({'error': 'Não é permitido usar e-mails temporários na roleta.'}), 400

    conn = get_db_connection()
    try:
        # 1. Verificar se o SMTP está configurado
        config_row = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
        if not config_row:
            return jsonify({'error': 'Configuração do sistema não localizada.'}), 500
        
        config = dict(config_row)
        if not config.get('smtp_server') or not config.get('smtp_user'):
            return jsonify({'error': 'O envio de e-mails da roleta não está configurado pelo administrador.'}), 500

        # 2. Verificar se o e-mail já realizou um giro nos últimos 30 dias (ignora para e-mail de teste)
        if email != 'luisroyo25@gmail.com':
            row = conn.execute('''
                SELECT 1 FROM lucky_spins 
                WHERE email = ? AND datetime(created_at) > datetime('now', '-30 days')
            ''', (email,)).fetchone()

            if row:
                return jsonify({'error': 'Este e-mail já realizou um giro nos últimos 30 dias.'}), 400

        # Verificar se o cliente possui cadastro para o Clube de Fidelidade
        client_row = conn.execute('SELECT 1 FROM clients WHERE email = ?', (email,)).fetchone()
        client_exists = client_row is not None

        # 3. Sorteio ponderado (Max 15%)
        # Índices: 0 = 5%, 1 = 8%, 2 = 10%, 3 = 12%, 4 = 15%
        options = [
            {"discount": 5, "weight": 45, "index": 0},
            {"discount": 8, "weight": 30, "index": 1},
            {"discount": 10, "weight": 15, "index": 2},
            {"discount": 12, "weight": 8, "index": 3},
            {"discount": 15, "weight": 2, "index": 4}
        ]
        
        choices = []
        for opt in options:
            choices.extend([opt] * opt["weight"])
            
        winner = random.choice(choices)
        discount_val = winner["discount"]
        winner_index = winner["index"]

        # 4. Gerar cupom de uso único no banco
        coupon_code = ""
        while True:
            code_rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            coupon_code = f"RAIOSPIN{discount_val}-{code_rand}"
            dup = conn.execute('SELECT 1 FROM coupons WHERE code = ?', (coupon_code,)).fetchone()
            if not dup:
                break

        valid_until = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

        # 5. Salvar registros no banco (com rollback caso haja falhas)
        conn.execute('''
            INSERT INTO coupons (code, discount_type, discount_value, max_uses, current_uses, valid_until)
            VALUES (?, 'percent', ?, 1, 0, ?)
        ''', (coupon_code, discount_val, valid_until))

        conn.execute('''
            INSERT INTO lucky_spins (email, discount_value, coupon_code)
            VALUES (?, ?, ?)
        ''', (email, discount_val, coupon_code))

        # 6. Enviar o cupom por e-mail
        success, msg = send_spin_coupon_email(config, email, discount_val, coupon_code)
        if not success:
            conn.rollback()
            return jsonify({'error': f'Falha ao enviar e-mail com cupom: {msg}'}), 500

        conn.commit()
        return jsonify({
            'success': True,
            'discount': discount_val,
            'index': winner_index,
            'client_exists': client_exists
        })

    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500
    finally:
        conn.close()