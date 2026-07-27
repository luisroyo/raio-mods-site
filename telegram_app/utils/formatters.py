"""
Formatters
Funções utilitárias de formatação visual.
"""

def format_price(value: float) -> str:
    """Formata um float (10.00) para Real Brasileiro (R$ 10,00)."""
    return f"R$ {value:.2f}".replace('.', ',')

def escape_markdown(text: str) -> str:
    """Função preparada para escapar caracteres especiais no MarkdownV2 (se necessário futuramente)."""
    return text
