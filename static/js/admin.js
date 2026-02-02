document.addEventListener('DOMContentLoaded', () => {
    // Inicialização do AOS (Animações)
    if (typeof AOS !== 'undefined') {
        AOS.init({ duration: 800, easing: 'ease-in-out', once: true });
    }
    
    // Inicializa os ouvintes de formulário
    setupFormListeners();

    // --- MENU MOBILE (HAMBURGER) ---
    // (Se você tiver removido do HTML, isso não fará mal, mas garante que funcione se existir)
    const btnMenu = document.getElementById('btn-menu-mobile');
    const menuPanel = document.getElementById('menu-mobile');
    const overlay = document.getElementById('menu-mobile-overlay');
    const btnClose = document.getElementById('btn-close-menu');

    function openMenu() {
        if (menuPanel) menuPanel.classList.remove('translate-x-full');
        if (overlay) overlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
        if (menuPanel) menuPanel.classList.add('translate-x-full');
        if (overlay) overlay.classList.add('hidden');
        document.body.style.overflow = '';
    }

    if (btnMenu) btnMenu.addEventListener('click', openMenu);
    if (overlay) overlay.addEventListener('click', closeMenu);
    if (btnClose) btnClose.addEventListener('click', closeMenu);
    
    document.querySelectorAll('.nav-mobile-link').forEach(link => {
        link.addEventListener('click', closeMenu);
    });
});

// --- NAVEGAÇÃO ENTRE ABAS DO ADMIN ---
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

// --- FUNÇÕES DE FECHAR MODAL (GENÉRICO) ---
function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.add('modal-active'); // Remove a classe ativa se usar CSS puro
        modal.classList.add('modal-hidden'); // Garante compatibilidade
    }
}

// --- MODAIS DE CONFIG E PRODUTOS ---

function openConfigModal() {
    const m = document.getElementById('configModal');
    m.classList.remove('hidden');
    m.classList.remove('modal-hidden');
}

function openAddSubproductModal(pid, name) {
    document.getElementById('sub_pid').value = pid;
    document.getElementById('sub_cat_name').innerText = name;
    const m = document.getElementById('addSubproductModal');
    m.classList.remove('hidden');
    m.classList.remove('modal-hidden');
}

function openEditModal(id, name, desc, price, cat, img, tagline, sort, pid, is_cat, pay_url) {
    document.getElementById('edit_id').value = id;
    document.getElementById('edit_name').value = name;
    document.getElementById('edit_description').value = desc;
    document.getElementById('edit_price').value = price;
    document.getElementById('edit_category').value = cat;
    document.getElementById('edit_tagline').value = tagline || '';
    document.getElementById('edit_sort_order').value = sort !== undefined && sort !== null ? sort : 0;
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

    const m = document.getElementById('editModal');
    m.classList.remove('hidden');
    m.classList.remove('modal-hidden');
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
    
    const m = document.getElementById('editLinkModal');
    m.classList.remove('hidden');
    m.classList.remove('modal-hidden');
}

// --- LÓGICA DE ENVIO (AJAX) ---
async function sendData(e, msgId) {
    e.preventDefault();
    const form = e.target;
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
    
    const editProdForm = document.getElementById('editProductForm');
    if(editProdForm) {
        editProdForm.onsubmit = (e) => {
            e.preventDefault();
            const id = document.getElementById('edit_id').value;
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

// --- GERENCIAMENTO DE ESTOQUE (CHAVES) ---

let currentKeyProductId = null;

function openKeyModal(productId, productName) {
    currentKeyProductId = productId;
    document.getElementById('keyProductId').value = productId;
    document.getElementById('keyProductName').innerText = productName;
    document.getElementById('key_message').classList.add('hidden');
    document.getElementById('addKeyForm').reset();
    
    // Reseta para a aba de adicionar
    switchKeyTab('add');
    
    const m = document.getElementById('keyModal');
    m.classList.remove('modal-hidden');
    m.classList.remove('hidden');
}

// Enviar chaves via AJAX (Aba Adicionar)
const addKeyForm = document.getElementById('addKeyForm');
if (addKeyForm) {
    addKeyForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const btn = this.querySelector('button[type="submit"]');
        const msg = document.getElementById('key_message');
        
        btn.disabled = true;
        btn.innerText = "Salvando...";
        
        try {
            const response = await fetch('/admin/keys/add', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            msg.classList.remove('hidden');
            if (data.success) {
                msg.className = "mt-2 text-center font-bold text-green-500";
                msg.innerText = data.message;
                setTimeout(() => {
                    location.reload(); 
                }, 1000);
            } else {
                msg.className = "mt-2 text-center font-bold text-red-500";
                msg.innerText = data.error || "Erro desconhecido";
                btn.disabled = false;
                btn.innerText = "Salvar Chaves";
            }
        } catch (error) {
            msg.classList.remove('hidden');
            msg.innerText = "Erro ao conectar.";
            btn.disabled = false;
            btn.innerText = "Salvar Chaves";
        }
    });
}

// Lógica de Abas do Modal de Chaves
function switchKeyTab(tab) {
    const btnAdd = document.getElementById('tab-key-add');
    const btnList = document.getElementById('tab-key-list');
    const viewAdd = document.getElementById('view-key-add');
    const viewList = document.getElementById('view-key-list');

    if (tab === 'add') {
        btnAdd.className = "flex-1 py-3 font-bold text-yellow-500 border-b-2 border-yellow-500 bg-gray-900";
        btnList.className = "flex-1 py-3 font-bold text-gray-500 hover:text-white";
        viewAdd.classList.remove('hidden');
        viewList.classList.add('hidden');
    } else {
        btnList.className = "flex-1 py-3 font-bold text-yellow-500 border-b-2 border-yellow-500 bg-gray-900";
        btnAdd.className = "flex-1 py-3 font-bold text-gray-500 hover:text-white";
        viewList.classList.remove('hidden');
        viewAdd.classList.add('hidden');
        loadKeysList(); 
    }
}

async function loadKeysList() {
    const listUl = document.getElementById('keys-list-ul');
    const loading = document.getElementById('keys-loading');
    
    listUl.innerHTML = '';
    loading.classList.remove('hidden');

    try {
        const res = await fetch(`/admin/keys/list/${currentKeyProductId}`);
        const keys = await res.json();
        
        loading.classList.add('hidden');

        if (keys.length === 0) {
            listUl.innerHTML = '<li class="text-center text-gray-500">Nenhuma chave cadastrada.</li>';
            return;
        }

        keys.forEach(key => {
            const li = document.createElement('li');
            li.className = "flex justify-between items-center bg-gray-900 p-3 rounded border border-gray-700";
            
            // Status visual (Verde = Livre, Vermelho = Usada)
            const statusColor = key.is_used ? "text-red-500" : "text-green-500";
            const statusIcon = key.is_used ? "🔴 Vendida" : "🟢 Livre";

            li.innerHTML = `
                <div class="overflow-hidden">
                    <p class="font-mono text-white text-sm truncate">${key.key_value}</p>
                    <p class="text-xs ${statusColor} font-bold">${statusIcon}</p>
                </div>
                <button onclick="deleteKey(${key.id})" class="text-red-500 hover:text-red-300 ml-4" title="Excluir">
                    🗑️
                </button>
            `;
            listUl.appendChild(li);
        });

    } catch (error) {
        loading.innerText = "Erro ao carregar chaves.";
    }
}

async function deleteKey(keyId) {
    if (!confirm("Tem certeza que deseja apagar essa chave?")) return;

    try {
        const res = await fetch(`/admin/keys/delete/${keyId}`, { method: 'POST' });
        const data = await res.json();
        
        if (data.success) {
            loadKeysList(); // Recarrega a lista
        } else {
            alert("Erro ao excluir.");
        }
    } catch (e) {
        alert("Erro de conexão.");
    }
}