"""
Handlers
Camada de Apresentação. Liga as interações do Telegram (Comandos e Cliques) aos Serviços.
Não contém regras de negócio de produtos ou formatações textuais (apenas delegação).
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from telegram_app.constants import CB_PRODUCTS, CB_HOW_TO_BUY, CB_SUPPORT, CB_WEBSITE, CB_PREFIX_PRODUCT
from telegram_app.messages import MSG_WELCOME, MSG_HOW_TO_BUY, MSG_SUPPORT
from telegram_app.keyboards import get_main_menu_keyboard, get_products_keyboard, get_product_details_keyboard, get_back_button_keyboard
from telegram_app.services.product_service import ProductService
from telegram_app.services.telegram_service import TelegramService

logger = logging.getLogger("telegram_bot")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trata o comando /start e exibe o menu inicial."""
    logger.info(f"Usuário {update.effective_user.id} acionou /start.")
    
    # Futuro: Aqui chamaríamos UserService.register_or_update_user(...)
    
    await TelegramService.send_message(
        update=update,
        text=MSG_WELCOME,
        reply_markup=get_main_menu_keyboard()
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa todos os cliques do Menu Principal e navegação geral."""
    query = update.callback_query
    data = query.data
    logger.info(f"Usuário clicou no callback: {data}")

    # Retorno ao Menu Inicial
    if data == "menu_main":
        await TelegramService.send_message(
            update=update,
            text=MSG_WELCOME,
            reply_markup=get_main_menu_keyboard()
        )
        
    # Navegação: Produtos
    elif data == CB_PRODUCTS:
        products_list = ProductService.get_all_products()
        keyboard = get_products_keyboard(products_list)
        
        await TelegramService.send_message(
            update=update,
            text="🎱 *Escolha um produto para ver os detalhes:*",
            reply_markup=keyboard
        )

    # Navegação: Como Comprar
    elif data == CB_HOW_TO_BUY:
        await TelegramService.send_message(
            update=update,
            text=MSG_HOW_TO_BUY,
            reply_markup=get_back_button_keyboard()
        )

    # Navegação: Suporte
    elif data == CB_SUPPORT:
        await TelegramService.send_message(
            update=update,
            text=MSG_SUPPORT,
            reply_markup=get_back_button_keyboard()
        )


async def product_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa o clique em um produto específico."""
    query = update.callback_query
    data = query.data
    
    # Extrai o ID do produto removendo o prefixo
    product_id = data.replace(CB_PREFIX_PRODUCT, "")
    logger.info(f"Usuário solicitou visualização do produto: {product_id}")
    
    # Busca informações do produto
    product = ProductService.get_product(product_id)
    
    if not product:
        await TelegramService.send_message(
            update=update,
            text="Desculpe, este produto não está mais disponível.",
            reply_markup=get_back_button_keyboard()
        )
        return
        
    # Gera texto formatado e teclado
    user_id = str(update.effective_user.id) if update.effective_user else None
    text = ProductService.get_product_details_text(product)
    keyboard = get_product_details_keyboard(product, user_id)
    
    # Futuro: Se tivermos envio de imagem aqui (assets/images), chamaremos uma variante do TelegramService.send_photo
    await TelegramService.send_message(
        update=update,
        text=text,
        reply_markup=keyboard
    )
