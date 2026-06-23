let allClients = [];

document.addEventListener('DOMContentLoaded', () => {
    loadResellers();

    document.getElementById('searchInput').addEventListener('input', renderTable);
    document.getElementById('filterSelect').addEventListener('change', renderTable);
});

async function loadResellers() {
    try {
        const res = await fetch('/admin/api/resellers/list');
        const data = await res.json();
        if (data.resellers) {
            allClients = data.resellers;
            renderTable();
        } else {
            document.getElementById('resellersTableBody').innerHTML = `<tr><td colspan="5" class="text-center py-8 text-red-500">Erro: ${data.error}</td></tr>`;
        }
    } catch (e) {
        document.getElementById('resellersTableBody').innerHTML = `<tr><td colspan="5" class="text-center py-8 text-red-500">Erro de conexão</td></tr>`;
    }
}

function renderTable() {
    const tbody = document.getElementById('resellersTableBody');
    const search = document.getElementById('searchInput').value.toLowerCase();
    const filter = document.getElementById('filterSelect').value;

    let filtered = allClients.filter(c => {
        if (filter === 'resellers' && c.is_reseller !== 1) return false;
        
        const text = `${c.name} ${c.email} ${c.client_id}`.toLowerCase();
        return text.includes(search);
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-8 text-gray-500">Nenhum cliente encontrado.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(c => {
        const isReseller = c.is_reseller === 1;
        const balance = c.wallet_balance || 0;
        
        return `
        <tr class="hover:bg-gray-800/50 transition">
            <td class="px-4 py-3">
                <div class="font-semibold text-white">${c.name}</div>
                <div class="text-xs text-gray-500 font-mono">ID: ${c.client_id}</div>
            </td>
            <td class="px-4 py-3 text-xs">
                <div>${c.email}</div>
                <div class="text-gray-500">${c.phone || 'Sem telefone'}</div>
            </td>
            <td class="px-4 py-3 text-center">
                <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" class="sr-only peer" ${isReseller ? 'checked' : ''} onchange="toggleReseller(${c.id}, this.checked)">
                    <div class="w-9 h-5 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-500"></div>
                </label>
            </td>
            <td class="px-4 py-3 text-right">
                <span class="font-mono text-sm ${balance > 0 ? 'text-green-400 font-bold' : 'text-gray-500'}">R$ ${balance.toFixed(2).replace('.', ',')}</span>
            </td>
            <td class="px-4 py-3 text-center">
                <div class="flex items-center justify-center gap-2">
                    <button onclick="openBalanceModal(${c.id}, '${c.name}', ${balance})" class="p-1.5 bg-green-500/10 text-green-400 rounded hover:bg-green-500/20 transition" title="Gerenciar Saldo">
                        💰
                    </button>
                    <button onclick="openHistoryModal(${c.id})" class="p-1.5 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition" title="Ver Extrato">
                        📜
                    </button>
                </div>
            </td>
        </tr>
        `;
    }).join('');
}

async function toggleReseller(id, isChecked) {
    try {
        const res = await fetch('/admin/api/resellers/toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: id, is_reseller: isChecked ? 1 : 0})
        });
        const data = await res.json();
        if(data.success) {
            const client = allClients.find(c => c.id === id);
            if(client) client.is_reseller = isChecked ? 1 : 0;
        } else {
            alert('Erro: ' + data.error);
            renderTable();
        }
    } catch(e) {
        alert('Erro de conexão');
        renderTable();
    }
}

function openBalanceModal(id, name, currentBalance) {
    document.getElementById('balanceClientId').value = id;
    document.getElementById('balanceClientName').innerText = name;
    document.getElementById('balanceCurrent').innerText = `R$ ${currentBalance.toFixed(2).replace('.', ',')}`;
    document.getElementById('balanceAmount').value = '';
    document.getElementById('balanceDescription').value = '';
    
    setBalanceAction('add');
    
    const modal = document.getElementById('balanceModal');
    const content = document.getElementById('balanceModalContent');
    modal.classList.remove('hidden');
    setTimeout(() => {
        content.classList.remove('scale-95', 'opacity-0');
    }, 10);
}

function closeBalanceModal() {
    const modal = document.getElementById('balanceModal');
    const content = document.getElementById('balanceModalContent');
    content.classList.add('scale-95', 'opacity-0');
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}

function setBalanceAction(action) {
    document.getElementById('balanceAction').value = action;
    const btnAdd = document.getElementById('btnActionAdd');
    const btnRem = document.getElementById('btnActionRemove');
    
    if (action === 'add') {
        btnAdd.className = "flex-1 py-2 text-sm rounded-lg bg-green-500/20 text-green-400 border border-green-500 transition font-bold";
        btnRem.className = "flex-1 py-2 text-sm rounded-lg bg-gray-700 text-gray-400 border border-gray-600 transition";
    } else {
        btnRem.className = "flex-1 py-2 text-sm rounded-lg bg-red-500/20 text-red-400 border border-red-500 transition font-bold";
        btnAdd.className = "flex-1 py-2 text-sm rounded-lg bg-gray-700 text-gray-400 border border-gray-600 transition";
    }
}

async function submitBalance() {
    const id = document.getElementById('balanceClientId').value;
    const action = document.getElementById('balanceAction').value;
    const amount = document.getElementById('balanceAmount').value;
    const desc = document.getElementById('balanceDescription').value;
    
    if (!amount || amount <= 0) {
        alert('Digite um valor válido');
        return;
    }
    
    const btn = document.getElementById('btnSubmitBalance');
    btn.disabled = true;
    btn.innerText = 'Processando...';
    
    try {
        const res = await fetch('/admin/api/resellers/balance', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id, action, amount, description: desc})
        });
        const data = await res.json();
        
        if (data.success) {
            const client = allClients.find(c => c.id == id);
            if(client) client.wallet_balance = data.new_balance;
            renderTable();
            closeBalanceModal();
        } else {
            alert('Erro: ' + data.error);
        }
    } catch(e) {
        alert('Erro de conexão');
    } finally {
        btn.disabled = false;
        btn.innerText = 'Confirmar Operação';
    }
}

async function openHistoryModal(id) {
    const modal = document.getElementById('historyModal');
    modal.classList.remove('hidden');
    
    const loading = document.getElementById('historyLoading');
    const list = document.getElementById('historyList');
    
    loading.classList.remove('hidden');
    list.classList.add('hidden');
    list.innerHTML = '';
    
    try {
        const res = await fetch(`/admin/api/resellers/history/${id}`);
        const data = await res.json();
        
        if (data.history && data.history.length > 0) {
            list.innerHTML = data.history.map(h => {
                const isAdd = h.transaction_type === 'add_balance';
                const isPurchase = h.transaction_type === 'purchase';
                const date = new Date(h.created_at + 'Z').toLocaleString('pt-BR');
                
                let icon = '🔄';
                let color = 'text-gray-400';
                let sign = '';
                
                if (isAdd) { icon = '➕'; color = 'text-green-400'; sign = '+'; }
                else if (isPurchase) { icon = '🛍️'; color = 'text-red-400'; sign = '-'; }
                else { icon = '➖'; color = 'text-red-400'; sign = '-'; }
                
                return `
                <div class="bg-gray-900/50 rounded p-3 border border-gray-700 flex justify-between items-center text-sm">
                    <div>
                        <div class="text-gray-300 font-medium">${icon} ${h.description || 'Sem descrição'}</div>
                        <div class="text-xs text-gray-500">${date}</div>
                    </div>
                    <div class="font-mono font-bold ${color}">
                        ${sign} R$ ${parseFloat(h.amount).toFixed(2).replace('.', ',')}
                    </div>
                </div>`;
            }).join('');
        } else {
            list.innerHTML = '<div class="text-center text-gray-500 py-4">Nenhuma transação encontrada.</div>';
        }
    } catch(e) {
        list.innerHTML = '<div class="text-center text-red-500 py-4">Erro ao carregar extrato.</div>';
    } finally {
        loading.classList.add('hidden');
        list.classList.remove('hidden');
    }
}

function closeHistoryModal() {
    document.getElementById('historyModal').classList.add('hidden');
}

function openAddResellerModal() {
    document.getElementById('addName').value = '';
    document.getElementById('addEmail').value = '';
    document.getElementById('addPhone').value = '';
    document.getElementById('addPassword').value = '';
    
    const modal = document.getElementById('addResellerModal');
    const content = document.getElementById('addResellerModalContent');
    modal.classList.remove('hidden');
    setTimeout(() => {
        content.classList.remove('scale-95', 'opacity-0');
    }, 10);
}

function closeAddResellerModal() {
    const modal = document.getElementById('addResellerModal');
    const content = document.getElementById('addResellerModalContent');
    content.classList.add('scale-95', 'opacity-0');
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}

async function submitAddReseller(event) {
    event.preventDefault();
    const btn = document.getElementById('btnSubmitAddReseller');
    const originalText = btn.innerText;
    
    const name = document.getElementById('addName').value;
    const email = document.getElementById('addEmail').value;
    const phone = document.getElementById('addPhone').value;
    const password = document.getElementById('addPassword').value;
    
    btn.disabled = true;
    btn.innerText = 'Cadastrando...';
    
    try {
        const res = await fetch('/admin/api/resellers/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, email, phone, password})
        });
        const data = await res.json();
        
        if (data.success) {
            alert('Revendedor cadastrado com sucesso!');
            closeAddResellerModal();
            loadResellers(); // recarrega a tabela
        } else {
            alert('Erro: ' + data.error);
        }
    } catch(e) {
        alert('Erro de conexão');
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }
}
