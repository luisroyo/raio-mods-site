def create_tables(cursor):
    """Cria todas as tabelas base do sistema, se não existirem."""
    
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
            translation_status TEXT DEFAULT "draft",
            link_id INTEGER REFERENCES links(id)
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            commission_percentage REAL DEFAULT 0.0,
            is_seller INTEGER DEFAULT 0
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
