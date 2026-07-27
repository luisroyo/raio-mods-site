"""
Validators
Funções utilitárias para validar entradas (ex: formato de ID, regras).
"""

def is_valid_product_id(product_id: str) -> bool:
    """Verifica se o ID possui formato válido"""
    return isinstance(product_id, str) and len(product_id) > 0
