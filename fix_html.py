import os

template_dir = r'c:\Users\l.royo\Documents\site\templates\admin'

for root, _, files in os.walk(template_dir):
    for f in files:
        if f.endswith('.html'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Replace backtick strings in inline scripts
            new_content = content.replace('`/admin/', '`/painel-mestre/')
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f"Fixed {filepath}")
