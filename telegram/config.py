import os
import logging
from dotenv import load_dotenv

# Carrega variáveis do .env (caso exista localmente)
load_dotenv()

# Obtemos apenas um logger específico, sem sobrescrever o basicConfig do Flask
logger = logging.getLogger("telegram_bot")

class TelegramConfig:
    """Configurações centralizadas do Bot do Telegram"""
    
    # Tokens
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    # Webhook
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "padrao_secreto_temporario")
    
    @classmethod
    def is_valid(cls):
        """Verifica se as configurações mínimas existem"""
        if not cls.TELEGRAM_TOKEN:
            logger.error("TELEGRAM_TOKEN não configurado no .env!")
            return False
        return True
