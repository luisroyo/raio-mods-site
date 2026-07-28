"""
Messages
Centraliza os textos do bot. Todos os textos são gerados via função,
aceitando um código de idioma para retornar a tradução correta.
"""
from utils.i18n import translate_for_lang


def get_welcome(lang: str = 'pt') -> str:
    return translate_for_lang('bot_welcome', lang)


def get_how_to_buy(lang: str = 'pt') -> str:
    return translate_for_lang('bot_how_to_buy', lang)


def get_support(lang: str = 'pt') -> str:
    return translate_for_lang('bot_support', lang)


def get_error(lang: str = 'pt') -> str:
    return translate_for_lang('bot_error', lang)


def get_product_unavailable(lang: str = 'pt') -> str:
    return translate_for_lang('bot_product_unavailable', lang)


def get_products_menu(lang: str = 'pt') -> str:
    return translate_for_lang('bot_products_menu', lang)


# ─── Backwards-compatible aliases (kept for any code importing the old constants) ───
MSG_WELCOME = get_welcome('pt')
MSG_HOW_TO_BUY = get_how_to_buy('pt')
MSG_SUPPORT = get_support('pt')
MSG_ERROR = get_error('pt')
