from dataclasses import dataclass
import hmac
import hashlib
import urllib.parse
import json
import time
import logging

logger = logging.getLogger("telegram_bot")

@dataclass
class TelegramWebAppUser:
    telegram_id: str
    username: str
    first_name: str

def validate_telegram_webapp_data(init_data: str, bot_token: str) -> TelegramWebAppUser:
    """
    Valida criptograficamente o initData enviado pelo Telegram WebApp.
    Retorna as informações do usuário se for válido, ou None se for inválido/falsificado.
    """
    if not init_data or not bot_token:
        return None
        
    try:
        # Parse da query string
        params = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
        params_dict = dict(params)
        
        received_hash = params_dict.get("hash")
        if not received_hash:
            return None
            
        # Filtrar e ordenar todas as chaves exceto 'hash'
        check_params = sorted([(k, v) for k, v in params if k != "hash"])
        data_check_string = "\n".join(f"{k}={v}" for k, v in check_params)
        
        # Chave secreta derivada do token do bot com a constante "WebAppData"
        secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
        
        # Calcular hash esperado
        expected_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        
        # Comparação segura contra ataques de tempo
        if not hmac.compare_digest(expected_hash, received_hash):
            logger.warning("Telegram WebApp authentication failed. Reason: Invalid hash.")
            return None
            
        # Validar expiração (auth_date) - máximo 5 minutos (300 segundos)
        auth_date_str = params_dict.get("auth_date")
        if auth_date_str:
            try:
                auth_date = int(auth_date_str)
                if abs(time.time() - auth_date) > 300:
                    logger.warning("Telegram WebApp authentication failed. Reason: Signature expired.")
                    return None
            except ValueError:
                logger.warning("Telegram WebApp authentication failed. Reason: Invalid auth_date format.")
                return None
            
        # Decodificar informações do usuário
        user_json = params_dict.get("user")
        if not user_json:
            return None
            
        user_data = json.loads(user_json)
        
        return TelegramWebAppUser(
            telegram_id=str(user_data.get("id")),
            username=user_data.get("username", ""),
            first_name=user_data.get("first_name", "")
        )
    except Exception as e:
        logger.error(f"Erro ao processar initData do Telegram: {e}")
        return None
