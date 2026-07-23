import os
import re
from datetime import datetime

def parse_price(price_str) -> float:
    """Converte strings de preço em float de forma segura e padronizada."""
    if not price_str:
        return 1.00
    try:
        clean_str = str(price_str).lower().replace('r$', '').replace(',', '.').strip()
        return float(clean_str)
    except ValueError:
        return 1.00

def get_active_global_promo(conn):
    """
    Verifica se existe uma promoção global configurada e ativa (não expirada).
    Retorna um dicionário com os dados da promoção ou None.
    """
    try:
        # Busca a configuração de promoção global
        row = conn.execute(
            '''SELECT global_discount_type, global_discount_value, 
                      global_discount_expiry, global_discount_label 
               FROM config WHERE id = 1'''
        ).fetchone()
        
        if not row:
            return None
            
        # Garante que temos as chaves necessárias
        row_keys = row.keys() if hasattr(row, 'keys') else []
        if not row_keys or 'global_discount_value' not in row_keys:
            return None
            
        discount_value = float(row['global_discount_value'] or 0)
        if discount_value <= 0:
            return None
            
        expiry_str = (row['global_discount_expiry'] or '').strip()
        if expiry_str:
            try:
                # Trata tanto o formato 'YYYY-MM-DD HH:MM:SS' quanto 'YYYY-MM-DDTHH:MM'
                if 't' in expiry_str.lower():
                    expiry = datetime.strptime(expiry_str, '%Y-%m-%dT%H:%M')
                else:
                    expiry = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
                
                # Se a data atual for maior que a expiração, a promoção expirou
                if datetime.now() > expiry:
                    return None
            except Exception as e:
                # Em caso de erro ao parsear a data, assume que a promoção está inativa/expirou por segurança
                return None
                
        return {
            'type': row['global_discount_type'] or 'percent',
            'value': discount_value,
            'expiry': expiry_str,
            'label': row['global_discount_label'] or 'PROMO'
        }
    except Exception as e:
        print(f"[PROMO] Erro ao buscar promoção global: {e}")
        return None

def apply_global_promo(product, promo):
    """
    Aplica a promoção global a um produto se ele não tiver uma promoção individual ativa.
    Recebe um dicionário (ou objeto tipo Row convertido em dict) e retorna o produto modificado ou o próprio produto.
    """
    p_dict = dict(product)
    if not promo:
        return p_dict
    
    # Se o produto já possui uma promoção individual (promo_price configurado e diferente de vazio), não aplica a global
    if p_dict.get('promo_price') and str(p_dict['promo_price']).strip() != '':
        return p_dict
        
    # Se o produto for um catálogo (is_catalog == 1 ou is_folder), não se aplica preço promocional
    if p_dict.get('is_catalog') == 1 or p_dict.get('is_folder'):
        return p_dict

    try:
        base_price = parse_price(p_dict.get('price'))
        if promo['type'] == 'percent':
            discount = base_price * (promo['value'] / 100.0)
        else:
            discount = promo['value']
            
        promo_price_val = max(1.0, base_price - discount)
        p_dict['promo_price'] = f"R$ {promo_price_val:.2f}".replace('.', ',')
        p_dict['promo_label'] = promo['label'] or 'PROMO'
    except Exception as e:
        print(f"[PROMO] Erro ao aplicar promoção global no produto {p_dict.get('id')}: {e}")
        
    return p_dict
