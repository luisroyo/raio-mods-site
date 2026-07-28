"""
Product Service
Responsável pela regra de negócios de produtos.
Conecta a camada de handlers com o repositório.
"""
from telegram_app.repositories.product_repository import ProductRepository
from telegram_app.utils.formatters import format_price, format_price_for_lang
from utils.i18n import translate_for_lang, get_currency_for_lang


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
    def get_product_details_text(product: dict, lang: str = 'pt') -> str:
        """
        Gera um texto padronizado com nome, descrição e planos de um produto.
        Utiliza os campos localizados (name_pt/name_en/etc) quando disponíveis,
        com fallback para o campo legado 'name'/'description'.
        Os preços são exibidos na moeda correspondente ao idioma do usuário.
        """
        if not product:
            return translate_for_lang('bot_product_unavailable', lang)

        # Nome localizado com fallback
        name = (
            product.get(f'name_{lang}')
            or product.get('name_pt')
            or product.get('name', 'N/A')
        )

        # Descrição localizada com fallback
        no_desc = translate_for_lang('bot_no_description', lang)
        description = (
            product.get(f'description_{lang}')
            or product.get('description_pt')
            or product.get('description')
            or no_desc
        )

        text = f"🎱 *{name}*\n\n"
        text += f"_{description}_\n\n"

        # Filtra apenas planos de compra reais (is_catalog == 0)
        purchase_plans = [p for p in product.get('plans', []) if p.get('is_catalog') == 0]

        if purchase_plans:
            text += translate_for_lang('bot_available_plans', lang) + "\n"
            for plan in purchase_plans:
                price_brl = plan.get('price_brl') or plan.get('price', 0)
                price_usd = plan.get('price_usd', 0)
                price_str = format_price_for_lang(price_brl, price_usd, lang)
                text += f"• {plan['duration']} — {price_str}\n"

        return text
