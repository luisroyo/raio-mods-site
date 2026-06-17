from flask import Flask
from core.config import Config
from routes.public import public_bp
from routes.admin import admin_bp
from routes.client import client_bp
from database.connection import init_db
from routes.payment import payment_bp

import os
from database.orm import db

app = Flask(__name__)

# 1. Carrega as configurações (SECRET_KEY, Uploads, etc) do arquivo core/config.py
app.config.from_object(Config)

# Configura o SQLAlchemy para ORM gradual
DATABASE_URL = os.getenv('DATABASE_URL')
db_uri = None

if DATABASE_URL and (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")):
    import psycopg2
    try:
        # Tenta uma conexao rápida de teste
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=3)
        conn.close()
        db_uri = DATABASE_URL
        if db_uri.startswith("postgres://"):
            db_uri = db_uri.replace("postgres://", "postgresql://", 1)
    except Exception as e:
        print(f"[SQLAlchemy] Erro ao conectar ao PostgreSQL, fallback para SQLite: {e}")
        db_uri = None

if not db_uri:
    # Fallback para SQLite local
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_uri = f"sqlite:///{os.path.join(basedir, 'database.db')}"

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# 2. Inicializa o Banco de Dados (Executa Migrações)
# Isso garante que tabelas e colunas novas sejam criadas mesmo em produção (WSGI)
with app.app_context():
    init_db()

# 3. Registra as Rotas (Blueprints)
app.register_blueprint(public_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(client_bp)

if __name__ == '__main__':
    # 4. Roda a aplicação
    # O host='0.0.0.0' permite acessar pelo IP da rede (igual ao seu original)
    app.run(debug=True, host='0.0.0.0', port=5000)