import sqlite3

def init_db():
    """Inicializa o banco de dados SQLite (cria o arquivo e tabelas se não existirem)"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 1. Criar tabela de Produtos
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
    
    # 1.1. Migration: coluna tagline (frase de destaque opcional no card)
    try:
        cursor.execute('ALTER TABLE products ADD COLUMN tagline TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass  # coluna já existe
    
    # 2. Criar tabela de Links Independentes (NOVO)
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
    
    # Verificar se a tabela de produtos está vazia para inserir teste
    cursor.execute('SELECT count(*) FROM products')
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.execute('''
            INSERT INTO products (name, description, price, image, category)
            VALUES (?, ?, ?, ?, ?)
        ''', ('8 Ball Pool VIP', 'Linhas longas e antecipação.', 'R$ 49,90', '8ball.jpg', 'Mod'))
        print("Dados de teste inseridos!")
        
    conn.commit()
    conn.close()
    print("Banco de dados SQLite inicializado com sucesso!")

if __name__ == "__main__":
    init_db()