/* =========================
   PRODUCTS - CRUD de Produtos
========================= */

async function sendData(e, msgId) {
    e.preventDefault();
    const form = e.target;
    const url = form.dataset.url;
    const msg = document.getElementById(msgId);

    if (!url) {
        alert('Erro interno: data-url não definido');
        return;
    }

    msg && (msg.innerHTML = '⏳ Processando...', msg.classList.remove('hidden'));

    try {
        const res = await fetch(url, { method: 'POST', body: new FormData(form) });
        const text = await res.text();

        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            console.error('JSON Parse Error:', e, 'Text:', text);
            msg && (msg.innerHTML = '❌ Erro na resposta do servidor');
            return;
        }

        if (data.success) {
            msg && (msg.innerHTML = '✅ Sucesso!');
            setTimeout(() => location.reload(), 600);
        } else {
            msg && (msg.innerHTML = '❌ ' + (data.error || 'Erro'));
        }
    } catch (err) {
        console.error('Fetch Error:', err);
        msg && (msg.innerHTML = '❌ Erro: ' + err.message);
    }
}

function setupFormListeners() {
    [
        ['addCatalogForm', 'catalog_message'],
        ['addProductForm', 'message'],
        ['addLinkForm', 'link_message'],
        ['addSubproductForm', 'subproduct_message'],
        ['configForm', 'config_message']
    ].forEach(([id, msg]) => {
        const f = document.getElementById(id);
        f && f.addEventListener('submit', e => sendData(e, msg));
    });

    const editProd = document.getElementById('editProductForm');
    editProd && editProd.addEventListener('submit', e => {
        e.preventDefault();
        const id = document.getElementById('edit_id').value;
        editProd.dataset.url = `/admin/edit/${id}`;
        sendData(e, 'edit_message');
    });

    const editLink = document.getElementById('editLinkForm');
    editLink && editLink.addEventListener('submit', e => {
        e.preventDefault();
        const id = document.getElementById('link_edit_id').value;
        editLink.dataset.url = `/admin/links/edit/${id}`;
        sendData(e, 'link_edit_message');
    });
}

async function deleteProduct(id) {
    if (!confirm('Confirmar exclusão?')) return;
    await fetch(`/admin/delete/${id}`, { method: 'POST' });
    location.reload();
}
