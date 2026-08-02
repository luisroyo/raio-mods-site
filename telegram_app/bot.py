"""
Bot Initialization
Isola a criação da instância do python-telegram-bot (Application),
registro dos Handlers e do ErrorHandler.
"""
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram_app.config import TelegramConfig
from telegram_app.handlers import (
    start_command, main_menu_callback, product_selection_callback,
    catalogo_command, suporte_command, site_command
)
from telegram_app.constants import CB_PREFIX_PRODUCT
from telegram_app.error_handler import global_error_handler
import logging

logger = logging.getLogger("telegram_bot")

def create_bot_application() -> Application:
    """
    Cria e configura a instância Singleton do bot.
    Registra todos os roteamentos de comandos e botões.
    """
    if not TelegramConfig.is_valid():
        logger.warning("Bot não será iniciado corretamente pois o Token é inválido.")

    # Inicializa o Application builder
    application = Application.builder().token(TelegramConfig.TELEGRAM_TOKEN).build()

    # Registra Command Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("catalogo", catalogo_command))
    application.add_handler(CommandHandler("kos", catalogo_command))
    application.add_handler(CommandHandler("apk", catalogo_command))
    application.add_handler(CommandHandler("suporte", suporte_command))
    application.add_handler(CommandHandler("site", site_command))

    # Registra Callback Handlers
    # 1. Botões do Menu Principal (cliques genéricos que não são produtos)
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern=r"^(menu_)"))
    
    # 2. Botões de Produtos Específicos (Iniciam com o prefixo)
    application.add_handler(CallbackQueryHandler(product_selection_callback, pattern=f"^{CB_PREFIX_PRODUCT}"))

    # Registra o Tratador Global de Erros (Apenas 1 vez)
    application.add_error_handler(global_error_handler)

    return application

# Instância única global para ser importada pelo routes.py
bot_app = create_bot_application()
