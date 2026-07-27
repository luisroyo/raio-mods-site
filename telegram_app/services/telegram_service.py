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

    @staticmethod
    def send_key_delivery(chat_id: str, product_name: str, key_value: str, download_link: str = None, order_ref: str = None) -> None:
        """Formata e envia a chave do produto para o usuário do Telegram de forma assíncrona."""
        from telegram_app.routes import send_telegram_message_safe
        
        text = (
            f"⚡ *PAGAMENTO APROVADO!* ⚡\n\n"
            f"Obrigado por comprar na *RAIO MODS*!\n\n"
            f"📦 *Produto:* {product_name}\n"
            f"🔑 *Sua Licença/Chave:* `{key_value}`\n"
        )
        if download_link and download_link.strip():
            text += f"\n📥 *Link para Download/Instruções:*\n{download_link}"
            
        send_telegram_message_safe(chat_id, text, order_ref=order_ref)

    @staticmethod
    def resend_key_delivery(order_ref: str) -> bool:
        """
        Recupera um pedido e reenvia a licença associada ao chat do Telegram do cliente.
        Útil para painéis administrativos ou reenvios automáticos em caso de falha.
        """
        from database.models import get_db_connection
        from contextlib import closing
        
        with closing(get_db_connection()) as conn:
            order = conn.execute('''
                SELECT o.telegram_id, o.external_reference, p.name as product_name, k.key_value, p.download_link
                FROM orders o
                JOIN products p ON o.product_id = p.id
                LEFT JOIN product_keys k ON o.key_assigned_id = k.id
                WHERE o.external_reference = ?
            ''', (order_ref,)).fetchone()
            
            if not order or not order['telegram_id']:
                return False
                
            key_value = order['key_value'] if order['key_value'] else "Nenhuma chave associada"
            TelegramService.send_key_delivery(
                chat_id=order['telegram_id'],
                product_name=order['product_name'],
                key_value=key_value,
                download_link=order['download_link'],
                order_ref=order['external_reference']
            )
            return True
