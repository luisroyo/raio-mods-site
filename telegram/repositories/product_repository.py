"""
Product Repository
Responsável pelo acesso aos dados dos produtos.
Atualmente acessa o dicionário em memória. Futuramente acessará o banco de dados.
"""
from telegram.data.products import PRODUCTS

class ProductRepository:
    
    @staticmethod
    def get_all_products():
        """Retorna a lista de todos os produtos cadastrados."""
        # Retorna apenas os valores do dicionário
        return list(PRODUCTS.values())
    
    @staticmethod
    def get_product_by_id(product_id: str):
        """Retorna um produto específico pelo seu ID (chave)."""
        return PRODUCTS.get(product_id)
