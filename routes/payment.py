import mercadopago
from flask import Blueprint, request, jsonify, current_app, url_for
from database.models import get_db_connection
import json
import uuid

payment_bp = Blueprint('payment', __name__)

def get_mp_sdk():
    conn = get_db_connection()
    config = conn.execute('SELECT mercado_pago_token FROM config WHERE id = 1').fetchone()
    conn.close()
    token = config['mercado_pago_token'] if config and 'mercado_pago_token' in config.keys() else None
    if not token: return None
    return mercadopago.SDK(token)

@payment_bp.route('/api/checkout', methods=['POST'])
def create_payment():
    data = request.json
    product_id = data.get('product_id')
    email = data.get('email')
    payment_type = data.get('type', 'pix') # 'pix' ou 'card'
    
    if not product_id or not email:
        return jsonify({'error': 'Dados incompletos'}), 400

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
        return jsonify({'error': 'Configuração de pagamento ausente.'}), 500

    # Limpa o preço base
    try:
        base_price = float(str(product['price']).lower().replace('r$', '').replace(',', '.').strip())
    except:
        base_price = 1.00

    # Gera ID único do pedido
    order_ref = f"ORD-{uuid.uuid4().hex[:12]}"

    # --- PIX (PREÇO ORIGINAL) ---
    if payment_type == 'pix':
        payment_data = {
            "transaction_amount": base_price,
            "description": f"{product['name']} (Key)",
            "payment_method_id": "pix",
            "external_reference": order_ref,
            "payer": {
                "email": email,
                "first_name": email.split('@')[0]
            },
            "notification_url": "https://raiomodsgames.pythonanywhere.com/webhook/mp"
        }

        try:
            mp_res = sdk.payment().create(payment_data)
            payment = mp_res["response"]
            
            if 'error' in payment:
                 return jsonify({'error': 'Erro ao criar Pix.'}), 400

            qr_code = payment['point_of_interaction']['transaction_data']['qr_code']
            qr_base64 = payment['point_of_interaction']['transaction_data']['qr_code_base64']
            
            # Salva Pedido (Preço Base)
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO orders (external_reference, product_id, customer_email, amount, status, qr_code, qr_code_base64)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (order_ref, product_id, email, base_price, 'pending', qr_code, qr_base64))
            conn.commit(); conn.close()

            return jsonify({
                'success': True, 'type': 'pix',
                'qr_code': qr_code, 'qr_code_base64': qr_base64, 'order_ref': order_ref
            })

        except Exception as e:
            return jsonify({'error': f'Erro Pix: {str(e)}'}), 500

    # --- CARTÃO (PREÇO + 7%) ---
    else:
        # APLICA A TAXA DE 7%
        card_price = base_price * 1.07
        card_price = round(card_price, 2) # Arredonda (ex: 30.00 -> 32.10)

        preference_data = {
            "items": [
                {
                    "title": f"Key: {product['name']} (+Taxa Cartão)",
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": card_price # USA O PREÇO COM ACRESCIMO
                }
            ],
            "payer": {"email": email},
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

            # Salva Pedido (Preço Com Acréscimo)
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO orders (external_reference, product_id, customer_email, amount, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_ref, product_id, email, card_price, 'pending'))
            conn.commit(); conn.close()

            return jsonify({
                'success': True, 'type': 'card',
                'checkout_url': checkout_url, 'order_ref': order_ref
            })
            
        except Exception as e:
            return jsonify({'error': f'Erro Link: {str(e)}'}), 500


@payment_bp.route('/webhook/mp', methods=['POST'])
def webhook():
    topic = request.args.get('topic') or request.args.get('type')
    p_id = request.args.get('id') or request.args.get('data.id')

    if topic == 'payment':
        sdk = get_mp_sdk()
        if not sdk: return jsonify({'status': 'error_config'}), 500
        
        try:
            payment_info = sdk.payment().get(p_id)
            payment = payment_info['response']
            order_ref = payment.get('external_reference')
            
            if payment['status'] == 'approved' and order_ref:
                conn = get_db_connection()
                order = conn.execute('SELECT * FROM orders WHERE external_reference = ?', (order_ref,)).fetchone()
                
                if order and order['status'] != 'approved':
                    key = conn.execute('SELECT * FROM product_keys WHERE product_id = ? AND is_used = 0 LIMIT 1', (order['product_id'],)).fetchone()
                    if key:
                        conn.execute('UPDATE product_keys SET is_used = 1 WHERE id = ?', (key['id'],))
                        conn.execute('UPDATE orders SET status = "approved", key_assigned_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (key['id'], order['id']))
                        conn.commit()
                conn.close()
        except: pass

    return jsonify({'status': 'ok'}), 200

@payment_bp.route('/api/check_status/<order_ref>', methods=['GET'])
def check_status(order_ref):
    conn = get_db_connection()
    order = conn.execute('SELECT o.*, k.key_value FROM orders o LEFT JOIN product_keys k ON o.key_assigned_id = k.id WHERE o.external_reference = ?', (order_ref,)).fetchone()
    conn.close()
    if not order: return jsonify({'status': 'not_found'})
    if order['status'] == 'approved' and order['key_value']:
        return jsonify({'status': 'approved', 'key': order['key_value']})
    return jsonify({'status': order['status']})