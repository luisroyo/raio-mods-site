import os
import hmac
import hashlib
import logging
from datetime import datetime
from contextlib import closing
import mercadopago
from database.models import get_db_connection

logger = logging.getLogger('payment_service')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class PaymentService:
    @staticmethod
    def get_mp_sdk():
        """Recupera o SDK do Mercado Pago inicializado com o token salvo no banco de dados ou .env."""
        token = None
        try:
            with closing(get_db_connection()) as conn:
                config = conn.execute('SELECT mercado_pago_token FROM config WHERE id = 1').fetchone()
                if config and 'mercado_pago_token' in config.keys():
                    db_token = config['mercado_pago_token']
                    if db_token and db_token.strip():
                        token = db_token.strip()
        except Exception as e:
            logger.warning(f"Erro ao ler token do banco: {e}")
        
        if not token:
            token = os.getenv('MP_ACCESS_TOKEN')

        return mercadopago.SDK(token) if token else None

    @staticmethod
    def verify_webhook_signature(headers: dict, query_params: dict, json_data: dict, client_ip: str) -> bool:
        """Valida a assinatura x-signature do Mercado Pago."""
        now = datetime.now().isoformat()
        
        def _reject(reason):
            logger.warning(f"[REJEITADO] Webhook inválido. IP: {client_ip} | Data: {now} | Motivo: {reason}")
            return False

        secret = os.getenv('MP_WEBHOOK_SECRET')
        if not secret:
            return _reject("MP_WEBHOOK_SECRET não configurado.")

        x_signature = headers.get('x-signature') or headers.get('X-Signature')
        x_request_id = headers.get('x-request-id') or headers.get('X-Request-Id')
        
        if not x_signature or not x_request_id:
            return _reject("Cabeçalhos x-signature ou x-request-id ausentes.")
            
        try:
            parts = dict(part.split('=') for part in x_signature.split(','))
            ts = parts.get('ts')
            v1 = parts.get('v1')
            
            if not ts or not v1:
                return _reject("Assinatura do webhook malformada.")
                
            data_id = query_params.get('data.id') or query_params.get('id')
            if not data_id:
                data_id = json_data.get('data', {}).get('id') or json_data.get('id')
                    
            if not data_id:
                return _reject("ID do pagamento não encontrado no payload.")
                
            data_id = str(data_id)
            manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
            
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                manifest.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if hmac.compare_digest(expected_signature, v1):
                return True
            else:
                return _reject("Assinatura do webhook inválida (hash não confere).")
                
        except Exception as e:
            return _reject(f"Erro na validação do webhook: {e}")

    @staticmethod
    def create_pix_payment(final_price: float, product_name: str, order_ref: str, payer_info: dict) -> dict:
        """Cria uma preferência de pagamento via PIX no Mercado Pago."""
        sdk = PaymentService.get_mp_sdk()
        if not sdk:
            raise ValueError("SDK Mercado Pago não configurado.")

        payment_data = {
            "transaction_amount": final_price,
            "description": f"{product_name} (Key)",
            "payment_method_id": "pix",
            "external_reference": order_ref,
            "payer": payer_info,
            "notification_url": "https://raiomodsgames.pythonanywhere.com/webhook/mp"
        }

        mp_res = sdk.payment().create(payment_data)
        payment_resp = mp_res.get("response", {})
        
        if 'error' in payment_resp:
            raise ValueError(f"Erro MP: {payment_resp.get('message', 'Erro desconhecido')}")

        try:
            tx_data = payment_resp['point_of_interaction']['transaction_data']
            return {
                'qr_code': tx_data['qr_code'],
                'qr_code_base64': tx_data['qr_code_base64']
            }
        except KeyError:
            logger.error(f"Resposta inesperada do MP ao gerar PIX: {payment_resp}")
            raise ValueError('Resposta inválida na geração de Pix pelo MercadoPago.')

    @staticmethod
    def create_card_payment(final_price: float, product_name: str, order_ref: str, card_payer_info: dict) -> dict:
        """Cria uma preferência de pagamento via Cartão no Mercado Pago."""
        sdk = PaymentService.get_mp_sdk()
        if not sdk:
            raise ValueError("SDK Mercado Pago não configurado.")

        preference_data = {
            "items": [{
                "title": f"Key: {product_name} (+Taxa Cartão)",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": final_price
            }],
            "payer": card_payer_info,
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
            raise ValueError('Erro ao gerar link de pagamento do Cartão.')

        return {
            'checkout_url': checkout_url
        }

    @staticmethod
    def search_payment(order_ref: str) -> list:
        """Busca um pagamento pelo external_reference no Mercado Pago."""
        sdk = PaymentService.get_mp_sdk()
        if not sdk:
            return []
        
        search_result = sdk.payment().search({"external_reference": order_ref})
        return search_result.get("response", {}).get("results", [])

    @staticmethod
    def get_payment_info(payment_id: str) -> dict:
        """Busca os dados completos de um pagamento específico pelo ID."""
        sdk = PaymentService.get_mp_sdk()
        if not sdk:
            raise ValueError("SDK Mercado Pago não configurado.")
            
        payment_info = sdk.payment().get(payment_id)
        return payment_info.get('response', {})
