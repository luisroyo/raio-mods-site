"""
Product Repository
Responsável pelo acesso aos dados dos produtos.
Lê diretamente do banco de dados SQLite oficial.
"""
import re
import time
from database.models import get_db_connection

class ProductRepository:
    # Variáveis de cache em memória
    _all_products_cache = None
    _all_products_cache_time = 0.0
    _product_by_id_cache = {}  # product_id -> (product_dict, timestamp)
    _CACHE_TTL = 60.0  # segundos de expiração (TTL)
    
    @staticmethod
    def clear_cache():
        """Limpa o cache em memória dos produtos."""
        ProductRepository._all_products_cache = None
        ProductRepository._all_products_cache_time = 0.0
        ProductRepository._product_by_id_cache.clear()
    
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
                    "id": str(child['id']),
                    "is_catalog": child['is_catalog'],
                    "parent_id": str(child['parent_id']) if child['parent_id'] is not None else None
                })
        else:
            plans.append({
                "duration": "Único",
                "price": ProductRepository._parse_price(row['price']),
                "id": str(row['id']),
                "is_catalog": row['is_catalog'],
                "parent_id": str(row['parent_id']) if row['parent_id'] is not None else None
            })
            
        return {
            "id": product_id,
            "name": row['name'],
            "description": row['description'] if row['description'] else "Sem descrição",
            "url": url,
            "image": row['image'] if row['image'] else "placeholder.jpg",
            "plans": plans,
            "is_catalog": row['is_catalog'],
            "parent_id": str(row['parent_id']) if row['parent_id'] is not None else None
        }

    @staticmethod
    def get_all_products():
        """Retorna a lista de todos os produtos principais cadastrados."""
        now = time.time()
        # Verificar cache com TTL de 60 segundos
        if (ProductRepository._all_products_cache is not None and 
            now - ProductRepository._all_products_cache_time < ProductRepository._CACHE_TTL):
            return ProductRepository._all_products_cache

        conn = get_db_connection()
        try:
            # Buscar todos os produtos ativos (principais e planos) de uma só vez para evitar consultas N+1
            rows = conn.execute('SELECT * FROM products WHERE is_active = 1 ORDER BY sort_order ASC, id ASC').fetchall()
            
            # Agrupar produtos principais e planos em memória
            main_products = []
            plans_by_parent = {}
            
            for row in rows:
                p_id = row['parent_id']
                if p_id is None:
                    main_products.append(row)
                else:
                    parent_key = str(p_id)
                    if parent_key not in plans_by_parent:
                        plans_by_parent[parent_key] = []
                    plans_by_parent[parent_key].append(row)
            
            products = []
            for row in main_products:
                product_id = str(row['id'])
                
                # Definir URL de compra
                if row['is_catalog'] == 1:
                    url = f"https://raiomodsgames.pythonanywhere.com/catalogo/{product_id}"
                else:
                    url = f"https://raiomodsgames.pythonanywhere.com/pagamento?product_id={product_id}"
                
                # Definir planos do produto
                plans = []
                if row['is_catalog'] == 1:
                    child_rows = plans_by_parent.get(product_id, [])
                    for child in child_rows:
                        plans.append({
                            "duration": child['name'],
                            "price": ProductRepository._parse_price(child['price']),
                            "id": str(child['id']),
                            "is_catalog": child['is_catalog'],
                            "parent_id": str(child['parent_id']) if child['parent_id'] is not None else None
                        })
                else:
                    plans.append({
                        "duration": "Único",
                        "price": ProductRepository._parse_price(row['price']),
                        "id": str(row['id']),
                        "is_catalog": row['is_catalog'],
                        "parent_id": str(row['parent_id']) if row['parent_id'] is not None else None
                    })
                
                products.append({
                    "id": product_id,
                    "name": row['name'],
                    "description": row['description'] if row['description'] else "Sem descrição",
                    "url": url,
                    "image": row['image'] if row['image'] else "placeholder.jpg",
                    "plans": plans,
                    "is_catalog": row['is_catalog'],
                    "parent_id": str(row['parent_id']) if row['parent_id'] is not None else None
                })
            
            # Salvar no cache antes de retornar
            ProductRepository._all_products_cache = products
            ProductRepository._all_products_cache_time = now
            return products
        except Exception as e:
            print(f"Erro ao buscar produtos para o bot: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def get_product_by_id(product_id: str):
        """Retorna um produto específico pelo seu ID."""
        now = time.time()
        # Verificar cache individual com TTL de 60 segundos
        cache_entry = ProductRepository._product_by_id_cache.get(product_id)
        if cache_entry is not None:
            cached_product, cache_time = cache_entry
            if now - cache_time < ProductRepository._CACHE_TTL:
                return cached_product

        conn = get_db_connection()
        try:
            row = conn.execute('SELECT * FROM products WHERE id = ? AND is_active = 1', (product_id,)).fetchone()
            if row:
                product = ProductRepository._format_product(row, conn)
                # Salvar no cache antes de retornar
                ProductRepository._product_by_id_cache[product_id] = (product, now)
                return product
            return None
        except Exception as e:
            print(f"Erro ao buscar produto {product_id} para o bot: {e}")
            return None
        finally:
            conn.close()
