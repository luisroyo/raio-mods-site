"""
Product Repository
Responsável pelo acesso aos dados dos produtos.
Lê diretamente do banco de dados SQLite oficial.
"""
import re
from database.models import get_db_connection

class ProductRepository:
    
    @staticmethod
    def _parse_price(price_str):
        if not price_str:
            return 0.0
        match = re.search(r'[\d\.,]+', str(price_str))
        if match:
            num_str = match.group()
            if ',' in num_str and '.' in num_str:
                num_str = num_str.replace('.', '').replace(',', '.')
            elif ',' in num_str:
                num_str = num_str.replace(',', '.')
            try:
                return float(num_str)
            except ValueError:
                pass
        return 0.0

    @staticmethod
    def _format_product(row, conn):
        """Formata um produto do banco de dados para o dicionário esperado pelo bot."""
        product_id = str(row['id'])
        
        # O URL para o botão de compra
        if row['is_catalog'] == 1:
            url = f"https://raiomodsgames.pythonanywhere.com/catalogo/{product_id}"
        else:
            url = f"https://raiomodsgames.pythonanywhere.com/pagamento?product_id={product_id}"
            
        plans = []
        if row['is_catalog'] == 1:
            children = conn.execute('SELECT * FROM products WHERE parent_id = ? AND is_active = 1 ORDER BY sort_order ASC, id ASC', (row['id'],)).fetchall()
            for child in children:
                plans.append({
                    "duration": child['name'],
                    "price": ProductRepository._parse_price(child['price']),
                    "id": str(child['id'])
                })
        else:
            plans.append({
                "duration": "Único",
                "price": ProductRepository._parse_price(row['price']),
                "id": str(row['id'])
            })
            
        return {
            "id": product_id,
            "name": row['name'],
            "description": row['description'] if row['description'] else "Sem descrição",
            "url": url,
            "image": row['image'] if row['image'] else "placeholder.jpg",
            "plans": plans
        }

    @staticmethod
    def get_all_products():
        """Retorna a lista de todos os produtos principais cadastrados."""
        conn = get_db_connection()
        try:
            # Buscar produtos principais ativos (sem parent_id)
            rows = conn.execute('SELECT * FROM products WHERE parent_id IS NULL AND is_active = 1 ORDER BY sort_order ASC, id ASC').fetchall()
            products = []
            for row in rows:
                products.append(ProductRepository._format_product(row, conn))
            return products
        except Exception as e:
            print(f"Erro ao buscar produtos para o bot: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def get_product_by_id(product_id: str):
        """Retorna um produto específico pelo seu ID."""
        conn = get_db_connection()
        try:
            row = conn.execute('SELECT * FROM products WHERE id = ? AND is_active = 1', (product_id,)).fetchone()
            if row:
                return ProductRepository._format_product(row, conn)
            return None
        except Exception as e:
            print(f"Erro ao buscar produto {product_id} para o bot: {e}")
            return None
        finally:
            conn.close()
