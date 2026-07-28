"""
Keyboards
Responsável pela montagem dos botões Inline (InlineKeyboardMarkup).
Aceita um parâmetro `lang` para gerar os rótulos dos botões no idioma correto.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram_app.constants import CB_PRODUCTS, CB_HOW_TO_BUY, CB_SUPPORT, CB_WEBSITE, CB_PREFIX_PRODUCT
from utils.i18n import translate_for_lang


def _t(key: str, lang: str) -> str:
    """Shortcut para traduzir uma chave no idioma informado."""
    return translate_for_lang(key, lang)


def get_main_menu_keyboard(lang: str = 'pt') -> InlineKeyboardMarkup:
    """Retorna o teclado do menu principal no idioma do usuário."""
    keyboard = [
        [InlineKeyboardButton(_t('btn_products', lang), callback_data=CB_PRODUCTS)],
        [InlineKeyboardButton(_t('btn_how_to_buy', lang), callback_data=CB_HOW_TO_BUY)],
        [InlineKeyboardButton(_t('btn_support', lang), callback_data=CB_SUPPORT)],
        [InlineKeyboardButton(_t('btn_official_site', lang), url="https://raiomodsgames.pythonanywhere.com")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_products_keyboard(products: list, lang: str = 'pt') -> InlineKeyboardMarkup:
    """
    Retorna o teclado com a lista dinâmica de produtos.
    products: lista de dicionários vinda do ProductService.
    """
    keyboard = []

    for product in products:
        callback_data = f"{CB_PREFIX_PRODUCT}{product['id']}"
        keyboard.append([InlineKeyboardButton(f"🎱 {product['name']}", callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton(_t('btn_back', lang), callback_data="menu_main")])

    return InlineKeyboardMarkup(keyboard)


def get_product_details_keyboard(product: dict, lang: str = 'pt') -> InlineKeyboardMarkup:
    """
    Retorna o teclado de detalhes do produto.
    Se for catálogo, cria botões para navegar nos sub-produtos ou comprar planos diretamente.
    """
    keyboard = []
    from telegram import WebAppInfo

    # Se o produto atual for um catálogo, mostramos botões para cada plano/subproduto
    if product.get('is_catalog') == 1:
        for plan in product.get('plans', []):
            if plan.get('is_catalog') == 1:
                keyboard.append([InlineKeyboardButton(f"🎱 {plan['duration']}", callback_data=f"{CB_PREFIX_PRODUCT}{plan['id']}")])
            else:
                from telegram_app.utils.formatters import format_price_for_lang
                price_str = format_price_for_lang(plan['price'], plan.get('price_usd', 0), lang)
                pay_url = f"https://raiomodsgames.pythonanywhere.com/pagamento?product_id={plan['id']}"
                keyboard.append([InlineKeyboardButton(f"{_t('btn_buy_now', lang)} — {plan['duration']} {price_str}", web_app=WebAppInfo(url=pay_url))])
    else:
        pay_url = product['url']
        keyboard.append([InlineKeyboardButton(_t('btn_buy_now', lang), web_app=WebAppInfo(url=pay_url))])

    # Botão de voltar inteligente
    parent_id = product.get('parent_id')
    back_callback = f"{CB_PREFIX_PRODUCT}{parent_id}" if parent_id else CB_PRODUCTS
    keyboard.append([InlineKeyboardButton(_t('btn_back', lang), callback_data=back_callback)])

    return InlineKeyboardMarkup(keyboard)


def get_back_button_keyboard(lang: str = 'pt') -> InlineKeyboardMarkup:
    """Teclado genérico com apenas o botão Voltar."""
    keyboard = [
        [InlineKeyboardButton(_t('btn_back', lang), callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)
