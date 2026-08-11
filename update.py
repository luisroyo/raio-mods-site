import os

p = r'c:\Users\l.royo\Documents\site\templates\admin\produtos.html'
c = open(p, encoding='utf-8').read()

# Replace all np and prod
c = c.replace(
    '{{ (np.translation_status|default("draft"))|tojson|forceescape }})\'',
    '{{ (np.translation_status|default("draft"))|tojson|forceescape }}, {{ (np.platform|default(""))|tojson|forceescape }})\''
)

c = c.replace(
    '{{ (prod.translation_status|default("draft"))|tojson|forceescape }})\'',
    '{{ (prod.translation_status|default("draft"))|tojson|forceescape }}, {{ (prod.platform|default(""))|tojson|forceescape }})\''
)

open(p, 'w', encoding='utf-8').write(c)
print("Updated successfully")
