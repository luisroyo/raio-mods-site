import os
import json
import logging
from flask import request, session

logger = logging.getLogger("i18n")

_translations = {}

def load_translations():
    global _translations
    basedir = os.path.abspath(os.path.dirname(__file__))
    trans_dir = os.path.join(basedir, '../translations')
    
    # Ensure directory exists
    if not os.path.exists(trans_dir):
        os.makedirs(trans_dir, exist_ok=True)
        
    for lang in ['pt', 'en', 'es']:
        path = os.path.join(trans_dir, f'{lang}.json')
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    _translations[lang] = json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar traducao {lang}: {e}")
                _translations[lang] = {}
        else:
            _translations[lang] = {}

def get_current_language():
    # 1. Manually selected language (URL parameter)
    lang = request.args.get('lang')
    if lang in ['pt', 'en', 'es']:
        session['lang'] = lang
        return lang
        
    # 2. Manual language in session
    lang = session.get('lang')
    if lang in ['pt', 'en', 'es']:
        return lang
        
    # 3. Manual language in cookie
    lang = request.cookies.get('lang')
    if lang in ['pt', 'en', 'es']:
        session['lang'] = lang
        return lang
        
    # 4. Accept-Language header
    accept = request.headers.get('Accept-Language', '')
    if accept:
        for part in accept.split(','):
            loc = part.split(';')[0].strip().lower()
            if loc.startswith('pt'):
                return 'pt'
            elif loc.startswith('en'):
                return 'en'
            elif loc.startswith('es'):
                return 'es'
                
    # 5. Default fallback
    return 'pt'

def get_current_currency():
    try:
        # Check if inside request context
        if not request:
            return 'BRL'
        # 1. Manually selected currency (URL parameter)
        curr = request.args.get('currency')
        if curr in ['BRL', 'USD']:
            session['currency'] = curr
            return curr
            
        # 2. Manual currency in session
        curr = session.get('currency')
        if curr in ['BRL', 'USD']:
            return curr
            
        # 3. Manual currency in cookie
        curr = request.cookies.get('currency')
        if curr in ['BRL', 'USD']:
            session['currency'] = curr
            return curr
            
        # 4. Default currency based on active language
        lang = get_current_language()
        return 'BRL' if lang == 'pt' else 'USD'
    except RuntimeError:
        return 'BRL'

def translate(key, default=None):
    # Load if not loaded yet
    if not _translations:
        load_translations()
        
    lang = get_current_language()
    trans = _translations.get(lang, {})
    val = trans.get(key)
    if val is not None:
        return val
        
    # Fallback to pt if key is missing in active language
    if lang != 'pt':
        val_pt = _translations.get('pt', {}).get(key)
        if val_pt is not None:
            return val_pt
            
    return default if default is not None else key

def _(key, default=None):
    """Proxy function for translation helper."""
    try:
        # Check if inside request context
        if not request:
            return default if default is not None else key
        return translate(key, default)
    except RuntimeError:
        # Outside request context (e.g. CLI, bot startups)
        # Fallback to loading and checking pt default translation
        if not _translations:
            load_translations()
        val_pt = _translations.get('pt', {}).get(key)
        if val_pt is not None:
            return val_pt
        return default if default is not None else key
