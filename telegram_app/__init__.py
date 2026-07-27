"""
Telegram Blueprint
Exporta as rotas (webhook) para o app Flask principal.
"""
from telegram_app.routes import telegram_bp

# Exportando o Blueprint para ser importado em app.py
__all__ = ['telegram_bp']
