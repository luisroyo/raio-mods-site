import mercadopago
from flask import Blueprint, request, jsonify, current_app, url_for
from database.models import get_db_connection
import json

payment_bp = Blueprint('payment', __name__)

def get_mp_sdk():
    """Inicializa o SDK com o token salvo no banco"""
    conn = get_db_connection()
    config = conn.execute('SELECT mercado_pago_token FROM config WHERE id = 1').fetchone()
    conn.close()
    
    token = config['mercado_pago_token'] if config and 'mercado_pago_token' in config.keys() else None
    if not token:
        return None
    return mercadopago.SDK(token)

@payment_bp.route('/api/checkout', methods=['POST'])
def create_payment():
    data = request.json
    product_id = data.get('product_id')
    email = data.get('email')
    
    if not product_id or not email:
        return jsonify({'error': 'Dados incompletos'}), 400

    conn = get_db_connection()
    
    # 1. Verifica se tem Estoque (Chave disponível)
    # Pega uma chave que não foi usada (is_used = 0)
    key_check = conn.execute('SELECT id FROM product_keys WHERE product_id = ? AND is_used = 0 LIMIT 1', (product_id,)).fetchone()
    
    if not key_check:
        conn.close()
        return jsonify({'error': 'Produto esgotado! Entre em contato com o suporte.'}), 409

    # 2. Busca dados do produto
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        conn.close()
        return jsonify({'error': 'Produto não encontrado'}), 404

    # 3. Gera o PIX no Mercado Pago
    sdk = get_mp_sdk()
    if not sdk:
        conn.close()
        return jsonify({'error': 'Sistema de pagamento não configurado (Token ausente).'}), 500

    # Limpa o preço (remove R$ e espaços) e converte para float
    try:
        clean_price = float(str(product['price']).lower().replace('r$', '').replace(',', '.').strip())
    except:
        clean_price = 1.00 # Fallback de segurança

    payment_data = {
        "transaction_amount": clean_price,
        "description": f"Key: {product['name']}",
        "payment_method_id": "pix",
        "payer": {
            "email": email,
            "first_name": email.split('@')[0]
        },
        # AQUI ESTÁ SEU ENDEREÇO CORRETO AGORA:
        "notification_url": "https://raiomodsgames.pythonanywhere.com/webhook/mp"
    }

    try:
        payment_response = sdk.payment().create(payment_data)
        payment = payment_response["response"]
        
        # 4. Salva o pedido no banco como 'pending'
        external_ref = str(payment['id'])
        qr_code = payment['point_of_interaction']['transaction_data']['qr_code']
        qr_base64 = payment['point_of_interaction']['transaction_data']['qr_code_base64']
        
        conn.execute('''
            INSERT INTO orders (external_reference, product_id, customer_email, amount, status, qr_code, qr_code_base64)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (external_ref, product_id, email, clean_price, 'pending', qr_code, qr_base64))
        
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'qr_code': qr_code,
            'qr_code_base64': qr_base64,
            'order_id': external_ref
        })

    except Exception as e:
        conn.close()
        print(f"Erro MP: {e}")
        return jsonify({'error': f'Erro no Mercado Pago: {str(e)}'}), 500

@payment_bp.route('/webhook/mp', methods=['POST'])
def webhook():
    """O Robô que recebe o aviso do Mercado Pago"""
    topic = request.args.get('topic') or request.args.get('type')
    p_id = request.args.get('id') or request.args.get('data.id')

    if topic == 'payment':
        sdk = get_mp_sdk()
        if not sdk: return jsonify({'status': 'error_config'}), 500
        
        # Consulta o status real no Mercado Pago
        payment_info = sdk.payment().get(p_id)
        payment = payment_info['response']
        
        if payment['status'] == 'approved':
            external_ref = str(payment['id'])
            
            conn = get_db_connection()
            
            # Verifica se o pedido existe e se já não foi entregue
            order = conn.execute('SELECT * FROM orders WHERE external_reference = ?', (external_ref,)).fetchone()
            
            if order and order['status'] != 'approved':
                # --- A MÁGICA DA ENTREGA ---
                
                # 1. Pega uma chave livre
                key = conn.execute('SELECT * FROM product_keys WHERE product_id = ? AND is_used = 0 LIMIT 1', (order['product_id'],)).fetchone()
                
                if key:
                    # 2. Marca a chave como usada
                    conn.execute('UPDATE product_keys SET is_used = 1 WHERE id = ?', (key['id'],))
                    
                    # 3. Atualiza o pedido com 'approved' e vincula a chave
                    conn.execute('UPDATE orders SET status = "approved", key_assigned_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (key['id'], order['id']))
                    conn.commit()
                    print(f"✅ Venda Aprovada! Chave {key['id']} entregue para pedido {order['id']}")
                else:
                    # Caso raro: Acabou a chave NO MOMENTO que o cara pagou
                    print(f"⚠️ Venda Aprovada, mas SEM ESTOQUE para pedido {order['id']}")
            
            conn.close()

    return jsonify({'status': 'ok'}), 200

@payment_bp.route('/api/check_status/<order_ref>', methods=['GET'])
def check_status(order_ref):
    """O Frontend chama isso a cada 5s para saber se pagou"""
    conn = get_db_connection()
    order = conn.execute('SELECT o.*, k.key_value FROM orders o LEFT JOIN product_keys k ON o.key_assigned_id = k.id WHERE o.external_reference = ?', (order_ref,)).fetchone()
    conn.close()

    if not order:
        return jsonify({'status': 'not_found'})
    
    if order['status'] == 'approved' and order['key_value']:
        return jsonify({
            'status': 'approved',
            'key': order['key_value'] # AQUI ESTÁ A CHAVE DO CLIENTE!
        })
    
    return jsonify({'status': order['status']})