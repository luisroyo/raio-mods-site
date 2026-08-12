import sqlite3

def run_schema_migrations(cursor, is_real_postgres):
    """Executa apenas migrações estruturais (adicionando novas colunas e tabelas)."""
    
    # Lista de colunas para verificar/adicionar em PRODUCTS
    new_columns_products = [
        ('tagline', 'TEXT DEFAULT ""'),
        ('sort_order', 'INTEGER DEFAULT 0'),
        ('parent_id', 'INTEGER NULL'),
        ('is_catalog', 'INTEGER DEFAULT 0'),
        ('payment_url', 'TEXT DEFAULT ""'),
        ('promo_price', 'TEXT DEFAULT ""'),
        ('promo_label', 'TEXT DEFAULT ""'),
        ('cost_usd', 'REAL DEFAULT 0'),
        ('cost_brl', 'REAL DEFAULT 0'),
        ('apply_iof', 'INTEGER DEFAULT 1'),
        ('is_active', 'INTEGER DEFAULT 1'),
        ('supplier', 'TEXT DEFAULT ""'),
        ('reseller_price', 'REAL DEFAULT 0'),
        ('download_link', 'TEXT DEFAULT ""'),
        ('pays_commission', 'INTEGER DEFAULT 1')
    ]

    for col_name, col_type in new_columns_products:
        try:
            cursor.execute(f'SELECT {col_name} FROM products LIMIT 1')
        except sqlite3.OperationalError:
            try:
                print(f"--> Adicionando coluna {col_name} em products...")
                cursor.execute(f'ALTER TABLE products ADD COLUMN {col_name} {col_type}')
            except: pass

    # Migração config: PIX Copia e Cola
    try:
        cursor.execute('SELECT pix_copia_cola FROM config LIMIT 1')
    except sqlite3.OperationalError:
        try:
            cursor.execute('ALTER TABLE config ADD COLUMN pix_copia_cola TEXT DEFAULT ""')
        except: pass

    # --- MIGRAÇÃO: Colunas de Revendedor (clients) ---
    reseller_columns = [
        ('is_reseller', 'INTEGER DEFAULT 0'),
        ('wallet_balance', 'REAL DEFAULT 0.0')
    ]
    for col_name, col_type in reseller_columns:
        try:
            cursor.execute(f'SELECT {col_name} FROM clients LIMIT 1')
        except sqlite3.OperationalError:
            try:
                print(f"--> Adicionando coluna {col_name} em clients...")
                cursor.execute(f'ALTER TABLE clients ADD COLUMN {col_name} {col_type}')
            except: pass

    # Migração config: Token do Mercado Pago (NOVO)
    try:
        cursor.execute('SELECT mercado_pago_token FROM config LIMIT 1')
    except sqlite3.OperationalError:
        try:
            print("--> Adicionando suporte a Mercado Pago na config...")
            cursor.execute('ALTER TABLE config ADD COLUMN mercado_pago_token TEXT DEFAULT ""')
        except: pass

    # Migração config: WhatsApp Suporte
    try:
        cursor.execute('SELECT contact_whatsapp FROM config LIMIT 1')
    except sqlite3.OperationalError:
        try:
            cursor.execute('ALTER TABLE config ADD COLUMN contact_whatsapp TEXT DEFAULT ""')
        except: pass

    # Migração links: Imagem
    try:
        cursor.execute('SELECT image FROM links LIMIT 1')
    except sqlite3.OperationalError:
        try:
            cursor.execute('ALTER TABLE links ADD COLUMN image TEXT')
        except: pass

    # --- MIGRAÇÃO: Colunas de Proteção Anti-Chargeback (orders) ---
    chargeback_columns = [
        ('customer_name', 'TEXT DEFAULT ""'),
        ('customer_cpf', 'TEXT DEFAULT ""'),
        ('customer_phone', 'TEXT DEFAULT ""'),
        ('ip_purchase', 'TEXT DEFAULT ""'),
        ('ip_delivery', 'TEXT DEFAULT ""'),
        ('terms_accepted_at', 'TIMESTAMP'),
        ('delivered_at', 'TIMESTAMP'),
        ('user_agent_delivery', 'TEXT DEFAULT ""'),
        ('key_hash', 'TEXT DEFAULT ""'),
        ('recovery_email_sent', 'INTEGER DEFAULT 0'),
        ('telegram_id', 'TEXT DEFAULT ""'),
        ('telegram_username', 'TEXT DEFAULT ""'),
        ('telegram_first_name', 'TEXT DEFAULT ""'),
        ('telegram_delivery_status', 'TEXT DEFAULT ""'),
        ('telegram_delivered_at', 'TIMESTAMP'),
        ('telegram_message_id', 'TEXT DEFAULT ""'),
        ('telegram_delivery_error', 'TEXT DEFAULT ""')
    ]
    
    # Obter colunas existentes de forma segura e idempotente
    existing_columns = []
    if is_real_postgres:
        try:
            for col_name, _ in chargeback_columns:
                try:
                    cursor.execute(f'SELECT {col_name} FROM orders LIMIT 1')
                    existing_columns.append(col_name.lower())
                except:
                    pass
        except:
            pass
    else:
        try:
            pragma_rows = cursor.execute('PRAGMA table_info(orders)').fetchall()
            existing_columns = [row['name'].lower() for row in pragma_rows]
        except Exception as e:
            print(f"[BD] Erro ao carregar PRAGMA table_info: {e}")

    for col_name, col_type in chargeback_columns:
        if col_name.lower() not in existing_columns:
            try:
                print(f"--> Adicionando coluna {col_name} em orders...")
                cursor.execute(f'ALTER TABLE orders ADD COLUMN {col_name} {col_type}')
            except Exception as e:
                print(f"[BD] Erro ao adicionar coluna {col_name} em orders: {e}")

    # --- MIGRAÇÃO: Colunas de SMTP (config) ---
    smtp_columns = [
        ('smtp_server', 'TEXT DEFAULT ""'),
        ('smtp_port', 'INTEGER DEFAULT 587'),
        ('smtp_user', 'TEXT DEFAULT ""'),
        ('smtp_password', 'TEXT DEFAULT ""')
    ]
    for col_name, col_type in smtp_columns:
        try:
            cursor.execute(f'SELECT {col_name} FROM config LIMIT 1')
        except sqlite3.OperationalError:
            try:
                print(f"--> Adicionando coluna {col_name} em config...")
                cursor.execute(f'ALTER TABLE config ADD COLUMN {col_name} {col_type}')
            except: pass

    # --- MIGRAÇÃO: Colunas de Promoção Global (config) ---
    promo_columns = [
        ('global_discount_type', "TEXT DEFAULT 'percent'"),
        ('global_discount_value', 'REAL DEFAULT 0.0'),
        ('global_discount_expiry', "TEXT DEFAULT ''"),
        ('global_discount_label', "TEXT DEFAULT 'PROMO'")
    ]
    for col_name, col_type in promo_columns:
        try:
            cursor.execute(f'SELECT {col_name} FROM config LIMIT 1')
        except sqlite3.OperationalError:
            try:
                print(f"--> Adicionando coluna {col_name} em config...")
                cursor.execute(f'ALTER TABLE config ADD COLUMN {col_name} {col_type}')
            except: pass

    # --- MIGRAÇÃO: Renomear notes para client_name na tabela manual_sales ---
    try:
        cursor.execute('SELECT client_name FROM manual_sales LIMIT 1')
    except sqlite3.OperationalError:
        try:
            cursor.execute('SELECT notes FROM manual_sales LIMIT 1')
            print("--> Renomeando coluna notes para client_name na tabela manual_sales...")
            cursor.execute('ALTER TABLE manual_sales RENAME COLUMN notes TO client_name')
        except sqlite3.OperationalError:
            pass

    # --- MIGRAÇÃO: Adicionar coluna client_email na tabela manual_sales ---
    try:
        cursor.execute('SELECT client_email FROM manual_sales LIMIT 1')
    except sqlite3.OperationalError:
        try:
            print("--> Adicionando coluna client_email em manual_sales...")
            cursor.execute('ALTER TABLE manual_sales ADD COLUMN client_email TEXT DEFAULT ""')
        except Exception as e:
            print(f"Erro ao adicionar coluna client_email: {e}")

    # --- MIGRAÇÃO: Adicionar colunas status e paid_amount na tabela manual_sales ---
    manual_sales_columns = [
        ('status', "TEXT DEFAULT 'paid'"),
        ('paid_amount', 'REAL DEFAULT 0.0')
    ]
    for col_name, col_type in manual_sales_columns:
        try:
            cursor.execute(f'SELECT {col_name} FROM manual_sales LIMIT 1')
        except sqlite3.OperationalError:
            try:
                print(f"--> Adicionando coluna {col_name} em manual_sales...")
                cursor.execute(f'ALTER TABLE manual_sales ADD COLUMN {col_name} {col_type}')
            except Exception as e:
                print(f"Erro ao adicionar coluna {col_name}: {e}")

    # --- MIGRAÇÃO: Colunas de Internacionalização/Multi-Moeda (products) ---
    product_i18n_columns = [
        ('name_pt', 'TEXT DEFAULT ""'),
        ('name_en', 'TEXT DEFAULT ""'),
        ('name_es', 'TEXT DEFAULT ""'),
        ('description_pt', 'TEXT DEFAULT ""'),
        ('description_en', 'TEXT DEFAULT ""'),
        ('description_es', 'TEXT DEFAULT ""'),
        ('price_brl', 'DECIMAL(10,2) DEFAULT 0.0'),
        ('price_usd', 'DECIMAL(10,2) DEFAULT 0.0'),
        ('default_currency', "TEXT DEFAULT 'BRL'"),
        ('translation_status', "TEXT DEFAULT 'draft'")
    ]
    
    # Obter colunas existentes de produtos de forma segura
    existing_prod_columns = []
    if is_real_postgres:
        try:
            for col_name, _ in product_i18n_columns:
                try:
                    cursor.execute(f'SELECT {col_name} FROM products LIMIT 1')
                    existing_prod_columns.append(col_name.lower())
                except:
                    pass
        except:
            pass
    else:
        try:
            pragma_rows = cursor.execute('PRAGMA table_info(products)').fetchall()
            existing_prod_columns = [row['name'].lower() for row in pragma_rows]
        except Exception as e:
            print(f"[BD] Erro ao carregar PRAGMA table_info(products): {e}")

    for col_name, col_type in product_i18n_columns:
        if col_name.lower() not in existing_prod_columns:
            try:
                print(f"--> Adicionando coluna {col_name} em products...")
                cursor.execute(f'ALTER TABLE products ADD COLUMN {col_name} {col_type}')
            except Exception as e:
                print(f"[BD] Erro ao adicionar coluna {col_name} em products: {e}")

    # --- MIGRAÇÃO: Vínculo Relacional de Links de Download (products.link_id) ---
    if 'link_id' not in existing_prod_columns:
        try:
            print("--> Adicionando coluna link_id em products...")
            cursor.execute('ALTER TABLE products ADD COLUMN link_id INTEGER REFERENCES links(id)')
        except Exception as e:
            print(f"[BD] Erro ao adicionar coluna link_id: {e}")
            
    # Cria o índice de link_id
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_link_id ON products(link_id)')
    except Exception as e:
        print(f"[BD] Erro ao criar índice idx_products_link_id: {e}")

    # --- MIGRAÇÃO: Adicionar coluna used_by_email na tabela product_keys ---
    try:
        cursor.execute('SELECT used_by_email FROM product_keys LIMIT 1')
    except sqlite3.OperationalError:
        try:
            print("--> Adicionando coluna used_by_email em product_keys...")
            cursor.execute('ALTER TABLE product_keys ADD COLUMN used_by_email TEXT DEFAULT ""')
        except Exception as e:
            print(f"Erro ao adicionar coluna used_by_email: {e}")

    # --- MIGRAÇÃO: Google Analytics (config) ---
    try:
        cursor.execute('SELECT google_analytics_id FROM config LIMIT 1')
    except sqlite3.OperationalError:
        try:
            print("--> Adicionando google_analytics_id na config...")
            cursor.execute('ALTER TABLE config ADD COLUMN google_analytics_id TEXT DEFAULT ""')
        except: pass

    # --- MIGRAÇÃO: Colunas de Cupons e i18n (orders) ---
    orders_new_cols = [
        ('coupon_id', 'INTEGER'),
        ('coupon_code', 'TEXT DEFAULT ""'),
        ('discount_type', 'TEXT DEFAULT ""'),
        ('discount_value', 'REAL DEFAULT 0.0'),
        ('discount_applied', 'REAL DEFAULT 0.0'),
        ('subtotal', 'REAL DEFAULT 0.0'),
        ('total', 'REAL DEFAULT 0.0'),
        ('language', "TEXT DEFAULT 'pt'"),
        ('currency', "TEXT DEFAULT 'BRL'")
    ]
    
    existing_ord_cols = []
    if is_real_postgres:
        try:
            for col_name, _ in orders_new_cols:
                try:
                    cursor.execute(f'SELECT {col_name} FROM orders LIMIT 1')
                    existing_ord_cols.append(col_name.lower())
                except:
                    pass
        except:
            pass
    else:
        try:
            pragma_rows = cursor.execute('PRAGMA table_info(orders)').fetchall()
            existing_ord_cols = [row['name'].lower() for row in pragma_rows]
        except Exception as e:
            print(f"[BD] Erro ao carregar PRAGMA table_info(orders): {e}")

    for col_name, col_type in orders_new_cols:
        if col_name.lower() not in existing_ord_cols:
            try:
                print(f"--> Adicionando coluna {col_name} em orders...")
                cursor.execute(f'ALTER TABLE orders ADD COLUMN {col_name} {col_type}')
            except Exception as e:
                print(f"[BD] Erro ao adicionar coluna {col_name} em orders: {e}")
