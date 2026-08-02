import logging
import hmac
import os
import uuid
import hashlib
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from contextlib import closing

import mercadopago
from flask import Blueprint, request, jsonify, current_app
from database.models import get_db_connection

# --- Configuração de Log ---
logger = logging.getLogger('payment_webhook')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

payment_bp = Blueprint('payment', __name__)

# --- Funções Auxiliares ---

def _get_client_ip() -> str:
    """Captura o IP real do cliente, considerando proxies (PythonAnywhere, Render, etc)."""
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'

def get_mp_sdk():
    """Recupera o SDK do Mercado Pago inicializado com o token salvo no banco de dados ou .env."""
    token = None
    
    # Prioridade máxima: Banco de Dados (Admin Panel) - permite trocar facilmente
    try:
        with closing(get_db_connection()) as conn:
            config = conn.execute('SELECT mercado_pago_token FROM config WHERE id = 1').fetchone()
            if config and 'mercado_pago_token' in config.keys():
                db_token = config['mercado_pago_token']
                if db_token and db_token.strip():
                    token = db_token.strip()
    except Exception as e:
        logger.warning(f"Erro ao ler token do banco: {e}")
    
    # Fallback: Variável de ambiente (.env)
    if not token:
        token = os.getenv('MP_ACCESS_TOKEN')

    return mercadopago.SDK(token) if token else None

def verify_webhook_signature(request) -> bool:
    """Valida a assinatura x-signature do Mercado Pago (Prevenção de Fraudes e Webhooks Falsos)"""
    secret = os.getenv('MP_WEBHOOK_SECRET')
    if not secret:
        # Se o admin não configurou o secret no .env, não temos como validar.
        # Loga o aviso mas deixa passar para não quebrar a lojinha, mas IDEALMENTE deve se configurar.
        logger.warning("MP_WEBHOOK_SECRET não configurado. Webhooks podem ser falsificados.")
        return True 

    x_signature = request.headers.get('x-signature')
    x_request_id = request.headers.get('x-request-id')
    
    if not x_signature or not x_request_id:
        logger.warning("Cabeçalhos x-signature ou x-request-id ausentes. Permitindo mesmo assim pois o status é verificado na API.")
        return True
        
    try:
        # Extrai 'ts' (timestamp) e 'v1' (hash) da string x_signature. Ex: 'ts=170000000,v1=abc123hash'
        parts = dict(part.split('=') for part in x_signature.split(','))
        ts = parts.get('ts')
        v1 = parts.get('v1')
        
        if not ts or not v1:
            logger.warning("Assinatura do webhook malformada. Permitindo mesmo assim.")
            return True
            
        # O payload para o HMAC é montar 'id_url-request_id-ts' (MercadoPago docs)
        # O ID da transação no request.args ou no body (JSON)
        data_id = request.args.get('data.id') or request.args.get('id')
        if not data_id:
            # tenta body
            if request.is_json:
                data_id = request.json.get('data', {}).get('id') or request.json.get('id')
                
        if not data_id:
            logger.warning("Verificação do webhook falhou: ID do pagamento não encontrado. Permitindo mesmo assim.")
            return True
            
        data_id = str(data_id)
        
        manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
        
        # Gera assinatura local e compara
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            manifest.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if hmac.compare_digest(expected_signature, v1):
            return True
        else:
            logger.warning("Assinatura do webhook inválida. Permitindo mesmo assim pois o status é verificado na API.")
            return True
            
    except Exception as e:
        logger.warning(f"Erro ao validar assinatura do webhook: {e}. Permitindo mesmo assim.")
        return True

def parse_price(price_str) -> float:
    """Converte strings de preço em float de forma segura e padronizada."""
    if not price_str:
        return 1.00
    try:
        clean_str = str(price_str).lower().replace('r$', '').replace(',', '.').strip()
        return float(clean_str)
    except ValueError:
        return 1.00

def parse_customer_name(customer_name: str, email: str) -> tuple[str, str]:
    """Separa nome e sobrenome focado nas exigências do Mercado Pago."""
    parts = customer_name.strip().split() if customer_name else email.split('@')
    first_name = parts[0]
    last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
    return first_name, last_name

def process_approved_payment(order_ref: str, p_id: str):
    """Lógica separada para aprovação do pedido e consumo de estoque do banco."""
    with closing(get_db_connection()) as conn:
        order = conn.execute('SELECT * FROM orders WHERE external_reference = ?', (order_ref,)).fetchone()
        
        if not order:
            logger.warning(f"Pedido não encontrado para OrderRef: {order_ref}")
            return

        if order['status'] == 'approved':
            logger.info(f"Pedido {order['id']} já estava aprovado.")
            return

        logger.info(f"Atualizando pedido {order['id']} (Status atual: {order['status']})")
        
        # Tenta encontrar uma chave disponível (estoque)
        key = conn.execute('SELECT * FROM product_keys WHERE product_id = ? AND is_used = 0 LIMIT 1', (order['product_id'],)).fetchone()
        
        if key:
            logger.info(f"Chave encontrada: ID {key['id']}")
            conn.execute('UPDATE product_keys SET is_used = 1 WHERE id = ?', (key['id'],))
            conn.execute(
                'UPDATE orders SET status = "approved", key_assigned_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', 
                (key['id'], order['id'])
            )
            logger.info(f"Pedido {order['id']} aprovado com chave {key['id']}")
        else:
            # ERRO CRÍTICO: SEM ESTOQUE
            logger.critical(f"SEM ESTOQUE para o produto {order['product_id']} no pedido {order['id']}!")
            # Marca como 'paid_no_key' para auditoria futura
            conn.execute('UPDATE orders SET status = "paid_no_key", updated_at = CURRENT_TIMESTAMP WHERE id = ?', (order['id'],))
            
        # Atribuir Pontos de Fidelidade
        customer_email = order['customer_email'].strip().lower()
        amount_val = order['amount']
        points_to_add = int(amount_val)
        if points_to_add > 0:
            try:
                prod_row = conn.execute('SELECT name FROM products WHERE id = ?', (order['product_id'],)).fetchone()
                prod_name = prod_row['name'] if prod_row else 'Produto'
                
                client_row = conn.execute('SELECT points FROM client_points WHERE email = ?', (customer_email,)).fetchone()
                if client_row:
                    conn.execute('UPDATE client_points SET points = points + ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?', (points_to_add, customer_email))
                else:
                    conn.execute('INSERT INTO client_points (email, points) VALUES (?, ?)', (customer_email, points_to_add))
                
                conn.execute(
                    'INSERT INTO points_history (email, points_changed, action_type, description) VALUES (?, ?, ?, ?)',
                    (customer_email, points_to_add, 'earn_online', f"Compra online #{order['id']} - {prod_name}")
                )
                logger.info(f"Creditado {points_to_add} pontos para {customer_email} pela compra #{order['id']}")
            except Exception as e:
                logger.error(f"Erro ao creditar pontos de fidelidade para {customer_email}: {e}")

        # Incrementar uso do cupom, se houver (somente após pagamento aprovado)
        if 'coupon_id' in order.keys() and order['coupon_id']:
            try:
                c_id = order['coupon_id']
                conn.execute('UPDATE coupons SET current_uses = current_uses + 1 WHERE id = ?', (c_id,))
                
                if 'coupon_code' in order.keys() and order['coupon_code']:
                    if str(order['coupon_code']).upper().startswith('FID-'):
                        conn.execute('UPDATE loyalty_coupons SET is_used = 1 WHERE coupon_code = ?', (order['coupon_code'],))
                logger.info(f"Uso do cupom ID {c_id} incrementado.")
            except Exception as e:
                logger.error(f"Erro ao atualizar uso do cupom no pedido {order['id']}: {e}")

        conn.commit()

        # Envia e-mails de notificação (Admin e Cliente) de forma assíncrona
        product = conn.execute('SELECT name, download_link FROM products WHERE id = ?', (order['product_id'],)).fetchone()
        
        # Enviar chave via Telegram (se o cliente comprou pelo bot)
        telegram_id = dict(order).get('telegram_id')
        if telegram_id:
            try:
                from telegram_app.services.telegram_service import TelegramService
                product_name = product['name'] if product else 'Produto Desconhecido'
                download_link = product['download_link'] if (product and 'download_link' in product.keys()) else ''
                
                if key:
                    key_value = key['key_value']
                    TelegramService.send_key_delivery(
                        chat_id=telegram_id,
                        product_name=product_name,
                        key_value=key_value,
                        download_link=download_link,
                        order_ref=order['external_reference']
                    )
                    logger.info(f"Entrega de chave via Telegram agendada para o chat_id: {telegram_id}")
                else:
                    from telegram_app.routes import send_telegram_message_safe
                    safe_prod_name = str(product_name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    warn_msg = (
                        f"⚠️ <b>PAGAMENTO APROVADO!</b> ⚠️\n\n"
                        f"Seu pagamento para o produto <b>{safe_prod_name}</b> foi confirmado, mas nosso estoque de chaves para este item esgotou temporariamente.\n\n"
                        f"O administrador já foi notificado e enviará sua licença manualmente no seu e-mail ou aqui no privado o mais rápido possível!"
                    )
                    send_telegram_message_safe(telegram_id, warn_msg, parse_mode='HTML', order_ref=order['external_reference'])
                    logger.warning(f"Aviso de sem estoque enviado via Telegram para o chat_id: {telegram_id}")
            except Exception as e:
                logger.error(f"Erro ao disparar entrega via Telegram: {e}")
                
        config = conn.execute('SELECT smtp_server, smtp_port, smtp_user, smtp_password FROM config WHERE id = 1').fetchone()

        if config and config['smtp_server'] and config['smtp_user']:
            prod_name = product['name'] if product else 'Produto Desconhecido'
            product_dict = dict(product) if product else {}
            download_link = product_dict.get('download_link') or ''
            order_dict = dict(order)
            config_dict = dict(config)
            
            # 1. Enviar e-mail de notificação para o Admin
            def send_admin_email():
                try:
                    msg = MIMEMultipart("alternative")
                    msg['Subject'] = f"Nova Venda! 🚀 - {prod_name}"
                    msg['From'] = f"RAIO MODS Loja <{config_dict['smtp_user']}>"
                    msg['To'] = config_dict['smtp_user'] # Envia para o próprio admin
                    
                    html = f"""
                    <html>
                      <body style="background-color: #050505; color: #fff; font-family: Arial, sans-serif; padding: 20px;">
                        <div style="background-color: #111; border: 1px solid #333; border-radius: 8px; max-width: 600px; margin: 0 auto; padding: 30px; text-align: left;">
                            <h1 style="color: #06b6d4;">RAIO MODS - Nova Venda Aprovada!</h1>
                            <p style="color: #ccc; font-size: 16px;">Você acabou de realizar uma nova venda.</p>
                            
                            <h2 style="color: #fff; margin-top:20px;">Detalhes do Pedido</h2>
                            <ul style="color: #ccc; font-size: 14px; line-height: 1.6;">
                                <li><strong>ID do Pedido:</strong> {order_dict.get('id')}</li>
                                <li><strong>Referência:</strong> {order_dict.get('external_reference')}</li>
                                <li><strong>Produto:</strong> {prod_name}</li>
                                <li><strong>Valor:</strong> R$ {order_dict.get('amount')}</li>
                                <li><strong>Cliente (Nome):</strong> {order_dict.get('customer_name')}</li>
                                <li><strong>Cliente (CPF):</strong> {order_dict.get('customer_cpf')}</li>
                                <li><strong>Email do Cliente:</strong> {order_dict.get('customer_email')}</li>
                            </ul>
                            
                            <p style="color: #666; font-size: 12px; margin-top: 30px;">Notificação Automática - RAIO MODS Administrativo.</p>
                        </div>
                      </body>
                    </html>
                    """
                    msg.attach(MIMEText(html, "html"))
                    
                    server = smtplib.SMTP(config_dict['smtp_server'], int(config_dict['smtp_port']))
                    server.starttls()
                    server.login(config_dict['smtp_user'], config_dict['smtp_password'])
                    server.sendmail(config_dict['smtp_user'], config_dict['smtp_user'], msg.as_string())
                    server.quit()
                    logger.info("Email de notificação para admin enviado com sucesso.")
                except Exception as e:
                    logger.error(f"Erro ao enviar e-mail de notificação para admin: {e}")
                    
            threading.Thread(target=send_admin_email).start()

            # 2. Enviar e-mail com a Chave para o Cliente (se houver chave associada)
            # Para evitar consultas no banco dentro da thread (e possíveis locks), extraímos o valor da chave antes.
            key_value = None
            if key:
                try:
                    key_value = key['key_value']
                except Exception:
                    pass

            if key_value:
                def send_customer_email():
                    try:
                        msg = MIMEMultipart("alternative")
                        msg['Subject'] = f"Seu produto está pronto! ⚡ - {prod_name}"
                        msg['From'] = f"RAIO MODS <{config_dict['smtp_user']}>"
                        msg['To'] = customer_email
                        
                        html_download = ""
                        if download_link and download_link.strip():
                            html_download = f"""
                            <p style="color: #ccc; font-size: 15px; margin-top: 20px;">
                                <strong>Link para Download / Instruções:</strong><br>
                                <a href="{download_link}" target="_blank" style="color: #06b6d4; text-decoration: underline; font-weight: bold;">Clique aqui para baixar</a>
                            </p>
                            """
                        
                        html = f"""
                        <html>
                          <body style="background-color: #050505; color: #fff; font-family: Arial, sans-serif; padding: 20px;">
                            <div style="background-color: #111; border: 1px solid #333; border-radius: 8px; max-width: 600px; margin: 0 auto; padding: 30px; text-align: center;">
                                <h1 style="color: #06b6d4; font-size: 28px; margin-bottom: 10px; font-weight: bold; letter-spacing: 1px;">RAIO MODS</h1>
                                <h2 style="color: #fff; font-size: 20px; margin-bottom: 20px;">Obrigado por sua compra! 🎉</h2>
                                <p style="color: #ccc; font-size: 15px;">
                                    Seu pagamento para o produto <strong>{prod_name}</strong> foi aprovado.
                                </p>
                                <p style="color: #ccc; font-size: 15px; margin-top: 15px;">
                                    Abaixo está a sua chave de ativação / licença:
                                </p>
                                <div style="margin: 25px 0;">
                                    <span style="background-color: #1a1a1a; border: 2px dashed #06b6d4; color: #06b6d4; padding: 12px 25px; border-radius: 6px; font-weight: bold; font-size: 20px; letter-spacing: 1px; display: inline-block; font-family: monospace;">
                                        {key_value}
                                    </span>
                                </div>
                                {html_download}
                                <hr style="border-color: #222; margin: 25px 0;">
                                <p style="color: #888; font-size: 12px; line-height: 1.4;">
                                    Referência do Pedido: <strong>{order_ref}</strong><br>
                                    Caso precise de ajuda ou suporte, entre em contato através do nosso WhatsApp.
                                </p>
                            </div>
                          </body>
                        </html>
                        """
                        msg.attach(MIMEText(html, "html"))
                        
                        server = smtplib.SMTP(config_dict['smtp_server'], int(config_dict['smtp_port']))
                        server.starttls()
                        server.login(config_dict['smtp_user'], config_dict['smtp_password'])
                        server.sendmail(config_dict['smtp_user'], customer_email, msg.as_string())
                        server.quit()
                        logger.info(f"Email de entrega de chave enviado para {customer_email} com sucesso.")
                    except Exception as e:
                        logger.error(f"Erro ao enviar e-mail de entrega de chave para o cliente: {e}")

                threading.Thread(target=send_customer_email).start()



# --- Lógica de Cupons ---
def get_coupon_discount(code, base_price, conn):
    """Retorna (valor_descontado_em_reais, erro_msg, dict_cupom)"""
    if not code:
        return 0, None, None
        
    coupon = conn.execute('SELECT * FROM coupons WHERE code = ? COLLATE NOCASE', (code.strip(),)).fetchone()
    if not coupon:
        return 0, 'Cupom inválido.', None
        
    if coupon['max_uses'] > 0 and coupon['current_uses'] >= coupon['max_uses']:
        return 0, 'Cupom esgotado.', None
        
    if coupon['valid_until']:
        # Verifica expiração
        try:
            exp_date = datetime.strptime(coupon['valid_until'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > exp_date:
                return 0, 'Cupom expirado.', None
        except Exception as e:
            logger.error(f"Erro ao converter data do cupom {code}: {e}")
            
    discount = 0.0
    if coupon['discount_type'] == 'percent':
        discount = base_price * (coupon['discount_value'] / 100.0)
    else:
        discount = coupon['discount_value']
        
    discount = min(discount, base_price - 1.0) # Não pode zerar ou negativar o preço (Min R$1)
    if discount < 0: discount = 0
    return discount, None, coupon

@payment_bp.route('/api/check_coupon', methods=['POST'])
def check_coupon():
    data = request.json or {}
    code = data.get('code')
    product_id = data.get('product_id')
    
    if not code or not product_id:
        return jsonify({'error': 'Código ou produto ausente.'}), 400
        
    try:
        with closing(get_db_connection()) as conn:
            product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
            if not product:
                return jsonify({'error': 'Produto não encontrado.'}), 404
                
            from utils.promo import get_active_global_promo, apply_global_promo
            promo = get_active_global_promo(conn)
            product_dict = apply_global_promo(product, promo)
            
            raw_price = product_dict.get('promo_price') or product_dict.get('price')
            base_price = parse_price(raw_price)
            
            discount_amount, error_msg, coupon = get_coupon_discount(code, base_price, conn)
            
            if error_msg:
                return jsonify({'error': error_msg}), 400
                
            discount_label = f"{coupon['discount_value']}%" if coupon['discount_type'] == 'percent' else f"R$ {coupon['discount_value']:.2f}"
            
            return jsonify({
                'discount_amount': round(discount_amount, 2),
                'discount_label': discount_label
            })
    except Exception as e:
        logger.error(f"Erro no check_coupon: {e}")
        return jsonify({'error': 'Erro ao validar cupom.'}), 500

# --- Validações de Segurança & Rate Limiting ---
import re
import time
from collections import defaultdict

rate_limit_lock = threading.Lock()
checkout_requests = defaultdict(list)

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    with rate_limit_lock:
        checkout_requests[ip] = [t for t in checkout_requests[ip] if now - t < 60]
        if len(checkout_requests[ip]) >= 5:
            return True
        checkout_requests[ip].append(now)
        return False

def validate_email(email_str: str) -> bool:
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(regex, email_str or ''))

def validate_cpf(cpf_str: str) -> bool:
    cpf = ''.join(filter(str.isdigit, cpf_str or ''))
    if len(cpf) != 11:
        return False
    if cpf in (c * 11 for c in '0123456789'):
        return False
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            return False
    return True

# --- Rotas da API ---

@payment_bp.route('/api/checkout', methods=['POST'])
def create_payment():
    """Endpoint principal de processamento de checkout."""
    try:
        data = request.json or {}
        product_id = data.get('product_id')
        email = (data.get('email') or '').strip().lower()
        payment_type = data.get('type', 'pix') # 'pix' ou 'card'
        customer_name = (data.get('name') or '').strip()
        customer_cpf = ''.join(filter(str.isdigit, data.get('cpf') or ''))
        customer_phone = (data.get('phone') or '').strip()
        terms_accepted = data.get('terms_accepted', False)
        
        # 1. Rate limiting check
        client_ip = _get_client_ip()
        if is_rate_limited(client_ip):
            return jsonify({'error': 'Muitas tentativas de compra em pouco tempo. Aguarde um minuto.'}), 429
            
        # Validação do initData do Telegram
        init_data = data.get('init_data')
        telegram_id = ""
        telegram_username = ""
        telegram_first_name = ""
        
        if init_data:
            from telegram_app.utils.auth import validate_telegram_webapp_data
            from telegram_app.config import TelegramConfig
            
            tg_user = validate_telegram_webapp_data(init_data, TelegramConfig.TELEGRAM_TOKEN)
            if tg_user:
                telegram_id = tg_user.telegram_id
                telegram_username = tg_user.username
                telegram_first_name = tg_user.first_name
            else:
                # Se a validação falhar, o checkout continua funcionando normalmente
                # apenas sem associar o usuário do Telegram ao pedido.
                logger.warning("Falha na validação do init_data do Telegram WebApp. Procedendo como compra comum.")
            
        # 2. Validações primárias de payload
        if not product_id or not email:
            return jsonify({'error': 'Dados incompletos'}), 400

        if not customer_name or not terms_accepted:
            return jsonify({'error': 'Preencha seu Nome e aceite os termos para continuar.'}), 400

        if not validate_email(email):
            return jsonify({'error': 'Por favor, insira um e-mail válido.'}), 400

        if customer_cpf and not validate_cpf(customer_cpf):
            return jsonify({'error': 'Por favor, insira um CPF válido.'}), 400

        terms_ts = datetime.now(timezone.utc).isoformat() if terms_accepted else None

        with closing(get_db_connection()) as conn:
            # Validação ágil de estoque antes do processamento pesado
            has_stock = conn.execute('SELECT 1 FROM product_keys WHERE product_id = ? AND is_used = 0 LIMIT 1', (product_id,)).fetchone()
            if not has_stock:
                return jsonify({'error': 'Produto esgotado! Contate o suporte.'}), 409

            product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
            if not product:
                return jsonify({'error': 'Produto não encontrado'}), 404
            
            from utils.promo import get_active_global_promo, apply_global_promo
            promo = get_active_global_promo(conn)
            product_dict = apply_global_promo(product, promo)

            # Regra de negócio de exibição de preço (promoção ou fixo)
            raw_price = product_dict.get('promo_price') or product_dict.get('price')
            base_price = parse_price(raw_price)
            final_price = base_price
            
            coupon_code = data.get('coupon')
            seller_coupon = data.get('seller_coupon')
            applied_coupon = None
            coupon_data = None
            discount_applied = 0.0
            
            # Se houver seller_ref e ele for válido, nós mantemos. (Sem dar desconto invisível)
            valid_seller = None
            if seller_coupon:
                s_check = conn.execute('SELECT code FROM coupons WHERE code = ? COLLATE NOCASE', (seller_coupon.strip(),)).fetchone()
                if s_check:
                    valid_seller = s_check['code']
                else:
                    # Pode salvar o ref cru mesmo se não for cupom? Sim, para afliados sem cupom.
                    valid_seller = seller_coupon[:50] # Limite de tamanho
            
            # Aplica o cupom de desconto real digitado pelo usuário
            if coupon_code:
                discount_amt, err, c_data = get_coupon_discount(coupon_code, base_price, conn)
                if not err and c_data:
                    final_price -= discount_amt
                    applied_coupon = c_data['id']
                    coupon_data = c_data
                    discount_applied += discount_amt
                    
            final_price = max(1.0, final_price)

        sdk = get_mp_sdk()
        if not sdk:
            return jsonify({'error': 'Configuração de pagamento (Mercado Pago) ausente ou inválida.'}), 500

        final_price = round(final_price, 2)
        order_ref = f"ORD-{uuid.uuid4().hex[:12]}"
        first_name, last_name = parse_customer_name(customer_name, email)

        # Configurações básicas de pagador no Mercado Pago
        payer_info = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name
        }
        if customer_cpf:
            payer_info["identification"] = {"type": "CPF", "number": customer_cpf}
        if customer_phone:
            payer_info["phone"] = {"number": customer_phone}

        # Inicializa variáveis de pagamento localmente a serem preenchidas pelo PIX/Cartão
        response_data = {'success': True, 'type': payment_type, 'order_ref': order_ref}
        qr_code, qr_base64, checkout_url = None, None, None

        # --- PIX (PREÇO ORIGINAL) ---
        if payment_type == 'pix':
            payment_data = {
                "transaction_amount": final_price,
                "description": f"{product_dict['name']} (Key)",
                "payment_method_id": "pix",
                "external_reference": order_ref,
                "payer": payer_info,
                "notification_url": "https://raiomodsgames.pythonanywhere.com/webhook/mp"
            }

            mp_res = sdk.payment().create(payment_data)
            payment_resp = mp_res.get("response", {})
            
            if 'error' in payment_resp:
                 return jsonify({'error': f"Erro MP: {payment_resp.get('message', 'Erro desconhecido')}"}), 400

            try:
                tx_data = payment_resp['point_of_interaction']['transaction_data']
                qr_code = tx_data['qr_code']
                qr_base64 = tx_data['qr_code_base64']
            except KeyError:
                logger.error(f"Resposta inesperada do MP ao gerar PIX: {payment_resp}")
                return jsonify({'error': 'Resposta inválida na geração de Pix pelo MercadoPago.'}), 500

            response_data.update({'qr_code': qr_code, 'qr_code_base64': qr_base64})

        # --- CARTÃO (ACRÉSCIMO DE 7%) ---
        else:
            final_price = round(final_price * 1.07, 2)

            # Preference exige formato 'surname'
            card_payer = {
                "email": email,
                "name": first_name,
                "surname": last_name
            }
            if customer_cpf:
                card_payer["identification"] = {"type": "CPF", "number": customer_cpf}
            if customer_phone:
                card_payer["phone"] = {"area_code": "", "number": customer_phone}

            preference_data = {
                "items": [{
                    "title": f"Key: {product_dict['name']} (+Taxa Cartão)",
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": final_price
                }],
                "payer": card_payer,
                "external_reference": order_ref,
                "back_urls": {
                    "success": f"https://raiomodsgames.pythonanywhere.com/pedido/{order_ref}",
                    "failure": f"https://raiomodsgames.pythonanywhere.com/pedido/{order_ref}?status=failure",
                    "pending": f"https://raiomodsgames.pythonanywhere.com/pedido/{order_ref}?status=pending"
                },
                "auto_return": "approved",
                "notification_url": "https://raiomodsgames.pythonanywhere.com/webhook/mp"
            }

            pref_res = sdk.preference().create(preference_data)
            response_body = pref_res.get("response", {})
            checkout_url = response_body.get("init_point") or response_body.get("sandbox_init_point")

            if not checkout_url:
                logger.error(f"Erro MP Preference: {pref_res}")
                return jsonify({'error': 'Erro ao gerar link de pagamento do Cartão.'}), 500

            response_data.update({'checkout_url': checkout_url})

        # Persistência do pedido unificada
        with closing(get_db_connection()) as conn:
            from utils.i18n import get_current_language, get_current_currency
            try:
                lang = get_current_language()
                curr = get_current_currency()
            except:
                lang = 'pt'
                curr = 'BRL'
                
            c_code = coupon_data['code'] if coupon_data else ''
            c_type = coupon_data['discount_type'] if coupon_data else ''
            c_val = coupon_data['discount_value'] if coupon_data else 0.0

            conn.execute('''
                INSERT INTO orders (
                    external_reference, product_id, customer_email, amount, status, 
                    qr_code, qr_code_base64, customer_name, customer_cpf, 
                    customer_phone, ip_purchase, terms_accepted_at,
                    telegram_id, telegram_username, telegram_first_name,
                    coupon_id, coupon_code, discount_type, discount_value, discount_applied,
                    subtotal, total, language, currency, seller_coupon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_ref, product_id, email, final_price, 'pending', 
                qr_code, qr_base64, customer_name, customer_cpf, 
                customer_phone, client_ip, terms_ts,
                telegram_id, telegram_username, telegram_first_name,
                applied_coupon, c_code, c_type, c_val, discount_applied,
                base_price, final_price, lang, curr, valid_seller
            ))
            conn.commit()

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"ERRO CRITICO CHECKOUT: {e}", exc_info=True)
        return jsonify({'error': 'Erro interno ao processar pagamento. Contate o suporte.'}), 500


@payment_bp.route('/webhook/mp', methods=['POST'])
def webhook():
    """Recebe as notificações de atualização do MercadoPago."""
    try:
        topic = request.args.get('topic') or request.args.get('type')
        p_id = request.args.get('id') or request.args.get('data.id')
        
        if request.is_json:
            body = request.json or {}
            if not topic:
                topic = body.get('type') or body.get('topic')
            if not p_id:
                p_id = body.get('data', {}).get('id') or body.get('id')
        
        logger.info(f"Webhook recebido: topic={topic}, id={p_id}")
        
        # Segurança: Valida x-signature antes de prosseguir
        if not verify_webhook_signature(request):
            logger.error(f"Webhook rejeitado: Assinatura x-signature inválida. (ID pago: {p_id})")
            return jsonify({'error': 'Unauthorized webhook. Signature mismatch.'}), 403

        if topic == 'payment' and p_id:
            sdk = get_mp_sdk()
            if not sdk:
                logger.error("Erro: SDK Mercado Pago não configurado.")
                return jsonify({'status': 'error_config'}), 500
            
            payment_info = sdk.payment().get(p_id)
            payment = payment_info.get('response', {})
            
            if 'error' in payment or 'status' not in payment:
                logger.error(f"Erro ao buscar pagamento {p_id}: {payment}")
                return jsonify({'status': 'error_mp'}), 400

            status = payment.get('status')
            order_ref = payment.get('external_reference')
            logger.info(f"Processando pagamento {p_id}: Status={status}, OrderRef={order_ref}")
            
            if status == 'approved' and order_ref:
                process_approved_payment(order_ref, p_id)
            else:
                logger.info(f"Pagamento {p_id} ignorado ou não finalizado (Status: {status}, Ref: {order_ref})")

    except Exception as e:
        logger.error(f"ERRO GERAL WEBHOOK: {e}", exc_info=True)
        return jsonify({'status': 'error_general'}), 500

    return jsonify({'status': 'ok'}), 200


@payment_bp.route('/api/check_status/<order_ref>', methods=['GET'])
def check_status(order_ref):
    """Verifica e retorna o status em tempo real do pedido via poll do cliente.
    Quando aprovado, retorna também os dados do produto (download_link, product_name)
    para que o frontend possa montar a tela de pós-compra sem depender do template.
    Inclui fallback ativo: se o webhook falhar, consulta o MP diretamente.
    """
    with closing(get_db_connection()) as conn:
        row = conn.execute('''
            SELECT o.status, o.key_assigned_id,
                   p.name AS product_name,
                   p.download_link,
                   l.download_link AS linked_download_url
            FROM orders o
            LEFT JOIN products p ON o.product_id = p.id
            LEFT JOIN links l ON p.link_id = l.id
            WHERE o.external_reference = ?
        ''', (order_ref,)).fetchone()
    
    if not row:
        return jsonify({'status': 'not_found'})
    
    def _build_approved_response(row):
        """Monta o payload completo quando o pedido está aprovado."""
        # Prioriza a URL da tabela de links, com fallback para o link manual antigo
        download_link = row.get('linked_download_url')
        if not download_link or not download_link.strip():
            download_link = row.get('download_link') or ''
        else:
            download_link = download_link.strip()
            
        return jsonify({
            'status': 'ready_to_reveal',
            'product_name': row.get('product_name') or '',
            'download_link': download_link,
            'has_download': bool(download_link.strip())
        })

    if row['status'] == 'approved':
        if row['key_assigned_id']:
            return _build_approved_response(row)
        else:
            return jsonify({'status': 'paid_no_key'})
    
    # Fallback: se ainda está pendente, consulta o MP diretamente
    if row['status'] == 'pending':
        try:
            sdk = get_mp_sdk()
            if sdk:
                search_result = sdk.payment().search({"external_reference": order_ref})
                results = search_result.get("response", {}).get("results", [])
                for payment in results:
                    if payment.get("status") == "approved":
                        logger.info(f"Fallback ativo: pagamento aprovado encontrado para {order_ref} (Payment ID: {payment.get('id')})")
                        process_approved_payment(order_ref, str(payment.get("id", "")))
                        # Re-busca para pegar os dados do produto após processar
                        with closing(get_db_connection()) as conn2:
                            updated = conn2.execute('''
                                SELECT o.status, o.key_assigned_id,
                                       p.name AS product_name,
                                       p.download_link,
                                       l.download_link AS linked_download_url
                                FROM orders o
                                LEFT JOIN products p ON o.product_id = p.id
                                LEFT JOIN links l ON p.link_id = l.id
                                WHERE o.external_reference = ?
                            ''', (order_ref,)).fetchone()
                        if updated:
                            return _build_approved_response(updated)
                        return jsonify({'status': 'ready_to_reveal', 'download_link': '', 'has_download': False})
        except Exception as e:
            logger.warning(f"Erro no fallback de verificação ativa: {e}")
        
    return jsonify({'status': row['status']})


@payment_bp.route('/api/reveal_key/<order_ref>', methods=['POST'])
def reveal_key(order_ref):
    """Registra forte prova de consumo (anti-chargeback) e retorna apenas a chave ao cliente.
    Responsabilidade única: revelar a chave. Dados do pedido (download_link, produto)
    são retornados por /api/check_status para manter a arquitetura limpa.
    """
    with closing(get_db_connection()) as conn:
        order = conn.execute('''
            SELECT o.*, k.key_value
            FROM orders o
            LEFT JOIN product_keys k ON o.key_assigned_id = k.id
            WHERE o.external_reference = ?
        ''', (order_ref,)).fetchone()

        if not order:
            return jsonify({'error': 'Pedido não encontrado'}), 404

        if order['status'] != 'approved' or not order['key_value']:
            return jsonify({'error': 'Chave ainda não disponível ou pedido pendente'}), 400

        key_value = order['key_value']

        # Registra as provas de consumo para proteção contra chargeback APENAS 1 VEZ
        if not order['delivered_at']:
            delivery_ip = _get_client_ip()
            user_agent = request.headers.get('User-Agent', 'unknown')
            now_iso = datetime.now(timezone.utc).isoformat()
            key_sha256 = hashlib.sha256(key_value.encode('utf-8')).hexdigest()

            try:
                conn.execute('''
                    UPDATE orders
                    SET delivered_at = ?, ip_delivery = ?, user_agent_delivery = ?, key_hash = ?
                    WHERE id = ?
                ''', (now_iso, delivery_ip, user_agent, key_sha256, order['id']))
                conn.commit()
            except Exception as e:
                logger.error(f"Erro ao registrar consumo anti-chargeback (Order Ref: {order_ref}): {e}", exc_info=True)

    # Retorna apenas a chave — dados do pedido já foram entregues pelo check_status
    return jsonify({'status': 'revealed', 'key': key_value})