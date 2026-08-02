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
    async def send_photo_with_fallback(update: Update, photo_url: str, caption: str, reply_markup=None, parse_mode='Markdown'):
        """
        Tenta enviar uma foto com legenda. Se falhar (URL inválida, por exemplo), envia apenas o texto.
        """
        import logging
        if update.callback_query:
            await update.callback_query.answer()
            
        try:
            if not photo_url or photo_url == 'placeholder.jpg':
                raise ValueError("No valid image URL provided")
                
            # Trata URLs relativas caso a imagem tenha sido upada direto no site
            if photo_url.startswith('/'):
                photo_url = f"https://raiomodsgames.pythonanywhere.com{photo_url}"
                
            await update.effective_chat.send_photo(
                photo=photo_url,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as e:
            logging.getLogger("telegram_bot").warning(f"Falha ao enviar foto ({photo_url}): {e}. Enviando texto...")
            # Fallback para envio apenas de texto
            await update.effective_chat.send_message(
                text=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )

    @staticmethod
    def send_key_delivery(chat_id: str, product_name: str, key_value: str, download_link: str = None, order_ref: str = None) -> None:
        """Formata e envia a chave do produto para o usuário do Telegram de forma assíncrona."""
        from telegram_app.routes import send_telegram_message_safe
        
        safe_product_name = str(product_name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        safe_key_value = str(key_value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        text = (
            f"⚡ <b>PAGAMENTO APROVADO!</b> ⚡\n\n"
            f"Obrigado por comprar na <b>RAIO MODS</b>!\n\n"
            f"📦 <b>Produto:</b> {safe_product_name}\n"
            f"🔑 <b>Sua Licença/Chave:</b> <code>{safe_key_value}</code>\n"
        )
        if download_link and download_link.strip():
            safe_download_link = str(download_link).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            text += f"\n📥 <b>Link para Download/Instruções:</b>\n{safe_download_link}"
            
        send_telegram_message_safe(chat_id, text, parse_mode='HTML', order_ref=order_ref)

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
