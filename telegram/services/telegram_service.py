"""
Telegram Service
Responsável por abstrair chamadas nativas da API do Telegram.
"""
from telegram import Update
from telegram.ext import CallbackContext

class TelegramService:
    
    @staticmethod
    async def send_message(update: Update, text: str, reply_markup=None, parse_mode='Markdown'):
        """
        Envia uma mensagem de texto simples ou com teclado.
        Se for uma resposta a callback query, tenta editar a mensagem original (opcional) ou enviar nova.
        Aqui vamos padronizar para responder no chat.
        """
        if update.callback_query:
            # Responde o alerta de loading do botão
            await update.callback_query.answer()
            
        await update.effective_chat.send_message(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
