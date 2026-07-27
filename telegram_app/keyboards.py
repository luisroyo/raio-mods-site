"""
Keyboards
Responsável pela montagem dos botões Inline (InlineKeyboardMarkup).
Recebe os dados já formatados dos Services e transforma em interface do Telegram.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram_app.constants import CB_PRODUCTS, CB_HOW_TO_BUY, CB_SUPPORT, CB_WEBSITE, CB_PREFIX_PRODUCT

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Retorna o teclado do menu principal"""
    keyboard = [
        [InlineKeyboardButton("🎱 Produtos", callback_data=CB_PRODUCTS)],
        [InlineKeyboardButton("🛒 Como Comprar", callback_data=CB_HOW_TO_BUY)],
        [InlineKeyboardButton("🛠 Suporte", callback_data=CB_SUPPORT)],
        [InlineKeyboardButton("🌐 Site Oficial", url="https://raiomodsgames.pythonanywhere.com", callback_data=CB_WEBSITE)]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_products_keyboard(products: list) -> InlineKeyboardMarkup:
    """
    Retorna o teclado com a lista dinâmica de produtos.
    products: lista de dicionários vinda do ProductService.
    """
    keyboard = []
    
    # Criar um botão para cada produto (2 por linha ou 1 por linha)
    for product in products:
        # callback_data ficará como "prod_kos_virtual"
        callback_data = f"{CB_PREFIX_PRODUCT}{product['id']}"
        keyboard.append([InlineKeyboardButton(f"🎱 {product['name']}", callback_data=callback_data)])
        
    # Botão de voltar ao menu principal
    keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_product_details_keyboard(product: dict) -> InlineKeyboardMarkup:
    """
    Retorna o teclado de detalhes do produto, com o botão de compra apontando para a URL.
    """
    keyboard = [
        [InlineKeyboardButton("🛒 Comprar Agora", url=product['url'])],
        [InlineKeyboardButton("🔙 Voltar aos Produtos", callback_data=CB_PRODUCTS)]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_button_keyboard() -> InlineKeyboardMarkup:
    """Teclado genérico com apenas o botão Voltar."""
    keyboard = [
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)
