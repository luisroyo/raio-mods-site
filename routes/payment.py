import mercadopago
from flask import Blueprint, request, jsonify, current_app, url_for
from database.models import get_db_connection
import json
import uuid
from datetime import datetime

payment_bp = Blueprint('payment', __name__)


def _get_client_ip():
    """Captura o IP real do cliente, considerando proxies (PythonAnywhere, Render, etc)."""
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'

def get_mp_sdk():
    conn = get_db_connection()
    config = conn.execute('SELECT mercado_pago_token FROM config WHERE id = 1').fetchone()
    conn.close()
    token = config['mercado_pago_token'] if config and 'mercado_pago_token' in config.keys() else None
    if not token: return None
    return mercadopago.SDK(token)

@payment_bp.route('/api/checkout', methods=['POST'])
def create_payment():
    try:
        data = request.json
        product_id = data.get('product_id')
        email = data.get('email')
        payment_type = data.get('type', 'pix') # 'pix' ou 'card'
        customer_name = (data.get('name') or '').strip()
        customer_cpf = (data.get('cpf') or '').strip().replace('.', '').replace('-', '')
        customer_phone = (data.get('phone') or '').strip()
        terms_accepted = data.get('terms_accepted', False)
        
        if not product_id or not email:
            return jsonify({'error': 'Dados incompletos'}), 400

        if not customer_name or not customer_cpf or not terms_accepted:
            return jsonify({'error': 'Preencha todos os campos obrigatórios e aceite os termos.'}), 400

        # Captura IP do comprador
        client_ip = _get_client_ip()
        terms_ts = datetime.utcnow().isoformat() if terms_accepted else None

        conn = get_db_connection()
        
        # Verifica Estoque
        key_check = conn.execute('SELECT id FROM product_keys WHERE product_id = ? AND is_used = 0 LIMIT 1', (product_id,)).fetchone()
        if not key_check:
            conn.close()
            return jsonify({'error': 'Produto esgotado! Contate o suporte.'}), 409

        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        conn.close()
        
        if not product:
            return jsonify({'error': 'Produto não encontrado'}), 404

        sdk = get_mp_sdk()
        if not sdk:
            return jsonify({'error': 'Configuração de pagamento (Mercado Pago) ausente ou inválida.'}), 500

        # Preço: usa promo_price se houver promoção, senão price
        product_dict = dict(product)
        price_str = (product_dict.get('promo_price') or product_dict.get('price') or product_dict.get('price')) or ''
        try:
            base_price = float(str(price_str).lower().replace('r$', '').replace(',', '.').strip())
        except:
            base_price = 1.00

        # Gera ID único do pedido
        order_ref = f"ORD-{uuid.uuid4().hex[:12]}"
        
        # Dados do pagador para enviar ao Mercado Pago (melhora score anti-fraude)
        first_name = customer_name.split()[0] if customer_name else email.split('@')[0]
        last_name = ' '.join(customer_name.split()[1:]) if len(customer_name.split()) > 1 else ''

        # --- PIX (PREÇO ORIGINAL) ---
        if payment_type == 'pix':
            payment_data = {
                "transaction_amount": base_price,
                "description": f"{product['name']} (Key)",
                "payment_method_id": "pix",
                "external_reference": order_ref,
                "payer": {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "identification": {
                        "type": "CPF",
                        "number": customer_cpf
                    }
                },
                "notification_url": "https://raiomodsgames.pythonanywhere.com/webhook/mp"
            }
            if customer_phone:
                payment_data["payer"]["phone"] = {"number": customer_phone}

            try:
                mp_res = sdk.payment().create(payment_data)
                payment = mp_res["response"]
                
                if 'error' in payment:
                     return jsonify({'error': f"Erro MP: {payment.get('message', 'Erro desconhecido')}"}), 400

                qr_code = payment['point_of_interaction']['transaction_data']['qr_code']
                qr_base64 = payment['point_of_interaction']['transaction_data']['qr_code_base64']
                
                # Salva Pedido (Preço Base + dados anti-chargeback)
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO orders (external_reference, product_id, customer_email, amount, status, qr_code, qr_code_base64,
                                        customer_name, customer_cpf, customer_phone, ip_purchase, terms_accepted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (order_ref, product_id, email, base_price, 'pending', qr_code, qr_base64,
                      customer_name, customer_cpf, customer_phone, client_ip, terms_ts))
                conn.commit(); conn.close()

                return jsonify({
                    'success': True, 'type': 'pix',
                    'qr_code': qr_code, 'qr_code_base64': qr_base64, 'order_ref': order_ref
                })

            except Exception as e:
                import traceback
                print(traceback.format_exc())
                return jsonify({'error': f'Erro na criação do Pix: {str(e)}'}), 500

        # --- CARTÃO (PREÇO + 7%) ---
        else:
            # APLICA A TAXA DE 7%
            card_price = base_price * 1.07
            card_price = round(card_price, 2) # Arredonda (ex: 30.00 -> 32.10)

            payer_info = {
                "email": email,
                "name": first_name,
                "surname": last_name,
                "identification": {
                    "type": "CPF",
                    "number": customer_cpf
                }
            }
            if customer_phone:
                payer_info["phone"] = {"area_code": "", "number": customer_phone}

            preference_data = {
                "items": [
                    {
                        "title": f"Key: {product['name']} (+Taxa Cartão)",
                        "quantity": 1,
                        "currency_id": "BRL",
                        "unit_price": card_price # USA O PREÇO COM ACRESCIMO
                    }
                ],
                "payer": payer_info,
                "external_reference": order_ref,
                "back_urls": {
                    "success": "https://raiomodsgames.pythonanywhere.com",
                    "failure": "https://raiomodsgames.pythonanywhere.com",
                    "pending": "https://raiomodsgames.pythonanywhere.com"
                },
                "auto_return": "approved",
                "notification_url": "https://raiomodsgames.pythonanywhere.com/webhook/mp"
            }

            try:
                pref_res = sdk.preference().create(preference_data)
                preference = pref_res["response"]
                checkout_url = preference["init_point"]

                # Salva Pedido (Preço Com Acréscimo + dados anti-chargeback)
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO orders (external_reference, product_id, customer_email, amount, status,
                                        customer_name, customer_cpf, customer_phone, ip_purchase, terms_accepted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (order_ref, product_id, email, card_price, 'pending',
                      customer_name, customer_cpf, customer_phone, client_ip, terms_ts))
                conn.commit(); conn.close()

                return jsonify({
                    'success': True, 'type': 'card',
                    'checkout_url': checkout_url, 'order_ref': order_ref
                })
                
            except Exception as e:
                return jsonify({'error': f'Erro Link: {str(e)}'}), 500
                
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        print(f"ERRO CRITICO CHECKOUT: {trace}") # Log no servidor
        return jsonify({'error': 'Erro interno ao processar pagamento. Contate o suporte.'}), 500


@payment_bp.route('/webhook/mp', methods=['POST'])
def webhook():
    import logging
    # Configura um logger específico para pagamentos
    logger = logging.getLogger('payment_webhook')
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    try:
        topic = request.args.get('topic') or request.args.get('type')
        p_id = request.args.get('id') or request.args.get('data.id')
        
        # Log da entrada do webhook
        logger.info(f"Webhook recebido: topic={topic}, id={p_id}")

        if topic == 'payment' and p_id:
            sdk = get_mp_sdk()
            if not sdk:
                logger.error("Erro: SDK Mercado Pago não configurado.")
                return jsonify({'status': 'error_config'}), 500
            
            try:
                payment_info = sdk.payment().get(p_id)
                payment = payment_info['response']
                
                # Verifica se houve erro na resposta do MP
                if 'error' in payment or 'status' not in payment:
                    logger.error(f"Erro ao buscar pagamento {p_id}: {payment}")
                    return jsonify({'status': 'error_mp'}), 400

                status = payment['status']
                order_ref = payment.get('external_reference')
                logger.info(f"Processando pagamento {p_id}: Status={status}, OrderRef={order_ref}")
                
                if status == 'approved' and order_ref:
                    conn = get_db_connection()
                    order = conn.execute('SELECT * FROM orders WHERE external_reference = ?', (order_ref,)).fetchone()
                    
                    if not order:
                        logger.warning(f"Pedido não encontrado para OrderRef: {order_ref}")
                        conn.close()
                        return jsonify({'status': 'order_not_found'}), 404

                    if order['status'] != 'approved':
                        logger.info(f"Atualizando pedido {order['id']} (Status atual: {order['status']})")
                        
                        # Tenta encontrar uma chave disponível
                        key = conn.execute('SELECT * FROM product_keys WHERE product_id = ? AND is_used = 0 LIMIT 1', (order['product_id'],)).fetchone()
                        
                        if key:
                            logger.info(f"Chave encontrada: ID {key['id']}")
                            conn.execute('UPDATE product_keys SET is_used = 1 WHERE id = ?', (key['id'],))
                            conn.execute('UPDATE orders SET status = "approved", key_assigned_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (key['id'], order['id']))
                            conn.commit()
                            logger.info(f"Pedido {order['id']} aprovado com chave {key['id']}")
                        else:
                            # ERRO CRÍTICO: SEM ESTOQUE
                            logger.critical(f"SEM ESTOQUE para o produto {order['product_id']} no pedido {order['id']}!")
                            # Marca como pago_sem_chave para auditoria
                            conn.execute('UPDATE orders SET status = "paid_no_key", updated_at = CURRENT_TIMESTAMP WHERE id = ?', (order['id'],))
                            conn.commit()
                    else:
                        logger.info(f"Pedido {order['id']} já estava aprovado.")
                    
                    conn.close()
                else:
                    logger.info(f"Pagamento {p_id} ignorado (Status: {status}, Ref: {order_ref})")

            except Exception as e:
                import traceback
                logger.error(f"Exceção no processamento do pagamento {p_id}: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({'status': 'error_processing'}), 500

    except Exception as e:
        import traceback
        print(f"ERRO GERAL WEBHOOK: {traceback.format_exc()}")
        return jsonify({'status': 'error_general'}), 500

    return jsonify({'status': 'ok'}), 200

@payment_bp.route('/api/check_status/<order_ref>', methods=['GET'])
def check_status(order_ref):
    conn = get_db_connection()
    order = conn.execute('SELECT o.*, k.key_value FROM orders o LEFT JOIN product_keys k ON o.key_assigned_id = k.id WHERE o.external_reference = ?', (order_ref,)).fetchone()
    if not order:
        conn.close()
        return jsonify({'status': 'not_found'})
    if order['status'] == 'approved' and order['key_value']:
        # Registra IP e momento da entrega da chave (prova de entrega)
        if not order['delivered_at']:
            delivery_ip = _get_client_ip()
            now = datetime.utcnow().isoformat()
            try:
                conn.execute('UPDATE orders SET delivered_at = ?, ip_delivery = ? WHERE id = ?',
                             (now, delivery_ip, order['id']))
                conn.commit()
            except Exception as e:
                print(f"Erro ao registrar entrega: {e}")
        conn.close()
        return jsonify({'status': 'approved', 'key': order['key_value']})
    conn.close()
    return jsonify({'status': order['status']})