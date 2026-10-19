import time
import ipaddress
import threading
from collections import defaultdict
from flask import request

_security_lock = threading.Lock()
_admin_attempts = defaultdict(lambda: {'count': 0, 'locked_until': 0.0, 'last_attempt': 0.0})
_otp_requests = defaultdict(float)
_otp_verify_attempts = defaultdict(lambda: {'count': 0, 'locked_until': 0.0})

def _is_valid_ip(ip_str: str) -> bool:
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except Exception:
        return False

def get_real_client_ip(req=None) -> str:
    """
    Captura o IP real do cliente com blindagem contra spoofing de X-Forwarded-For (XFF).
    O proxy reverso (PythonAnywhere/Nginx/Cloudflare) anexa o IP real no final do header
    ou define X-Real-IP / CF-Connecting-IP.
    """
    r = req or request
    if not r:
        return 'unknown'

    cf_ip = r.headers.get('CF-Connecting-IP')
    if cf_ip and _is_valid_ip(cf_ip.strip()):
        return cf_ip.strip()

    real_ip = r.headers.get('X-Real-IP')
    if real_ip and _is_valid_ip(real_ip.strip()):
        return real_ip.strip()

    xff = r.headers.get('X-Forwarded-For')
    if xff:
        parts = [p.strip() for p in xff.split(',') if p.strip()]
        for candidate in reversed(parts):
            if _is_valid_ip(candidate):
                return candidate

    return r.remote_addr or 'unknown'

def check_admin_login_rate_limit(ip: str) -> tuple[bool, str]:
    now = time.time()
    with _security_lock:
        data = _admin_attempts[ip]
        if data['locked_until'] > now:
            mins_left = int((data['locked_until'] - now) / 60) + 1
            return False, f'Acesso bloqueado por seguranca devido a muitas tentativas. Tente novamente em {mins_left} minuto(s).'
        return True, ''

def record_admin_login_attempt(ip: str, success: bool):
    now = time.time()
    with _security_lock:
        if success:
            _admin_attempts.pop(ip, None)
        else:
            data = _admin_attempts[ip]
            if now - data['last_attempt'] > 900:
                data['count'] = 0
            data['count'] += 1
            data['last_attempt'] = now
            if data['count'] >= 5:
                data['locked_until'] = now + 900

def check_otp_request_rate_limit(email: str, ip: str) -> tuple[bool, str]:
    now = time.time()
    with _security_lock:
        last_email_req = _otp_requests.get(f'email:{email}', 0.0)
        last_ip_req = _otp_requests.get(f'ip:{ip}', 0.0)
        
        if now - last_email_req < 60:
            secs = int(60 - (now - last_email_req))
            return False, f'Aguarde {secs} segundos para solicitar um novo codigo.'
        if now - last_ip_req < 30:
            secs = int(30 - (now - last_ip_req))
            return False, f'Aguarde {secs} segundos antes de tentar novamente.'
            
        _otp_requests[f'email:{email}'] = now
        _otp_requests[f'ip:{ip}'] = now
        return True, ''

def check_otp_verify_rate_limit(email: str, ip: str) -> tuple[bool, str]:
    now = time.time()
    with _security_lock:
        for key in (f'verify_email:{email}', f'verify_ip:{ip}'):
            data = _otp_verify_attempts[key]
            if data['locked_until'] > now:
                mins = int((data['locked_until'] - now) / 60) + 1
                return False, f'Muitas tentativas incorretas. Bloqueado por {mins} minuto(s).'
    return True, ''

def record_otp_verify_attempt(email: str, ip: str, success: bool):
    now = time.time()
    with _security_lock:
        keys = (f'verify_email:{email}', f'verify_ip:{ip}')
        if success:
            for k in keys:
                _otp_verify_attempts.pop(k, None)
        else:
            for k in keys:
                data = _otp_verify_attempts[k]
                data['count'] += 1
                if data['count'] >= 5:
                    data['locked_until'] = now + 900
