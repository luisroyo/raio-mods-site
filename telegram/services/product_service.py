"""
Product Service
Responsável pela regra de negócios de produtos.
Conecta a camada de handlers com o repositório.
"""
from telegram.repositories.product_repository import ProductRepository
from telegram.utils.formatters import format_price

class ProductService:
    
    @staticmethod
    def get_all_products():
        """Obtém todos os produtos formatados para os menus"""
        return ProductRepository.get_all_products()
        
    @staticmethod
    def get_product(product_id: str):
        """Obtém um produto específico"""
        return ProductRepository.get_product_by_id(product_id)
        
    @staticmethod
    def get_product_details_text(product: dict) -> str:
        """
        Gera um texto padronizado com nome, descrição e planos de um produto.
        """
        if not product:
            return "Produto não encontrado."
            
        text = f"🎱 *{product['name']}*\n\n"
        text += f"_{product['description']}_\n\n"
        text += "💰 *Planos Disponíveis:*\n"
        
        for plan in product['plans']:
            price_str = format_price(plan['price'])
            text += f"• {plan['duration']} - {price_str}\n"
            
        return text
