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
    """Envia mensagem de forma assíncrona e segura de qualquer thread."""
    global _bot_initialized
    loop = get_persistent_loop()
    
    async def _send():
        global _bot_initialized
        if not _bot_initialized:
            try:
                await bot_app.initialize()
                await bot_app.start()
                _bot_initialized = True
            except Exception as e:
                logger.error(f"Erro ao inicializar o bot no envio seguro de mensagem: {e}")
        try:
            msg = await bot_app.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
            if order_ref:
                try:
                    from database.models import get_db_connection
                    from contextlib import closing
                    import time
                    
                    now_iso = time.strftime('%Y-%m-%d %H:%M:%S')
                    with closing(get_db_connection()) as conn:
                        conn.execute('''
                            UPDATE orders 
                            SET telegram_delivery_status = 'delivered',
                                telegram_delivered_at = ?,
                                telegram_message_id = ?
                            WHERE external_reference = ?
                        ''', (now_iso, str(msg.message_id), order_ref))
                        conn.commit()
                except Exception as db_err:
                    logger.error(f"Erro ao atualizar status de entrega de auditoria no banco: {db_err}")
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
                                telegram_message_id = ?
                            WHERE external_reference = ?
                        ''', (str(e)[:200], order_ref))
                        conn.commit()
                except Exception as db_err:
                    logger.error(f"Erro ao atualizar status de falha de auditoria no banco: {db_err}")
            
    asyncio.run_coroutine_threadsafe(_send(), loop)

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

