// Inicializa animações
document.addEventListener('DOMContentLoaded', () => {
    AOS.init();
    setupFormListeners();
});

// --- NAVEGAÇÃO ENTRE ABAS ---
function showSection(id) {
    document.querySelectorAll('.section-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('[id^="tab-"]').forEach(el => { 
        el.classList.remove('neon-cyan', 'border-b-2'); 
        el.classList.add('text-gray-400'); 
    });
    
    const section = document.getElementById('section-' + id);
    if(section) section.classList.remove('hidden');
    
    const tab = document.getElementById('tab-' + id);
    if(tab) {
        tab.classList.add('neon-cyan', 'border-b-2'); 
        tab.classList.remove('text-gray-400');
    }
}

// --- FUNÇÕES DE MODAL ---
function closeModal(id) { 
    document.getElementById(id).classList.remove('modal-active'); 
}

function openConfigModal() {
    document.getElementById('configModal').classList.add('modal-active');
}

function openAddSubproductModal(pid, name) {
    document.getElementById('sub_pid').value = pid;
    document.getElementById('sub_cat_name').innerText = name;
    document.getElementById('addSubproductModal').classList.add('modal-active');
}

function openEditModal(id, name, desc, price, cat, img, tagline, sort, pid, is_cat, pay_url) {
    document.getElementById('edit_id').value = id;
    document.getElementById('edit_name').value = name;
    document.getElementById('edit_description').value = desc;
    document.getElementById('edit_price').value = price;
    document.getElementById('edit_category').value = cat;
    document.getElementById('edit_is_catalog').value = is_cat;
    document.getElementById('edit_payment_url').value = pay_url || "";
    
    document.getElementById('edit_image_url').value = ""; 
    document.getElementById('edit_image').value = ""; 
    
    const preview = document.getElementById('edit_preview');
    if(img) preview.src = img;
    else preview.src = "";

    const parentDiv = document.getElementById('edit_parent_div');
    const parentSel = document.getElementById('edit_parent_id');
    
    if (is_cat == 1) { 
        parentDiv.style.display = 'none'; 
        parentSel.value = ""; 
    } else { 
        parentDiv.style.display = 'block'; 
        parentSel.value = pid || ""; 
        Array.from(parentSel.options).forEach(opt => { 
            opt.disabled = (opt.value == id); 
        }); 
    }

    document.getElementById('editModal').classList.add('modal-active');
}

function openEditLink(id, title, desc, img, down, vid, game) {
    document.getElementById('link_edit_id').value = id;
    document.getElementById('link_title').value = title || '';
    document.getElementById('link_desc').value = desc || '';
    document.getElementById('link_down').value = down || '';
    document.getElementById('link_vid').value = vid || '';
    document.getElementById('link_game').value = game || '';
    document.getElementById('link_edit_image_url').value = '';
    document.getElementById('link_edit_image').value = '';
    const preview = document.getElementById('link_edit_preview');
    preview.src = img || '';
    document.getElementById('editLinkModal').classList.add('modal-active');
}

// --- LÓGICA DE ENVIO (AJAX) ---
async function sendData(e, msgId) {
    e.preventDefault();
    const form = e.target;
    // Pega a URL definida no atributo data-url do HTML
    const url = form.getAttribute('data-url'); 
    
    if(!url) {
        alert('Erro: URL de destino não definida no formulário.');
        return;
    }

    const msg = document.getElementById(msgId);
    msg.classList.remove('hidden'); 
    msg.innerHTML = '⏳...';
    
    try {
        const res = await fetch(url, {method:'POST', body:new FormData(form)});
        const data = await res.json();
        if(data.success) { 
            msg.innerHTML = '✅ OK!'; 
            setTimeout(() => location.reload(), 500); 
        } else { 
            msg.innerHTML = '❌ ' + data.error; 
        }
    } catch (err) { 
        console.error(err);
        msg.innerHTML = '❌ Erro de conexão'; 
    }
}

// Configura os ouvintes de evento (Listeners)
function setupFormListeners() {
    const forms = [
        { id: 'addCatalogForm', msg: 'catalog_message' },
        { id: 'addProductForm', msg: 'message' },
        { id: 'addLinkForm', msg: 'link_message' },
        { id: 'addSubproductForm', msg: 'subproduct_message' },
        { id: 'configForm', msg: 'config_message' }
    ];

    forms.forEach(item => {
        const form = document.getElementById(item.id);
        if(form) {
            form.onsubmit = (e) => sendData(e, item.msg);
        }
    });
    
    // Forms de Edição (URL dinâmica é tratada aqui ou no HTML?)
    // Para edição, a URL muda com o ID. Vamos manter o listener específico para pegar o ID na hora.
    
    const editProdForm = document.getElementById('editProductForm');
    if(editProdForm) {
        editProdForm.onsubmit = (e) => {
            e.preventDefault();
            const id = document.getElementById('edit_id').value;
            // Define a URL dinamicamente antes de enviar
            editProdForm.setAttribute('data-url', `/admin/edit/${id}`);
            sendData(e, 'edit_message');
        };
    }

    const editLinkForm = document.getElementById('editLinkForm');
    if(editLinkForm) {
        editLinkForm.onsubmit = (e) => {
            e.preventDefault();
            const id = document.getElementById('link_edit_id').value;
            editLinkForm.setAttribute('data-url', `/admin/links/edit/${id}`);
            sendData(e, 'link_edit_message');
        };
    }
}

// Funções de Exclusão
async function deleteProduct(id) { 
    if(confirm('Apagar este item?')) { 
        await fetch('/admin/delete/'+id, {method:'POST'}); 
        location.reload(); 
    } 
}

async function deleteLink(id) { 
    if(confirm('Apagar este link?')) { 
        await fetch('/admin/links/delete/'+id, {method:'POST'}); 
        location.reload(); 
    } 
}