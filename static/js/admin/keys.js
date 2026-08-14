/* =========================
   KEYS - Gerenciamento de Chaves
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
                <div>
                    <button onclick="checkKosStatus('${k.key_value}')" class="text-cyan-400 hover:text-cyan-300 ml-2" title="Verificar Status KOS">🔍</button>
                    <button onclick="deleteKey(${k.id})" class="text-red-500 hover:text-red-300 ml-2" title="Excluir">🗑️</button>
                </div>
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

async function checkKosStatus(keyValue) {
    if (!keyValue) return;
    
    // Create or show loading modal
    let modal = document.getElementById('kosStatusModal');
    if (!modal) {
        const modalHtml = `
        <div class="fixed inset-0 bg-black/90 z-[400] flex items-center justify-center p-4 backdrop-blur-sm" id="kosStatusModal">
            <div class="bg-gray-900 border-2 border-cyan-500 rounded-xl w-full max-w-sm overflow-hidden shadow-[0_0_30px_rgba(0,242,255,0.2)] relative">
                <div class="bg-cyan-500/10 p-4 border-b border-cyan-500/30 flex justify-between items-center">
                    <h3 class="text-lg font-bold text-cyan-400">🔍 Status da Chave</h3>
                    <button onclick="document.getElementById('kosStatusModal').remove()" class="text-gray-400 hover:text-white text-xl">&times;</button>
                </div>
                <div class="p-6 space-y-4 text-sm" id="kosStatusContent">
                    <div class="text-center text-cyan-400 font-bold py-4">⏳ Consultando KOS API...</div>
                </div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modal = document.getElementById('kosStatusModal');
    } else {
        document.getElementById('kosStatusContent').innerHTML = '<div class="text-center text-cyan-400 font-bold py-4">⏳ Consultando KOS API...</div>';
        modal.classList.remove('hidden');
    }

    try {
        const formData = new FormData();
        formData.append('key_value', keyValue);
        
        const res = await fetch('/admin/keys/status', { method: 'POST', body: formData });
        const data = await res.json();
        
        const content = document.getElementById('kosStatusContent');
        
        if (data.success) {
            let statusColor = data.status === 'available' ? 'text-green-400' : 
                              data.status === 'used' || data.status === 'activated' ? 'text-yellow-400' : 'text-cyan-400';
            
            content.innerHTML = `
                <div class="border border-cyan-500/20 rounded p-3 bg-black/40">
                    <p class="text-gray-400 mb-2">Chave: <span class="text-white font-mono text-xs break-all">${keyValue}</span></p>
                    <p class="text-gray-400">Status KOS: <span class="${statusColor} font-bold uppercase">${data.status}</span></p>
                    ${data.hardware_id ? `<p class="text-gray-400 mt-2">HWID: <span class="text-gray-300 font-mono text-xs break-all">${data.hardware_id}</span></p>` : ''}
                    ${data.activated_at ? `<p class="text-gray-400 mt-1">Ativado em: <span class="text-white">${new Date(data.activated_at).toLocaleString()}</span></p>` : ''}
                    ${data.expires_at ? `<p class="text-gray-400 mt-1">Expira em: <span class="text-white">${new Date(data.expires_at).toLocaleString()}</span></p>` : ''}
                </div>
            `;
        } else {
            content.innerHTML = `
                <div class="border border-red-500/20 rounded p-3 bg-red-900/20">
                    <p class="text-red-400 font-bold text-center">❌ ${data.error}</p>
                </div>
            `;
        }
    } catch (err) {
        document.getElementById('kosStatusContent').innerHTML = `
            <div class="border border-red-500/20 rounded p-3 bg-red-900/20">
                <p class="text-red-400 font-bold text-center">❌ Erro de conexão ao consultar status.</p>
            </div>
        `;
    }
}

