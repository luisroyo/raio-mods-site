import os
import re

base_dir = r"c:\Users\l.royo\Documents\site"
old_dir = os.path.join(base_dir, "telegram")
new_dir = os.path.join(base_dir, "telegram_app")

if os.path.exists(old_dir):
    os.rename(old_dir, new_dir)
    print(f"Renamed {old_dir} to {new_dir}")

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # We want to replace "from telegram." with "from telegram_app."
    # and "from telegram_app import telegram_bp" with "from telegram_app import telegram_bp"
    
    new_content = re.sub(r'from telegram\.(routes|config|bot|services|repositories|utils|data|constants|messages|keyboards)', r'from telegram_app.\1', content)
    new_content = re.sub(r'from telegram_app import telegram_bp', r'from telegram_app import telegram_bp', new_content)
    new_content = re.sub(r'import telegram\.', r'import telegram_app.', new_content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, _, files in os.walk(base_dir):
    if '.git' in root or '__pycache__' in root or '.venv' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                replace_in_file(filepath)
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
