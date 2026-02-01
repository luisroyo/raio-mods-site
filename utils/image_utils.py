"""
Utilitário para redimensionar e otimizar imagens no upload.
Redimensiona para max 800x800px e converte para .webp para reduzir tamanho.
"""
import os
import time

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

MAX_SIZE = (800, 800)
WEBP_QUALITY = 85


def process_upload_image(file_stream, save_dir, base_filename):
    """
    Processa imagem de upload: redimensiona para max 800x800 e converte para .webp.
    Retorna (caminho_relativo, sucesso) ou (None, False) se falhar.
    
    base_filename: nome base sem extensão (ex: "1234567890_foto")
    """
    if not PILLOW_AVAILABLE:
        return None, False
    
    try:
        img = Image.open(file_stream)
        # Converte para RGB se necessário (ex: PNG com alpha, GIF)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensiona mantendo proporção (cabe em 800x800)
        img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
        
        os.makedirs(save_dir, exist_ok=True)
        out_name = f"{base_filename}.webp"
        out_path = os.path.join(save_dir, out_name)
        img.save(out_path, 'WEBP', quality=WEBP_QUALITY, optimize=True)
        
        return f"/static/uploads/{out_name}", True
    except Exception:
        return None, False


def get_base_filename(original_filename):
    """Gera nome base: timestamp + nome sem extensão."""
    stem = os.path.splitext(os.path.basename(original_filename))[0]
    stem = stem[:50] if len(stem) > 50 else stem  # limite de tamanho
    return f"{int(time.time())}_{stem}"
