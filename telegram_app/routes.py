"""
Routes
Endpoint do Flask para recebimento seguro do Webhook.
"""
import asyncio
from flask import Blueprint, request, jsonify
from telegram import Update
from telegram_app.config import TelegramConfig
from telegram_app.bot import bot_app
import logging

logger = logging.getLogger("telegram_bot")

telegram_bp = Blueprint('telegram_bp', __name__)

@telegram_bp.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """
    Recebe os updates do Telegram e processa via python-telegram-bot.
    Protegido opcionalmente via cabeçalho X-Telegram-Bot-Api-Secret-Token.
    """
    # Validação de Segurança do Webhook (PythonAnywhere)
    secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
    if TelegramConfig.WEBHOOK_SECRET and secret != TelegramConfig.WEBHOOK_SECRET:
        logger.warning("Tentativa de acesso não autorizada ao webhook.")
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Extrai o JSON do payload recebido
        data = request.get_json(force=True)
        
        # Converte o dicionário para um objeto Update do Telegram
        update = Update.de_json(data, bot_app.bot)

        # Processa o update de forma stateless no Flask
        # Como o Flask (tradicional) roda sincronamente, e a V20 do PTB é Async,
        # criamos uma task assíncrona executada até o fim para processar essa request.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def process():
            async with bot_app:
                await bot_app.process_update(update)

        loop.run_until_complete(process())
        loop.close()

        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Erro no endpoint do webhook: {e}", exc_info=True)
        return jsonify({"error": "Internal Error"}), 500
