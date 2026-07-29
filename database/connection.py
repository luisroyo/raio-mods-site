import sqlite3
import os

def get_db_path():
    basedir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(basedir, '../database.db')

from database.models import get_db_connection, PostgreSQLConnectionWrapper

def init_db():
    DATABASE_URL = os.getenv('DATABASE_URL')
    is_postgres_configured = DATABASE_URL and (DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://'))
    
    if is_postgres_configured:
        print("[BD] Verificando banco de dados em: PostgreSQL (Neon)")
    else:
        db_path = get_db_path()
        print(f"[BD] Verificando banco de dados em: {db_path}")
    
    conn = get_db_connection()
    is_real_postgres = isinstance(conn, PostgreSQLConnectionWrapper)
    
    if is_real_postgres:
        conn.conn.autocommit = True
    cursor = conn.cursor()
    
    if is_real_postgres:
        # Criar funções customizadas de compatibilidade com SQLite date(...)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION date(time_val timestamp, mod1 text)
        RETURNS date AS $$
        BEGIN
            RETURN (time_val + mod1::interval)::date;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION date(time_val timestamp, mod1 text, mod2 text)
        RETURNS date AS $$
        BEGIN
            RETURN (time_val + mod1::interval + mod2::interval)::date;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION date(time_str text, mod1 text)
        RETURNS date AS $$
        DECLARE
            ts timestamp;
        BEGIN
            IF time_str = 'now' THEN
                ts := CURRENT_TIMESTAMP;
            ELSE
                ts := time_str::timestamp;
            END IF;
            RETURN (ts + mod1::interval)::date;
        END;
        $$ LANGUAGE plpgsql STABLE;
        """)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION date(time_str text, mod1 text, mod2 text)
        RETURNS date AS $$
        DECLARE
            ts timestamp;
        BEGIN
            IF time_str = 'now' THEN
                ts := CURRENT_TIMESTAMP;
            ELSE
                ts := time_str::timestamp;
            END IF;
            RETURN (ts + mod1::interval + mod2::interval)::date;
        END;
        $$ LANGUAGE plpgsql STABLE;
        """)

        # Criar funções customizadas de compatibilidade com SQLite datetime(...)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION datetime(time_val timestamp)
        RETURNS timestamp AS $$
        BEGIN
            RETURN time_val;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION datetime(time_str text)
        RETURNS timestamp AS $$
        BEGIN
            IF time_str = 'now' THEN
                RETURN CURRENT_TIMESTAMP;
            ELSE
                RETURN time_str::timestamp;
            END IF;
        END;
        $$ LANGUAGE plpgsql STABLE;
        """)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION datetime(time_str text, mod1 text)
        RETURNS timestamp AS $$
        DECLARE
            ts timestamp;
        BEGIN
            IF time_str = 'now' THEN
                ts := CURRENT_TIMESTAMP;
            ELSE
                ts := time_str::timestamp;
            END IF;
            RETURN ts + mod1::interval;
        END;
        $$ LANGUAGE plpgsql STABLE;
        """)
        cursor.execute("""
        CREATE OR REPLACE FUNCTION datetime(time_val timestamp, mod1 text)
        RETURNS timestamp AS $$
        BEGIN
            RETURN time_val + mod1::interval;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """)
    
    # --- TABELAS BASE DO SISTEMA ---
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price TEXT NOT NULL,
            image TEXT NOT NULL,
            category TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            is_catalog INTEGER DEFAULT 0,
            parent_id INTEGER,
            name_pt TEXT DEFAULT "",
            name_en TEXT DEFAULT "",
            name_es TEXT DEFAULT "",
            description_pt TEXT DEFAULT "",
            description_en TEXT DEFAULT "",
            description_es TEXT DEFAULT "",
            price_brl DECIMAL(10,2) DEFAULT 0.0,
            price_usd DECIMAL(10,2) DEFAULT 0.0,
            default_currency TEXT DEFAULT "BRL",
            translation_status TEXT DEFAULT "draft"
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            image TEXT,
            download_link TEXT,
            video_link TEXT,
            game TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pix_key TEXT DEFAULT '',
            binance_wallet TEXT DEFAULT '',
            whatsapp_number TEXT DEFAULT '5519989888909'
        )
    ''')

    # 3. Tabela de Vendas Manuais (Novo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS manual_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            unit_price REAL,
            cost_per_unit_brl REAL,
            total_price REAL,
            client_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    # 4. Tabela de Recargas de Painel (Novo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS panel_recharges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quantity INTEGER,
            cost_per_unit_usd REAL,
            total_cost_usd REAL,
            dolar_rate REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- NOVAS TABELAS PARA AUTOMAÇÃO (MERCADO PAGO) ---
    
    # 1. Tabela de Chaves (O Estoque de produtos digitais)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            key_value TEXT NOT NULL,
            is_used INTEGER DEFAULT 0, -- 0 = Disponível, 1 = Vendida
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    # 2. Tabela de Pedidos (Histórico de vendas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_reference TEXT UNIQUE, -- ID do Pedido no Mercado Pago
            product_id INTEGER NOT NULL,
            customer_email TEXT NOT NULL,
            amount REAL,
            status TEXT DEFAULT 'pending', -- pending, approved, refunded
            key_assigned_id INTEGER, -- Qual chave foi entregue
            qr_code TEXT,
            qr_code_base64 TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (key_assigned_id) REFERENCES product_keys (id)
        )
    ''')
    
    # 3. Tabela de Cupons de Desconto
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_type TEXT NOT NULL, -- 'percent' ou 'fixed'
            discount_value REAL NOT NULL,
            max_uses INTEGER DEFAULT 0, -- 0 = ilimitado
            current_uses INTEGER DEFAULT 0,
            valid_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Tabela de Códigos OTP (Login do Cliente)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otp_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. Tabela de Pontos de Fidelidade
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            points INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 6. Tabela de Histórico de Pontos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            points_changed INTEGER NOT NULL,
            action_type TEXT NOT NULL, -- 'earn_online', 'earn_manual', 'redeem', 'admin_adjust', 'admin_rollback'
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 7. Tabela de Cupons de Fidelidade
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loyalty_coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            coupon_code TEXT UNIQUE NOT NULL,
            discount_value REAL NOT NULL,
            is_used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 8. Tabela de Clientes Cadastrados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 9. Tabela de Cupons de Pontos (Fidelidade Promocional)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points_coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            points_value INTEGER NOT NULL,
            max_uses_global INTEGER DEFAULT 1,
            max_uses_per_client INTEGER DEFAULT 1,
            current_uses INTEGER DEFAULT 0,
            valid_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 10. Tabela de Auditoria de Resgates de Cupons de Pontos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points_coupon_redemptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coupon_id INTEGER NOT NULL,
            client_email TEXT NOT NULL,
            redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (coupon_id) REFERENCES points_coupons (id)
        )
    ''')

    # 11. Tabela de Feedbacks/Avaliações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            client_email TEXT,
            rating INTEGER NOT NULL,
            comment TEXT NOT NULL,
            product_id INTEGER,
            status TEXT DEFAULT 'pending', -- pending, approved, rejected
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # 12. Tabela de Giros da Sorte (Lucky Spins)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lucky_spins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            discount_value REAL NOT NULL,
            coupon_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 13. Tabela de Transações de Revendedores (Histórico/Extrato)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reseller_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reseller_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL, -- 'add_balance', 'remove_balance', 'purchase'
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reseller_id) REFERENCES clients (id)
        )
    ''')
    
    # --- MIGRAÇÕES E ATUALIZAÇÕES ---

    # Seed Config (Insere configuração padrão se vazio)
    cursor.execute('SELECT count(*) FROM config')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO config (id, pix_key, binance_wallet) VALUES (1, "", "")')

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
        ('download_link', 'TEXT DEFAULT ""')
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

    # Executar migração de dados de produtos legados de forma idempotente e segura
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
                print(f"--> [MIGRAÇÃO] Produto ID {prod_id} migrado: {updates}")
    except Exception as mig_err:
        print(f"[BD] Erro na migração de dados legados de produtos: {mig_err}")

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

    conn.commit()
    conn.close()
    print("[OK] Banco de dados inicializado/atualizado com sucesso!")