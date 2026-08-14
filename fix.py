import re

with open('templates/admin/produtos.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the broken quotes
text = text.replace('default("))', 'default(""))')
text = text.replace('default())', 'default(""))')

with open('templates/admin/produtos.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Fixed!")
