from flask import Flask
from core.config import Config
from routes.public import public_bp
from routes.admin import admin_bp
from database.connection import init_db
from routes.payment import payment_bp

app = Flask(__name__)

# 1. Carrega as configurações (SECRET_KEY, Uploads, etc) do arquivo core/config.py
app.config.from_object(Config)

# 2. Inicializa o Banco de Dados (Executa Migrações)
# Isso garante que tabelas e colunas novas sejam criadas mesmo em produção (WSGI)
with app.app_context():
    init_db()

# 3. Registra as Rotas (Blueprints)
app.register_blueprint(public_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(payment_bp)

if __name__ == '__main__':
    # 4. Roda a aplicação
    # O host='0.0.0.0' permite acessar pelo IP da rede (igual ao seu original)
    app.run(debug=True, host='0.0.0.0', port=5000)