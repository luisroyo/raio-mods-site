/* =========================
   MODALS - Funções de abertura de modais
========================= */

function openConfigModal() {
    document.getElementById('configModal')?.classList.add('modal-active');
}

function openAddSubproductModal(pid, name) {
    setVal('sub_pid', pid);
    const lbl = document.getElementById('sub_cat_name');
    if (lbl) lbl.innerText = name;

    document.getElementById('addSubproductModal')?.classList.add('modal-active');
}

function openEditModal(
    id, name, desc, price, cat, img,
    tagline, sort, pid, isCat,
    payUrl, promoPrice, promoLabel, costUsd, applyIoF, isActive
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
    setVal('edit_apply_iof', applyIoF !== undefined ? applyIoF : 1);

    // isActive (default 1)
    setVal('edit_is_active', isActive !== undefined ? isActive : 1);
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

function switchConfigTab(tab) {
    // Esconde todos
    document.getElementById('view-config-payment').classList.add('hidden');
    document.getElementById('view-config-system').classList.add('hidden');

    // Mostra o selecionado
    document.getElementById('view-config-' + tab).classList.remove('hidden');

    // Atualiza botões
    const btnPay = document.getElementById('tab-config-payment');
    const btnSys = document.getElementById('tab-config-system');

    if (tab === 'payment') {
        btnPay.classList.add('border-yellow-500', 'bg-gray-900', 'text-yellow-500');
        btnPay.classList.remove('text-gray-500');

        btnSys.classList.remove('border-yellow-500', 'bg-gray-900', 'text-yellow-500');
        btnSys.classList.add('text-gray-500');
    } else {
        btnSys.classList.add('border-yellow-500', 'bg-gray-900', 'text-yellow-500');
        btnSys.classList.remove('text-gray-500');

        btnPay.classList.remove('border-yellow-500', 'bg-gray-900', 'text-yellow-500');
        btnPay.classList.add('text-gray-500');
    }
}
