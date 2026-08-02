/* =========================
   MODALS - Funções de abertura de modais
========================= */

function openConfigModal() {
    document.getElementById('configModal')?.classList.add('modal-active');
}

// Define se o item será Produto (is_catalog=0) ou Subcategoria (is_catalog=1)
function setSubproductType(type) {
    const isCatInput = document.getElementById('add_sub_is_catalog');
    if (!isCatInput) return;
    isCatInput.value = type === 'category' ? '1' : '0';
}

function openAddSubproductModal(pid, name, isCategory) {
    setVal('sub_pid', pid);
    const lbl = document.getElementById('sub_cat_name');
    if (lbl) lbl.innerText = name;

    // Ajusta o tipo padrão ao abrir
    if (typeof isCategory !== 'undefined' && isCategory) {
        const catRadio = document.querySelector('input[name="sub_item_type"][value="category"]');
        if (catRadio) catRadio.checked = true;
        setSubproductType('category');
    } else {
        const prodRadio = document.querySelector('input[name="sub_item_type"][value="product"]');
        if (prodRadio) prodRadio.checked = true;
        setSubproductType('product');
    }

    document.getElementById('addSubproductModal')?.classList.add('modal-active');
}

function openEditModal(
    id, name, desc, price, cat, img,
    tagline, sort, pid, isCat,
    payUrl, promoPrice, promoLabel, costUsd, costBrl, applyIoF, isActive, supplier, resellerPrice, downloadLink, linkId,
    namePt, nameEn, nameEs, descPt, descEn, descEs, priceBrl, priceUsd, defaultCurrency, translationStatus, platform
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
    setVal('edit_download_link', downloadLink || '');
    
    // Set link_id and update preview
    const linkSelect = document.getElementById('edit_link_id');
    if (linkSelect) {
        linkSelect.value = linkId || '';
        // trigger preview update if function exists
        if (typeof updateLinkPreview === 'function') {
            updateLinkPreview(linkSelect);
        }
    }
    setVal('edit_promo_price', promoPrice);
    setVal('edit_promo_label', promoLabel);
    setVal('edit_cost_usd', costUsd || 0);
    setVal('edit_cost_brl', costBrl || 0);
    setVal('edit_apply_iof', applyIoF !== undefined ? applyIoF : 1);
    setVal('edit_reseller_price', resellerPrice || 0);

    // isActive (default 1)
    setVal('edit_is_active', isActive !== undefined ? isActive : 1);
    setVal('edit_supplier', supplier || '');
    setVal('edit_image_url', '');

    // i18n & multi-currency fields
    setVal('edit_name_pt', namePt || '');
    setVal('edit_name_en', nameEn || '');
    setVal('edit_name_es', nameEs || '');
    setVal('edit_description_pt', descPt || '');
    setVal('edit_description_en', descEn || '');
    setVal('edit_description_es', descEs || '');
    setVal('edit_price_brl', priceBrl || 0.0);
    setVal('edit_price_usd', priceUsd || 0.0);
    setVal('edit_default_currency', defaultCurrency || 'BRL');
    setVal('edit_translation_status', translationStatus || 'draft');
    setVal('edit_platform', platform || '');

    const preview = document.getElementById('edit_preview');
    if (preview) preview.src = img || '';

    const parentDiv = document.getElementById('edit_parent_div');
    const parentSel = document.getElementById('edit_parent_id');

    if (parentDiv && parentSel) {
        parentDiv.style.display = 'block';
        parentSel.value = pid || '';
        // Desabilita a opção de selecionar a si mesmo como pai (evita loop)
        [...parentSel.options].forEach(o => o.disabled = o.value == id);
    }

    document.getElementById('editModal')?.classList.add('modal-active');
}
