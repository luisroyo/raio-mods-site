"""
Formatters
Funções utilitárias de formatação visual.
"""
from utils.i18n import get_currency_for_lang


def format_price(value: float) -> str:
    """Formata um float (10.00) para Real Brasileiro (R$ 10,00). Mantido por compatibilidade."""
    return f"R$ {value:.2f}".replace('.', ',')


def format_price_for_lang(price_brl: float, price_usd: float, lang: str) -> str:
    """
    Retorna o preço formatado na moeda correspondente ao idioma do usuário.
    Se o preço_usd for 0 ou None, exibe BRL independente do idioma.
    """
    currency = get_currency_for_lang(lang)
    if currency == 'USD' and price_usd and price_usd > 0:
        return f"$ {price_usd:.2f}"
    return f"R$ {price_brl:.2f}".replace('.', ',')


def escape_markdown(text: str) -> str:
    """Função preparada para escapar caracteres especiais no MarkdownV2 (se necessário futuramente)."""
    return text
