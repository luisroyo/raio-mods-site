import sqlite3
import os

# --- Caminho Absoluto (Essencial para não criar bancos duplicados) ---
basedir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(basedir, 'database.db')

def init_db():
    print(f"🔌 Conectando ao banco em: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Tabela de Produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price TEXT NOT NULL,
            image TEXT NOT NULL,
            category TEXT NOT NULL
        )
    ''')
    
    # 2. Migração de Colunas (Adiciona o que falta sem quebrar o que existe)
    # is_catalog = 1 (É um Jogo/Capa) | is_catalog = 0 (É um produto/hack)
    new_columns = [
        ('tagline', 'TEXT DEFAULT ""'),
        ('sort_order', 'INTEGER DEFAULT 0'),
        ('parent_id', 'INTEGER NULL'),
        ('is_catalog', 'INTEGER DEFAULT 0') 
    ]

    print("🛠️ Verificando estrutura da tabela Products...")
    for col_name, col_type in new_columns:
        try:
            cursor.execute(f'SELECT {col_name} FROM products LIMIT 1')
        except sqlite3.OperationalError:
            print(f"   ➕ Adicionando coluna '{col_name}'...")
            try:
                cursor.execute(f'ALTER TABLE products ADD COLUMN {col_name} {col_type}')
            except Exception as e:
                print(f"   ❌ Erro ao adicionar {col_name}: {e}")
    
    # 3. Tabela de Links Independentes (Mantendo sua funcionalidade de Links)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            download_link TEXT,
            video_link TEXT,
            game TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados verificado e atualizado com sucesso!")

if __name__ == "__main__":
    init_db()