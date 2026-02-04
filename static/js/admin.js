document.addEventListener('DOMContentLoaded', () => {

    /* =========================
       INIT
    ========================= */

    if (typeof AOS !== 'undefined') {
        AOS.init({ duration: 800, easing: 'ease-in-out', once: true });
    }

    setupFormListeners();
    setupMobileMenu();
    setupKeyForm();

});

/* =========================
   HELPERS
========================= */

function setVal(id, value) {
    const el = document.getElementById(id);
    if (!el) {
        console.warn(`Elemento #${id} não encontrado`);
        return;
    }

    if (el.type === 'checkbox') {
        el.checked = value == 1 || value === true;
    } else {
        el.value = value ?? '';
    }
}

/* =========================
   MENU MOBILE
========================= */

function setupMobileMenu() {
    const btnMenu = document.getElementById('btn-menu-mobile');
    const menuPanel = document.getElementById('menu-mobile');
    const overlay = document.getElementById('menu-mobile-overlay');
    const btnClose = document.getElementById('btn-close-menu');

    function openMenu() {
        menuPanel?.classList.remove('translate-x-full');
        overlay?.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
        menuPanel?.classList.add('translate-x-full');
        overlay?.classList.add('hidden');
        document.body.style.overflow = '';
    }

    btnMenu?.addEventListener('click', openMenu);
    overlay?.addEventListener('click', closeMenu);
    btnClose?.addEventListener('click', closeMenu);

    document.querySelectorAll('.nav-mobile-link').forEach(l =>
        l.addEventListener('click', closeMenu)
    );
}

/* =========================
   SEÇÕES / MODAIS
========================= */

function showSection(id) {
    document.querySelectorAll('.section-content').forEach(s => s.classList.add('hidden'));
    document.querySelectorAll('[id^="tab-"]').forEach(t => {
        t.classList.remove('neon-cyan', 'border-b-2');
        t.classList.add('text-gray-400');
    });

    document.getElementById(`section-${id}`)?.classList.remove('hidden');
    const tab = document.getElementById(`tab-${id}`);
    tab?.classList.add('neon-cyan', 'border-b-2');
    tab?.classList.remove('text-gray-400');
}

function closeModal(id) {
    const m = document.getElementById(id);
    m?.classList.add('hidden', 'modal-hidden');
}

function openConfigModal() {
    document.getElementById('configModal')?.classList.remove('hidden', 'modal-hidden');
}

function openAddSubproductModal(pid, name) {
    setVal('sub_pid', pid);
    const lbl = document.getElementById('sub_cat_name');
    if (lbl) lbl.innerText = name;

    document.getElementById('addSubproductModal')?.classList.remove('hidden', 'modal-hidden');
}

/* =========================
   EDITAR PRODUTO
========================= */

function openEditModal(
    id, name, desc, price, cat, img,
    tagline, sort, pid, isCat,
    payUrl, promoPrice, promoLabel
) {
    setVal('edit_id', id);
    setVal('edit_name', name);
    setVal('edit_description', desc);
    setVal('edit_price', price);
    setVal('edit_category', cat);
    setVal('edit_tagline', tagline);
    setVal('edit_sort_order', sort || 0);
    setVal('edit_is_catalog', isCat);
    setVal('edit_payment_url', payUrl);
    setVal('edit_promo_price', promoPrice);
    setVal('edit_promo_label', promoLabel);
    setVal('edit_image_url', '');

    const preview = document.getElementById('edit_preview');
    if (preview) preview.src = img || '';

    const parentDiv = document.getElementById('edit_parent_div');
    const parentSel = document.getElementById('edit_parent_id');

    if (parentDiv && parentSel) {
        if (isCat == 1) {
            parentDiv.style.display = 'none';
            parentSel.value = '';
        } else {
            parentDiv.style.display = 'block';
            parentSel.value = pid || '';
            [...parentSel.options].forEach(o => o.disabled = o.value == id);
        }
    }

    document.getElementById('editModal')?.classList.remove('hidden', 'modal-hidden');
}

/* =========================
   LINKS
========================= */

function openEditLink(id, title, desc, img, down, vid, game) {
    setVal('link_edit_id', id);
    setVal('link_title', title);
    setVal('link_desc', desc);
    setVal('link_down', down);
    setVal('link_vid', vid);
    setVal('link_game', game);
    setVal('link_edit_image_url', '');

    const preview = document.getElementById('link_edit_preview');
    if (preview) preview.src = img || '';

    document.getElementById('editLinkModal')?.classList.remove('hidden', 'modal-hidden');
}

/* =========================
   AJAX FORMS
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
        const data = await res.json();

        if (data.success) {
            msg && (msg.innerHTML = '✅ Sucesso!');
            setTimeout(() => location.reload(), 600);
        } else {
            msg && (msg.innerHTML = '❌ ' + (data.error || 'Erro'));
        }
    } catch {
        msg && (msg.innerHTML = '❌ Erro de conexão');
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

/* =========================
   DELETE
========================= */

async function deleteProduct(id) {
    if (!confirm('Confirmar exclusão?')) return;
    await fetch(`/admin/delete/${id}`, { method: 'POST' });
    location.reload();
}

async function deleteLink(id) {
    if (!confirm('Confirmar exclusão?')) return;
    await fetch(`/admin/links/delete/${id}`, { method: 'POST' });
    location.reload();
}

/* =========================
   KEYS
========================= */

let currentKeyProductId = null;

function openKeyModal(id, name) {
    currentKeyProductId = id;
    setVal('keyProductId', id);
    document.getElementById('keyProductName').innerText = name;
    document.getElementById('keyModal')?.classList.remove('hidden', 'modal-hidden');
    switchKeyTab('add');
}

function setupKeyForm() {
    const form = document.getElementById('addKeyForm');
    if (!form) return;

    form.addEventListener('submit', async e => {
        e.preventDefault();
        const msg = document.getElementById('key_message');
        try {
            const r = await fetch('/admin/keys/add', { method: 'POST', body: new FormData(form) });
            const d = await r.json();
            msg.innerText = d.success ? '✅ Salvo!' : '❌ Erro';
            msg.classList.remove('hidden');
            d.success && setTimeout(() => location.reload(), 800);
        } catch {
            msg.innerText = '❌ Erro de conexão';
            msg.classList.remove('hidden');
        }
    });
}

function switchKeyTab(tab) {
    document.getElementById('view-key-add')?.classList.toggle('hidden', tab !== 'add');
    document.getElementById('view-key-list')?.classList.toggle('hidden', tab === 'add');
    tab === 'list' && loadKeysList();
}

async function loadKeysList() {
    const ul = document.getElementById('keys-list-ul');
    const loading = document.getElementById('keys-loading');
    ul.innerHTML = '';
    loading.classList.remove('hidden');

    const res = await fetch(`/admin/keys/list/${currentKeyProductId}`);
    const keys = await res.json();
    loading.classList.add('hidden');

    if (!keys.length) {
        ul.innerHTML = '<li class="text-gray-500 text-center">Nenhuma chave.</li>';
        return;
    }

    keys.forEach(k => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span class="font-mono">${k.key_value}</span>
            <button onclick="deleteKey(${k.id})">🗑️</button>
        `;
        ul.appendChild(li);
    });
}

async function deleteKey(id) {
    if (!confirm('Excluir chave?')) return;
    await fetch(`/admin/keys/delete/${id}`, { method: 'POST' });
    loadKeysList();
}
