"""
Handlers
Camada de Apresentação. Liga as interações do Telegram (Comandos e Cliques) aos Serviços.
Detecta o idioma do usuário via update.effective_user.language_code e propaga para
mensagens, teclados e serviços de produto.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from telegram_app.constants import CB_PRODUCTS, CB_HOW_TO_BUY, CB_SUPPORT, CB_WEBSITE, CB_PREFIX_PRODUCT
from telegram_app.messages import get_welcome, get_how_to_buy, get_support, get_product_unavailable, get_products_menu, get_error
from telegram_app.keyboards import get_main_menu_keyboard, get_products_keyboard, get_product_details_keyboard, get_back_button_keyboard
from telegram_app.services.product_service import ProductService
from telegram_app.services.telegram_service import TelegramService
from utils.i18n import get_user_lang_from_telegram

logger = logging.getLogger("telegram_bot")


def _lang(update: Update) -> str:
    """Extrai e normaliza o código de idioma do usuário Telegram."""
    user = update.effective_user
    lang_code = user.language_code if user else None
    return get_user_lang_from_telegram(lang_code)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trata o comando /start e exibe o menu inicial no idioma do usuário."""
    lang = _lang(update)
    logger.info(f"Usuário {update.effective_user.id} acionou /start (lang={lang}).")

    await TelegramService.send_message(
        update=update,
        text=get_welcome(lang),
        reply_markup=get_main_menu_keyboard(lang)
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa todos os cliques do Menu Principal e navegação geral."""
    query = update.callback_query
    data = query.data
    lang = _lang(update)
    logger.info(f"Usuário {update.effective_user.id} clicou: {data} (lang={lang})")

    # Retorno ao Menu Inicial
    if data == "menu_main":
        await TelegramService.send_message(
            update=update,
            text=get_welcome(lang),
            reply_markup=get_main_menu_keyboard(lang)
        )

    # Navegação: Produtos
    elif data == CB_PRODUCTS:
        products_list = ProductService.get_all_products()
        keyboard = get_products_keyboard(products_list, lang)

        await TelegramService.send_message(
            update=update,
            text=get_products_menu(lang),
            reply_markup=keyboard
        )

    # Navegação: Como Comprar
    elif data == CB_HOW_TO_BUY:
        await TelegramService.send_message(
            update=update,
            text=get_how_to_buy(lang),
            reply_markup=get_back_button_keyboard(lang)
        )

    # Navegação: Suporte
    elif data == CB_SUPPORT:
        await TelegramService.send_message(
            update=update,
            text=get_support(lang),
            reply_markup=get_back_button_keyboard(lang)
        )


async def product_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa o clique em um produto específico."""
    query = update.callback_query
    data = query.data
    lang = _lang(update)

    # Extrai o ID do produto removendo o prefixo
    product_id = data.replace(CB_PREFIX_PRODUCT, "")
    logger.info(f"Usuário {update.effective_user.id} solicitou produto: {product_id} (lang={lang})")

    # Busca informações do produto
    product = ProductService.get_product(product_id)

    if not product:
        await TelegramService.send_message(
            update=update,
            text=get_product_unavailable(lang),
            reply_markup=get_back_button_keyboard(lang)
        )
        return

    # Gera texto formatado e teclado no idioma correto
    text = ProductService.get_product_details_text(product, lang)
    keyboard = get_product_details_keyboard(product, lang)

    await TelegramService.send_message(
        update=update,
        text=text,
        reply_markup=keyboard
    )
