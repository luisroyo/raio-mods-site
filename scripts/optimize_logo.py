"""Script para otimizar o logo do site em múltiplos tamanhos."""
from PIL import Image
import os

img = Image.open("static/logo.png")
original_size = os.path.getsize("static/logo.png") / 1024

# 1. WebP otimizado para uso geral (512x512)
img_512 = img.resize((512, 512), Image.LANCZOS)
img_512.save("static/logo.webp", "WEBP", quality=85, method=6)

# 2. PNG otimizado menor para header (128x128)
img_128 = img.resize((128, 128), Image.LANCZOS)
img_128.save("static/logo-128.png", "PNG", optimize=True)

# 3. WebP para PWA (192x192)
img_192 = img.resize((192, 192), Image.LANCZOS)
img_192.save("static/logo-192.webp", "WEBP", quality=90, method=6)

# 4. PNG fallback para PWA (192x192)
img_192.save("static/logo-192.png", "PNG", optimize=True)

# 5. PNG para PWA grande (512x512)
img_512.save("static/logo-512.png", "PNG", optimize=True)

print(f"Original logo.png: {original_size:.1f} KB")
print(f"logo.webp (512): {os.path.getsize('static/logo.webp') / 1024:.1f} KB")
print(f"logo-128.png: {os.path.getsize('static/logo-128.png') / 1024:.1f} KB")
print(f"logo-192.webp: {os.path.getsize('static/logo-192.webp') / 1024:.1f} KB")
print(f"logo-192.png: {os.path.getsize('static/logo-192.png') / 1024:.1f} KB")
print(f"logo-512.png: {os.path.getsize('static/logo-512.png') / 1024:.1f} KB")
