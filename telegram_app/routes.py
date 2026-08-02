"""
Routes
Endpoint do Flask para recebimento seguro do Webhook.
"""
import asyncio
import atexit
from flask import Blueprint, request, jsonify
from telegram import Update
from telegram_app.config import TelegramConfig
from telegram_app.bot import bot_app
import logging
logger = logging.getLogger("telegram_bot")

telegram_bp = Blueprint('telegram_bp', __name__)

_loop = None
_bot_initialized = False

def get_persistent_loop():
    global _loop
    if _loop is None:
        try:
            _loop = asyncio.get_event_loop()
        except RuntimeError:
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
    return _loop

def shutdown_bot():
    global _bot_initialized, _loop
    if _bot_initialized and _loop is not None:
        try:
            logger.info("Encerrando conexões do bot do Telegram...")
            _loop.run_until_complete(bot_app.stop())
            _loop.run_until_complete(bot_app.shutdown())
            logger.info("Bot do Telegram finalizado com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao finalizar bot: {e}")
        finally:
            _bot_initialized = False

atexit.register(shutdown_bot)

def send_telegram_message_safe(chat_id: str, text: str, parse_mode: str = 'Markdown', order_ref: str = None) -> None:
    """Envia mensagem de forma segura usando requests (evita problemas de event loop do asyncio)."""
    import requests
    import threading
    
    def _send():
        try:
            url = f"https://api.telegram.org/bot{TelegramConfig.TELEGRAM_TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            resp = requests.post(url, json=payload, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                msg_id = data.get('result', {}).get('message_id')
                if order_ref:
                    try:
                        from database.models import get_db_connection
                        from contextlib import closing
                        with closing(get_db_connection()) as conn:
                            conn.execute('''
                                UPDATE orders 
                                SET telegram_delivery_status = 'delivered',
                                    telegram_delivered_at = CURRENT_TIMESTAMP,
                                    telegram_message_id = ?
                                WHERE external_reference = ?
                            ''', (str(msg_id), order_ref))
                            conn.commit()
                    except Exception as db_err:
                        logger.error(f"Erro ao atualizar status de entrega de auditoria no banco: {db_err}")
            else:
                logger.error(f"Erro da API do Telegram: {resp.text}")
                if order_ref:
                    try:
                        from database.models import get_db_connection
                        from contextlib import closing
                        with closing(get_db_connection()) as conn:
                            conn.execute('''
                                UPDATE orders 
                                SET telegram_delivery_status = 'failed',
                                    telegram_delivery_error = ?
                                WHERE external_reference = ?
                            ''', (resp.text[:500], order_ref))
                            conn.commit()
                    except Exception as db_err:
                        logger.error(f"Erro ao atualizar status de falha de auditoria no banco: {db_err}")
                        
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para chat_id {chat_id}: {e}")
            if order_ref:
                try:
                    from database.models import get_db_connection
                    from contextlib import closing
                    with closing(get_db_connection()) as conn:
                        conn.execute('''
                            UPDATE orders 
                            SET telegram_delivery_status = 'failed',
                                telegram_delivery_error = ?
                            WHERE external_reference = ?
                        ''', (str(e)[:500], order_ref))
                        conn.commit()
                except Exception as db_err:
                    logger.error(f"Erro ao atualizar status de falha de auditoria no banco: {db_err}")
            
    threading.Thread(target=_send).start()

@telegram_bp.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """
    Recebe os updates do Telegram e processa via python-telegram-bot.
    Protegido opcionalmente via cabeçalho X-Telegram-Bot-Api-Secret-Token.
    """
    global _bot_initialized

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

        # Processa o update de forma stateless e rápida no Flask usando loop persistente
        loop = get_persistent_loop()

        # Inicializa o bot apenas uma vez no loop persistente
        if not _bot_initialized:
            logger.info("Inicializando bot do Telegram pela primeira vez...")
            loop.run_until_complete(bot_app.initialize())
            loop.run_until_complete(bot_app.start())
            _bot_initialized = True
            logger.info("Bot do Telegram inicializado e iniciado com sucesso!")

        # Processa o update
        loop.run_until_complete(bot_app.process_update(update))

        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Erro no endpoint do webhook: {e}", exc_info=True)
        return jsonify({"error": "Internal Error"}), 500

