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

/* Auto-fill custo unitário em BRL ao selecionar produto */
document.addEventListener('DOMContentLoaded', () => {
    const prodSelect = document.querySelector('#manualSaleForm select[name="product_id"]');
    if (prodSelect) {
        prodSelect.addEventListener('change', async (e) => {
            const pid = e.target.value;
            const costInput = document.querySelector('#manualSaleForm input[name="cost_per_unit_brl"]');
            if (!pid) {
                if (costInput) costInput.value = '';
                return;
            }

            try {
                const res = await fetch(`/admin/product/info/${pid}`);
                if (!res.ok) return;
                const info = await res.json();
                if (info && typeof info.calculated_cost_brl !== 'undefined') {
                    // set value with dot as decimal separator
                    if (costInput) costInput.value = info.calculated_cost_brl.toFixed(2);
                }
            } catch (err) {
                console.error('Erro ao buscar info do produto:', err);
            }
        });
    }
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
    // Esconde todas as seções
    document.querySelectorAll('.section-content').forEach(s => s.classList.add('hidden'));

    // Reseta abas
    document.querySelectorAll('[id^="tab-"]').forEach(t => {
        t.classList.remove('neon-cyan', 'border-b-2');
        t.classList.add('text-gray-400');
    });

    // Mostra a seção desejada
    const section = document.getElementById(`section-${id}`);
    if (section) {
        section.classList.remove('hidden');

        // CORREÇÃO: Força o AOS a recalcular posições, senão o conteúdo fica invisível
        if (typeof AOS !== 'undefined') {
            setTimeout(() => AOS.refresh(), 100);
        }
    }

    // Ativa aba
    const tab = document.getElementById(`tab-${id}`);
    tab?.classList.add('neon-cyan', 'border-b-2');
    tab?.classList.remove('text-gray-400');
}


function closeModal(id) {
    const m = document.getElementById(id);
    m?.classList.remove('modal-active');
    m?.classList.add('hidden');
    m?.classList.remove('flex');
}

function openConfigModal() {
    document.getElementById('configModal')?.classList.add('modal-active');
}

function openAddSubproductModal(pid, name) {
    setVal('sub_pid', pid);
    const lbl = document.getElementById('sub_cat_name');
    if (lbl) lbl.innerText = name;

    document.getElementById('addSubproductModal')?.classList.add('modal-active');
}

/* =========================
   EDITAR PRODUTO
========================= */

function openEditModal(
    id, name, desc, price, cat, img,
    tagline, sort, pid, isCat,
    payUrl, promoPrice, promoLabel, costUsd
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
    setVal('edit_cost_usd', costUsd || 0);
    // set apply_iof checkbox if provided (backwards compatible)
    if (typeof arguments !== 'undefined' && arguments.length > 14) {
        const applyIoF = arguments[14];
        try { setVal('edit_apply_iof', applyIoF); } catch (e) { /* ignore */ }
    }
    setVal('edit_image_url', '');

    const preview = document.getElementById('edit_preview');
    if (preview) preview.src = img || '';

    const parentDiv = document.getElementById('edit_parent_div');
    const parentSel = document.getElementById('edit_parent_id');

    if (parentDiv && parentSel) {
        // Se for catálogo, esconde a opção de escolher pai
        if (isCat == 1) {
            parentDiv.style.display = 'none';
            parentSel.value = '';
        } else {
            parentDiv.style.display = 'block';
            parentSel.value = pid || '';
            // Desabilita a opção de selecionar a si mesmo como pai (evita loop)
            [...parentSel.options].forEach(o => o.disabled = o.value == id);
        }
    }

    document.getElementById('editModal')?.classList.add('modal-active');
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

    document.getElementById('editLinkModal')?.classList.add('modal-active');
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
   KEYS (GERENCIAMENTO)
========================= */

let currentKeyProductId = null;

function openKeyModal(id, name) {
    currentKeyProductId = id;
    setVal('keyProductId', id);
    document.getElementById('keyProductName').innerText = name;
    document.getElementById('keyModal')?.classList.add('modal-active');

    // Limpa mensagem anterior
    const msg = document.getElementById('key_message');
    if (msg) msg.classList.add('hidden');

    switchKeyTab('add');
}

function setupKeyForm() {
    const form = document.getElementById('addKeyForm');
    if (!form) return;

    // CORREÇÃO: Remove listener anterior clonando o elemento
    // Isso evita envios múltiplos se a função for recarregada
    const newForm = form.cloneNode(true);
    form.parentNode.replaceChild(newForm, form);

    newForm.addEventListener('submit', async e => {
        e.preventDefault();
        const msg = document.getElementById('key_message');
        try {
            const r = await fetch('/admin/keys/add', { method: 'POST', body: new FormData(newForm) });
            const d = await r.json();
            msg.innerText = d.success ? '✅ Salvo!' : '❌ ' + (d.error || 'Erro');
            msg.classList.remove('hidden');
            if (d.success) {
                newForm.reset(); // Limpa o textarea
                setTimeout(() => location.reload(), 800);
            }
        } catch {
            msg.innerText = '❌ Erro de conexão';
            msg.classList.remove('hidden');
        }
    });
}

function switchKeyTab(tab) {
    document.getElementById('view-key-add')?.classList.toggle('hidden', tab !== 'add');
    document.getElementById('view-key-list')?.classList.toggle('hidden', tab === 'add');

    // Recarrega a lista se entrar na aba list
    if (tab === 'list') {
        loadKeysList();
    }
}

async function loadKeysList() {
    const ul = document.getElementById('keys-list-ul');
    const loading = document.getElementById('keys-loading');

    if (!ul || !currentKeyProductId) return;

    ul.innerHTML = '';
    loading.classList.remove('hidden');

    try {
        const res = await fetch(`/admin/keys/list/${currentKeyProductId}`);
        const keys = await res.json();
        loading.classList.add('hidden');

        if (!keys || !keys.length) {
            ul.innerHTML = '<li class="text-gray-500 text-center py-4">Nenhuma chave cadastrada.</li>';
            return;
        }

        keys.forEach(k => {
            const li = document.createElement('li');
            li.className = "flex justify-between items-center p-2 border-b border-gray-800";

            // Visual diferente para chave usada vs livre
            const statusClass = k.is_used
                ? "text-gray-600 line-through"
                : "text-green-400 font-mono";
            const statusIcon = k.is_used ? "✅" : "🔑";

            li.innerHTML = `
                <span class="${statusClass} text-sm">${statusIcon} ${k.key_value}</span>
                <button onclick="deleteKey(${k.id})" class="text-red-500 hover:text-red-300 ml-2" title="Excluir">🗑️</button>
            `;
            ul.appendChild(li);
        });
    } catch (error) {
        loading.classList.add('hidden');
        ul.innerHTML = '<li class="text-red-500 text-center">Erro ao carregar chaves.</li>';
    }
}

async function deleteKey(id) {
    if (!confirm('Excluir chave?')) return;
    try {
        await fetch(`/admin/keys/delete/${id}`, { method: 'POST' });
        loadKeysList(); // Recarrega a lista após excluir
    } catch {
        alert("Erro ao excluir chave");
    }
}

/* =========================
   VENDAS MANUAIS
========================= */

document.getElementById('manualSaleForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
        const res = await fetch('/admin/sales/manual/add', { method: 'POST', body: formData });
        const data = await res.json();
        const msg = document.getElementById('manualSaleMessage');
        if (data.success) {
            msg.textContent = '✅ ' + data.message;
            msg.className = 'mt-4 p-2 bg-green-900/30 border border-green-500 text-green-400 rounded';
            e.target.reset();
            loadManualSales();
            loadSalesReport();
        } else {
            msg.textContent = '❌ ' + data.error;
            msg.className = 'mt-4 p-2 bg-red-900/30 border border-red-500 text-red-400 rounded';
        }
        msg.classList.remove('hidden');
    } catch (err) {
        alert('Erro: ' + err);
    }
});

let allManualSales = []; // Global store for sales

async function loadManualSales() {
    try {
        const res = await fetch('/admin/sales/manual/list');
        const sales = await res.json();
        allManualSales = sales; // Store globally
        const tbody = document.getElementById('manualSalesTable');
        
        if (sales.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="p-4 text-center text-gray-500">Nenhuma venda registrada</td></tr>';
            return;
        }
        
        tbody.innerHTML = sales.map(sale => {
            const totalVenda = (sale.quantity * sale.unit_price).toFixed(2);
            const totalCusto = (sale.quantity * sale.cost_per_unit_brl).toFixed(2);
            const lucro = (totalVenda - totalCusto).toFixed(2);
            const data = new Date(sale.created_at).toLocaleDateString('pt-BR');
            
            return `<tr class="border-b border-purple-500/30 hover:bg-purple-900/20">
                <td class="p-2">${sale.product_name}</td>
                <td class="p-2 text-center">${sale.quantity}</td>
                <td class="p-2 text-right">R$ ${sale.unit_price.toFixed(2)}</td>
                <td class="p-2 text-right">R$ ${sale.cost_per_unit_brl.toFixed(2)}</td>
                <td class="p-2 text-right font-bold text-green-400">R$ ${totalVenda}</td>
                <td class="p-2 text-right font-bold text-yellow-400">R$ ${lucro}</td>
                <td class="p-2 text-center text-xs">${data}</td>
                <td class="p-2 text-center">
                    <button onclick='openEditManualSale(${sale.id}, ${sale.product_id}, ${sale.quantity}, ${sale.unit_price.toFixed(2)}, ${sale.cost_per_unit_brl.toFixed(2)}, ${JSON.stringify(sale.notes || "")})' class="text-blue-400 hover:text-blue-300 mr-2">✏️</button>
                    <button onclick="deleteManualSale(${sale.id})" class="text-red-400 hover:text-red-300">🗑️</button>
                </td>
            </tr>`;
        }).join('');
    } catch (err) {
        console.error('Erro ao carregar vendas manuais:', err);
    }
}

function openEditManualSale(id, pid, qty, price, cost, notes) {
    document.getElementById('edit_sale_id').value = id;
    document.getElementById('edit_sale_product_id').value = pid;
    document.getElementById('edit_sale_quantity').value = qty;
    document.getElementById('edit_sale_unit_price').value = price;
    document.getElementById('edit_sale_cost').value = cost;
    document.getElementById('edit_sale_notes').value = notes || '';
    
    const modal = document.getElementById('editManualSaleModal');
    modal?.classList.remove('hidden');
    modal?.classList.add('modal-active');
}

async function deleteManualSale(id) {
    if (!confirm('Excluir esta venda?')) return;
    try {
        const res = await fetch(`/admin/sales/manual/delete/${id}`, { method: 'POST' });
        if (res.ok) {
            loadManualSales();
            loadSalesReport();
        }
    } catch {
        alert('Erro ao excluir');
    }
}

/* =========================
   RECARGAS DE PAINEL
========================= */

document.getElementById('panelRechargeForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
        const res = await fetch('/admin/panel/recharge', { method: 'POST', body: formData });
        const data = await res.json();
        const msg = document.getElementById('panelRechargeMessage');
        if (data.success) {
            msg.textContent = '✅ ' + data.message;
            msg.className = 'mt-4 p-2 bg-green-900/30 border border-green-500 text-green-400 rounded';
            e.target.reset();
            loadPanelRecharges();
            loadSalesReport();
        } else {
            msg.textContent = '❌ ' + data.error;
            msg.className = 'mt-4 p-2 bg-red-900/30 border border-red-500 text-red-400 rounded';
        }
        msg.classList.remove('hidden');
    } catch (err) {
        alert('Erro: ' + err);
    }
});

async function loadPanelRecharges() {
    try {
        const res = await fetch('/admin/panel/recharge/list');
        const recharges = await res.json();
        const tbody = document.getElementById('panelRechargesTable');

        if (recharges.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="p-4 text-center text-gray-500">Nenhuma recarga registrada</td></tr>';
            return;
        }

        tbody.innerHTML = recharges.map(r => {
            const totalBRL = (r.total_cost_usd * r.dolar_rate).toFixed(2);
            const data = new Date(r.created_at).toLocaleDateString('pt-BR');

            return `<tr class="border-b border-orange-500/30 hover:bg-orange-900/20">
                <td class="p-2 text-center">${r.quantity}</td>
                <td class="p-2 text-right">$${r.cost_per_unit_usd.toFixed(2)}</td>
                <td class="p-2 text-right font-bold text-cyan-400">$${r.total_cost_usd.toFixed(2)}</td>
                <td class="p-2 text-right">R$ ${r.dolar_rate.toFixed(2)}</td>
                <td class="p-2 text-right font-bold text-red-400">R$ ${totalBRL}</td>
                <td class="p-2 text-sm">${r.notes || '-'}</td>
                <td class="p-2 text-center text-xs">${data}</td>
                <td class="p-2 text-center"><button onclick="deletePanelRecharge(${r.id})" class="text-red-400 hover:text-red-300">🗑️</button></td>
            </tr>`;
        }).join('');
    } catch (err) {
        console.error('Erro ao carregar recargas:', err);
    }
}

async function deletePanelRecharge(id) {
    if (!confirm('Excluir esta recarga?')) return;
    try {
        const res = await fetch(`/admin/panel/recharge/delete/${id}`, { method: 'POST' });
        if (res.ok) {
            loadPanelRecharges();
            loadSalesReport();
        }
    } catch {
        alert('Erro ao excluir');
    }
}

/* =========================
   RELATÓRIO DE VENDAS
========================= */

async function loadSalesReport() {
    try {
        const res = await fetch('/admin/sales/report');
        const report = await res.json();

        const fmt = (n) => 'R$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
        const fmtUSD = (n) => '$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits: 2 });

        // Online
        document.getElementById('onlineRevenue').textContent = fmt(report.online.revenue);
        document.getElementById('onlineCount').textContent = report.online.count + ' vendas';

        // Manual
        document.getElementById('manualRevenue').textContent = fmt(report.manual.revenue);
        document.getElementById('manualCount').textContent = report.manual.count + ' vendas';

        // Totais
        const totalCount = report.online.count + report.manual.count;
        document.getElementById('totalRevenue').textContent = fmt(report.summary.total_revenue);
        document.getElementById('totalCount').textContent = totalCount + ' vendas';

        document.getElementById('totalCosts').textContent = fmt(report.summary.total_costs);

        const profitElement = document.getElementById('totalProfit');
        profitElement.textContent = fmt(report.summary.total_profit);
        profitElement.className = report.summary.total_profit >= 0
            ? 'text-2xl font-bold text-green-500'
            : 'text-2xl font-bold text-red-500';

        document.getElementById('marginProfit').textContent = report.summary.profit_margin + '%';

    } catch (err) {
        console.error('Erro ao carregar relatório:', err);
    }
}

// Carregar dados ao iniciar
window.addEventListener('load', () => {
    setTimeout(() => {
        loadManualSales();
        loadPanelRecharges();
        loadSalesReport();
    }, 500);
    
    // Event listener para o formulário de edição de venda manual
    document.getElementById('editManualSaleForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('edit_sale_id').value;
        const formData = new FormData(e.target);
        const msg = document.getElementById('editManualSaleMessage');

        try {
            const res = await fetch(`/admin/sales/manual/edit/${id}`, { method: 'POST', body: formData });
            const data = await res.json();

            if (data.success) {
                msg.textContent = '✅ ' + data.message;
                msg.className = 'mt-4 p-2 bg-green-900/30 border border-green-500 text-green-400 rounded text-center font-bold';
                setTimeout(() => {
                    closeModal('editManualSaleModal');
                    loadManualSales();
                    loadSalesReport();
                    msg.textContent = '';
                    msg.classList.add('hidden');
                }, 1000);
            } else {
                msg.textContent = '❌ ' + data.error;
                msg.className = 'mt-4 p-2 bg-red-900/30 border border-red-500 text-red-400 rounded text-center font-bold';
            }
            msg.classList.remove('hidden');
        } catch (err) {
            alert('Erro: ' + err);
        }
    });
});