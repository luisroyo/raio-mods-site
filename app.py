from flask import Flask
from core.config import Config
from routes.public import public_bp
from routes.admin import admin_bp
from database.connection import init_db
from routes.payment import payment_bp

app = Flask(__name__)

# 1. Carrega as configurações (SECRET_KEY, Uploads, etc) do arquivo core/config.py
app.config.from_object(Config)

# 2. Registra as Rotas (Blueprints)
app.register_blueprint(public_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(payment_bp)

if __name__ == '__main__':
    # 3. Inicializa/Verifica o banco de dados antes de rodar
    with app.app_context():
        init_db() 
    
    # 4. Roda a aplicação
    # O host='0.0.0.0' permite acessar pelo IP da rede (igual ao seu original)
    app.run(debug=True, host='0.0.0.0', port=5000)