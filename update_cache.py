import os
import re
import time

ts = int(time.time())
template_dir = r'c:\Users\l.royo\Documents\site\templates\admin'

for root, _, files in os.walk(template_dir):
    for f in files:
        if f.endswith('.html'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            new_content = re.sub(r'\?v=\d+', f'?v={ts}', content)
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f"Updated {filepath}")
