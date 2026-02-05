"""
Helpers - Funções auxiliares para rotas admin
(dólar, upload, cache)
"""
from flask import current_app, session, jsonify
from werkzeug.utils import secure_filename
from utils.image_utils import process_upload_image, get_base_filename
import os
import time
import requests
import logging
import json

# Cache file for dolar rate
CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'dolar_cache.json')

# IDs legados de catálogos (para compatibilidade)
legacy_catalog_ids = [1, 2, 3]

# Constantes financeiras
IOF = 1.0638  # 6.38%
CUSTO_FIXO_PAINEL_USD = 50.0


def get_dolar_logger():
    logger = logging.getLogger('dolar')
    if not logger.handlers:
        log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'dolar.log')
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def _read_cache():
    try:
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def _write_cache(rate):
    try:
        payload = {'rate': float(rate), 'ts': time.time()}
        with open(CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(payload, f)
    except Exception:
        pass


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def get_dolar_hoje():
    """
    Consulta a cotação atual do dólar em tempo real via API AwesomeAPI.
    Retorna o valor 'bid' (compra) como float.
    Em caso de erro, retorna valor padrão de segurança (5.50).
    """
    logger = get_dolar_logger()

    # Try cache first (valid for 10 minutes)
    try:
        cached = _read_cache()
        if cached and 'rate' in cached and 'ts' in cached:
            age = time.time() - float(cached['ts'])
            if age < 600:  # 10 minutes
                logger.info(f"Usando cotacao em cache (age={int(age)}s): R$ {float(cached['rate']):.4f}")
                return float(cached['rate'])
    except Exception:
        pass

    apis = [
        ('https://economia.awesomeapi.com.br/last/USD-BRL', 'USDBRL', 'bid'),
        ('https://api.exchangerate-api.com/v4/latest/USD', 'rates', 'BRL'),
    ]

    for api_url, key1, key2 in apis:
        try:
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if key1 in data:
                    if isinstance(data[key1], dict) and key2 in data[key1]:
                        bid = float(data[key1][key2])
                        msg = f"[OK] Dolar atualizado via {api_url}: R$ {bid:.4f}"
                        logger.info(msg)
                        _write_cache(bid)
                        return bid
        except Exception as e:
            logger.error(f"[ERRO] Falha ao consultar dolar em {api_url}: {e}")
            continue

    # Se todas as APIs falharem, tentar retornar cache mesmo que velho
    cached = _read_cache()
    if cached and 'rate' in cached:
        logger.warning("Todas as APIs falharam; usando cache existente")
        return float(cached['rate'])

    logger.warning("Todas as APIs falharam e nao ha cache; usando valor padrao: 5.50")
    return 5.50


def require_admin(f):
    """Decorador para verificar se admin está logado"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'error': '401'}), 401
        return f(*args, **kwargs)
    return decorated_function


def handle_image_upload(request, existing_image=''):
    """Processa upload de imagem, retorna caminho da imagem"""
    image = request.form.get('image_url', '') or existing_image
    
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            base_name = get_base_filename(secure_filename(file.filename))
            uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            img_path, ok = process_upload_image(file.stream, uploads_dir, base_name)
            if ok:
                image = img_path
            else:
                fname = f"{int(time.time())}_{secure_filename(file.filename)}"
                file.seek(0)
                file.save(os.path.join(uploads_dir, fname))
                image = f"/static/uploads/{fname}"
    
    return image
