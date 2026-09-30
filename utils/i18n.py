import os
import json
import logging

logger = logging.getLogger("i18n")

_translations = {}

def load_translations():
    global _translations
    basedir = os.path.abspath(os.path.dirname(__file__))
    trans_dir = os.path.join(basedir, '../translations')
    
    if not os.path.exists(trans_dir):
        os.makedirs(trans_dir, exist_ok=True)
        
    path = os.path.join(trans_dir, 'pt.json')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                _translations['pt'] = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar traducao pt: {e}")
            _translations['pt'] = {}
    else:
        _translations['pt'] = {}

def get_current_language():
    return 'pt'

def get_current_currency():
    return 'BRL'

def translate(key, default=None):
    if not _translations:
        load_translations()
        
    val = _translations.get('pt', {}).get(key)
    if val is not None:
        return val
            
    return default if default is not None else key

def _(key, default=None):
    return translate(key, default)

def translate_for_lang(key, lang, default=None):
    return translate(key, default)

def get_user_lang_from_telegram(telegram_lang_code: str) -> str:
    return 'pt'

def get_currency_for_lang(lang: str) -> str:
    return 'BRL'
