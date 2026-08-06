import sqlite3

def run_data_migrations(cursor):
    """Executa migrações de dados (higienização, seed e atualização de registros)."""
    
    # 1. Seed Config (Insere configuração padrão se vazio)
    cursor.execute('SELECT count(*) FROM config')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO config (id, pix_key, binance_wallet) VALUES (1, "", "")')

    # 2. Auto-migração: Move download_link textuais legados para a tabela links e atualiza link_id
    try:
        # Primeiro, verifica se as colunas necessárias existem para evitar erros duros caso a tabela ainda não tenha sido migrada
        cursor.execute('SELECT link_id FROM products LIMIT 1')
        cursor.execute('SELECT download_link FROM products LIMIT 1')
        
        # Seleciona produtos que têm download_link mas não têm link_id
        prods_to_migrate = cursor.execute('''
            SELECT id, name, download_link 
            FROM products 
            WHERE download_link IS NOT NULL 
            AND download_link != '' 
            AND link_id IS NULL
        ''').fetchall()
        
        if prods_to_migrate:
            print(f"--> Migrando {len(prods_to_migrate)} produtos legados para vínculos de links...")
            for prod in prods_to_migrate:
                dlink = prod['download_link'].strip()
                # Verifica se esse link já existe na tabela links
                existing_link = cursor.execute('SELECT id FROM links WHERE download_link = ?', (dlink,)).fetchone()
                if existing_link:
                    new_link_id = existing_link['id']
                else:
                    # Cria um novo link para essa URL
                    cursor.execute('INSERT INTO links (title, download_link) VALUES (?, ?)', 
                                (f"Link gerado: {prod['name']}", dlink))
                    new_link_id = cursor.lastrowid
                
                # Atualiza o produto com o novo link_id
                cursor.execute('UPDATE products SET link_id = ? WHERE id = ?', (new_link_id, prod['id']))
    except sqlite3.OperationalError:
        # Colunas ainda não existem ou não há produtos, ignora
        pass
    except Exception as e:
        print(f"[BD] Erro na auto-migração de links: {e}")

    # 3. Executar migração de dados de preços legados de forma idempotente e segura
    def clean_and_parse_price(price_str):
        if not price_str:
            return 0.0
        cleaned = price_str.replace('R$', '').replace('$', '').strip()
        if ',' in cleaned and '.' not in cleaned:
            cleaned = cleaned.replace(',', '.')
        elif ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace('.', '').replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    try:
        rows = cursor.execute('SELECT id, name, description, price, name_pt, description_pt, price_brl FROM products').fetchall()
        for row in rows:
            prod_id = row['id']
            name_pt = row['name_pt']
            desc_pt = row['description_pt']
            price_brl = row['price_brl']
            
            updates = {}
            if not name_pt or name_pt.strip() == "":
                updates['name_pt'] = row['name']
            if not desc_pt or desc_pt.strip() == "":
                updates['description_pt'] = row['description']
            if not price_brl or float(price_brl) == 0.0:
                legacy_price_str = row['price']
                updates['price_brl'] = clean_and_parse_price(legacy_price_str)
                
            if updates:
                set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
                values = list(updates.values())
                values.append(prod_id)
                query = f"UPDATE products SET {set_clause} WHERE id = ?"
                cursor.execute(query, values)
                print(f"--> [MIGRAÇÃO DE DADOS] Produto ID {prod_id} atualizado: {updates}")
    except sqlite3.OperationalError:
        pass
    except Exception as mig_err:
        print(f"[BD] Erro na migração de dados legados de produtos: {mig_err}")
