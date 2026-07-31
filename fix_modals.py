with open('templates/admin/_modals.html', 'a', encoding='utf-8') as f:
    f.write('''
<script>
function updateLinkPreview(selectElement) {
    const previewEl = selectElement.nextElementSibling;
    if (!previewEl || !previewEl.classList.contains('link-preview-text')) return;
    
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    const url = selectedOption.getAttribute('data-url');
    
    if (url && url.trim() !== '') {
        previewEl.innerHTML = '<span class="text-blue-400">URL:</span> ' + url;
    } else {
        previewEl.innerText = 'Nenhum link selecionado ou link não possui URL';
    }
}
</script>
''')
