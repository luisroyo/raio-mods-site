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
