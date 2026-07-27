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
    Retorna o teclado de detalhes do produto.
    Se for catálogo, cria botões para navegar nos sub-produtos ou comprar planos diretamente.
    """
    keyboard = []
    from telegram import WebAppInfo
    
    # Se o produto atual for um catálogo, mostramos botões para cada plano/subproduto
    if product.get('is_catalog') == 1:
        for plan in product.get('plans', []):
            # Se o plano for também um catálogo, é um subproduto (botão de navegação)
            if plan.get('is_catalog') == 1:
                keyboard.append([InlineKeyboardButton(f"🎱 {plan['duration']}", callback_data=f"{CB_PREFIX_PRODUCT}{plan['id']}")])
            else:
                # Se for um plano de compra simples, mostra o botão com preço que leva ao pagamento
                from telegram_app.utils.formatters import format_price
                price_str = format_price(plan['price'])
                pay_url = f"https://raiomodsgames.pythonanywhere.com/pagamento?product_id={plan['id']}"
                keyboard.append([InlineKeyboardButton(f"🛒 {plan['duration']} - {price_str}", web_app=WebAppInfo(url=pay_url))])
    else:
        # Se for um produto único, mostra o botão de compra direta
        pay_url = product['url']
        keyboard.append([InlineKeyboardButton("🛒 Comprar Agora", web_app=WebAppInfo(url=pay_url))])
        
    # Botão de voltar inteligente: se tiver pai (parent_id), volta para o catálogo pai; caso contrário, volta para a lista
    parent_id = product.get('parent_id')
    if parent_id:
        back_callback = f"{CB_PREFIX_PRODUCT}{parent_id}"
    else:
        back_callback = CB_PRODUCTS
        
    keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data=back_callback)])
    
    return InlineKeyboardMarkup(keyboard)

def get_back_button_keyboard() -> InlineKeyboardMarkup:
    """Teclado genérico com apenas o botão Voltar."""
    keyboard = [
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)
