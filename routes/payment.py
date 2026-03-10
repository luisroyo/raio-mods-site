import logging
import hmac
import os
import uuid
import hashlib
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
    # Prioridade máxima: Variável de ambiente (Seguro)
    token = os.getenv('MP_ACCESS_TOKEN')
    
    # Fallback: Banco de Dados SQLite
    if not token:
        with closing(get_db_connection()) as conn:
            config = conn.execute('SELECT mercado_pago_token FROM config WHERE id = 1').fetchone()
            token = config['mercado_pago_token'] if config and 'mercado_pago_token' in config.keys() else None

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
        logger.error("Cabeçalhos de segurança do Mercado Pago ausentes (x-signature / x-request-id)")
        return False
        
    try:
        # Extrai 'ts' (timestamp) e 'v1' (hash) da string x_signature. Ex: 'ts=170000000,v1=abc123hash'
        parts = dict(part.split('=') for part in x_signature.split(','))
        ts = parts.get('ts')
        v1 = parts.get('v1')
        
        if not ts or not v1:
            return False
            
        # O payload para o HMAC é montar 'id_url-request_id-ts' (MercadoPago docs)
        # O ID da transação no request.args ou no body (JSON)
        data_id = request.args.get('data.id') or request.args.get('id')
        if not data_id and request.is_json:
            body = request.json or {}
            data_id = body.get('data', {}).get('id') or body.get('id')
        data_id = str(data_id) if data_id else ''
        
        manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
        
        # Gera assinatura local e compara
        signature = hmac.new(
            secret.encode('utf-8'),
            manifest.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, v1)
            
    except Exception as e:
        logger.error(f"Erro ao validar assinatura x-signature: {e}")
        return False

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
            
        conn.commit()


# --- Rotas da API ---

@payment_bp.route('/api/checkout', methods=['POST'])
def create_payment():
    """Endpoint principal de processamento de checkout."""
    try:
        data = request.json or {}
        product_id = data.get('product_id')
        email = data.get('email')
        payment_type = data.get('type', 'pix') # 'pix' ou 'card'
        customer_name = (data.get('name') or '').strip()
        customer_cpf = (data.get('cpf') or '').strip().translate(str.maketrans('', '', '.-'))
        customer_phone = (data.get('phone') or '').strip()
        terms_accepted = data.get('terms_accepted', False)
        
        # Validações primárias de payload
        if not product_id or not email:
            return jsonify({'error': 'Dados incompletos'}), 400

        if not customer_name or not customer_cpf or not terms_accepted:
            return jsonify({'error': 'Preencha todos os campos obrigatórios e aceite os termos.'}), 400

        client_ip = _get_client_ip()
        terms_ts = datetime.now(timezone.utc).isoformat() if terms_accepted else None

        with closing(get_db_connection()) as conn:
            # Validação ágil de estoque antes do processamento pesado
            has_stock = conn.execute('SELECT 1 FROM product_keys WHERE product_id = ? AND is_used = 0 LIMIT 1', (product_id,)).fetchone()
            if not has_stock:
                return jsonify({'error': 'Produto esgotado! Contate o suporte.'}), 409

            product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
            if not product:
                return jsonify({'error': 'Produto não encontrado'}), 404
            
            product_dict = dict(product)

        sdk = get_mp_sdk()
        if not sdk:
            return jsonify({'error': 'Configuração de pagamento (Mercado Pago) ausente ou inválida.'}), 500

        # Regra de negócio de exibição de preço (promoção ou fixo)
        raw_price = product_dict.get('promo_price') or product_dict.get('price')
        base_price = parse_price(raw_price)

        order_ref = f"ORD-{uuid.uuid4().hex[:12]}"
        first_name, last_name = parse_customer_name(customer_name, email)

        # Configurações básicas de pagador no Mercado Pago
        payer_info = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "identification": {"type": "CPF", "number": customer_cpf}
        }
        if customer_phone:
            payer_info["phone"] = {"number": customer_phone}

        # Inicializa variáveis de pagamento localmente a serem preenchidas pelo PIX/Cartão
        response_data = {'success': True, 'type': payment_type, 'order_ref': order_ref}
        qr_code, qr_base64, checkout_url = None, None, None
        final_price = base_price

        # --- PIX (PREÇO ORIGINAL) ---
        if payment_type == 'pix':
            payment_data = {
                "transaction_amount": base_price,
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
            final_price = round(base_price * 1.07, 2)

            # Preference exige formato 'surname'
            card_payer = {
                "email": email,
                "name": first_name,
                "surname": last_name,
                "identification": {"type": "CPF", "number": customer_cpf}
            }
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
                    "success": "https://raiomodsgames.pythonanywhere.com",
                    "failure": "https://raiomodsgames.pythonanywhere.com",
                    "pending": "https://raiomodsgames.pythonanywhere.com"
                },
                "auto_return": "approved",
                "notification_url": "https://raiomodsgames.pythonanywhere.com/webhook/mp"
            }

            pref_res = sdk.preference().create(preference_data)
            checkout_url = pref_res.get("response", {}).get("init_point")

            if not checkout_url:
                logger.error(f"Erro MP Preference: {pref_res}")
                return jsonify({'error': 'Erro ao gerar link de pagamento do Cartão.'}), 500

            response_data.update({'checkout_url': checkout_url})

        # Persistência do pedido unificada
        with closing(get_db_connection()) as conn:
            conn.execute('''
                INSERT INTO orders (
                    external_reference, product_id, customer_email, amount, status, 
                    qr_code, qr_code_base64, customer_name, customer_cpf, 
                    customer_phone, ip_purchase, terms_accepted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_ref, product_id, email, final_price, 'pending', 
                qr_code, qr_base64, customer_name, customer_cpf, 
                customer_phone, client_ip, terms_ts
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
        
        if not topic and request.is_json:
            body = request.json or {}
            topic = body.get('type') or body.get('topic')
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
    """Verifica e retorna o status em tempo real do pedido via poll do cliente."""
    with closing(get_db_connection()) as conn:
        order = conn.execute('SELECT status, key_assigned_id FROM orders WHERE external_reference = ?', (order_ref,)).fetchone()
    
    if not order:
        return jsonify({'status': 'not_found'})
        
    if order['status'] == 'approved' and order['key_assigned_id']:
        # Sinaliza proatividade sem exibir a chave real ainda
        return jsonify({'status': 'ready_to_reveal'})
        
    return jsonify({'status': order['status']})


@payment_bp.route('/api/reveal_key/<order_ref>', methods=['POST'])
def reveal_key(order_ref):
    """Registra forte prova de consumo (anti-chargeback) e decifra a chave final ao cliente."""
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

    return jsonify({'status': 'revealed', 'key': key_value})