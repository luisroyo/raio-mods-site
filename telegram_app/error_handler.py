"""
Error Handler
Captura e trata exceções globais que ocorrem durante o processamento de atualizações do bot.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram_app.messages import MSG_ERROR
from telegram_app.services.telegram_service import TelegramService

logger = logging.getLogger("telegram_bot")

async def global_error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Tratador global de erros. Loga a exceção e avisa o usuário de forma amigável.
    """
    logger.error("Exceção não tratada ao processar update:", exc_info=context.error)

    # Verifica se a request partiu do usuário
    if update and update.effective_chat:
        try:
            await TelegramService.send_message(
                update=update,
                text=MSG_ERROR
            )
        except Exception as send_error:
            # Se até o envio de erro falhar, não temos como avisar o usuário
            logger.error(f"Falha ao enviar mensagem de erro de fallback: {send_error}")
