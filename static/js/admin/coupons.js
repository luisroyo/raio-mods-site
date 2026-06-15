document.addEventListener('DOMContentLoaded', () => {
    loadCoupons();
    loadSpins();
    
    document.getElementById('couponForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        saveCoupon();
    });
});

async function loadCoupons() {
    try {
        const response = await fetch('/admin/coupons/list');
        const coupons = await response.json();
        
        const tbody = document.getElementById('couponsList');
        tbody.innerHTML = '';
        
        if (coupons.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="p-8 text-center text-gray-500">Nenhum cupom cadastrado.</td></tr>';
            return;
        }
        
        coupons.forEach(c => {
            const discount = c.discount_type === 'percent' ? `${c.discount_value}%` : `R$ ${c.discount_value.toFixed(2)}`;
            const uses = c.max_uses > 0 ? `${c.current_uses} / ${c.max_uses}` : `${c.current_uses} (Ilimitado)`;
            
            let statusBadge = '<span class="bg-green-500/20 text-green-400 px-2 py-1 rounded text-xs">Ativo</span>';
            
            if (c.max_uses > 0 && c.current_uses >= c.max_uses) {
                statusBadge = '<span class="bg-red-500/20 text-red-400 px-2 py-1 rounded text-xs">Esgotado</span>';
            } else if (c.valid_until && new Date(c.valid_until) < new Date()) {
                statusBadge = '<span class="bg-red-500/20 text-red-400 px-2 py-1 rounded text-xs">Expirado</span>';
            }
            
            const expDate = c.valid_until ? new Date(c.valid_until).toLocaleDateString('pt-BR') : 'Sem validade';
            
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-gray-800/50 transition';
            tr.innerHTML = `
                <td class="p-4">
                    <div class="font-mono font-bold text-amber-400">${c.code}</div>
                    <div class="mt-1">${statusBadge}</div>
                </td>
                <td class="p-4 text-white">${discount}</td>
                <td class="p-4 text-gray-300">${uses}</td>
                <td class="p-4 text-gray-400 text-sm">${expDate}</td>
                <td class="p-4 text-right">
                    <button onclick="deleteCoupon(${c.id})" class="text-red-400 hover:text-red-300 p-2 rounded hover:bg-red-400/10 transition" title="Excluir">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error('Erro ao carregar cupons:', e);
        document.getElementById('couponsList').innerHTML = '<tr><td colspan="5" class="p-4 text-center text-red-500">Erro ao carregar.</td></tr>';
    }
}

function openAddCouponModal() {
    document.getElementById('couponForm').reset();
    document.getElementById('addCouponModal').classList.remove('hidden');
}

function closeAddCouponModal() {
    document.getElementById('addCouponModal').classList.add('hidden');
}

async function saveCoupon() {
    const formData = new FormData();
    formData.append('code', document.getElementById('couponCode').value);
    formData.append('discount_type', document.getElementById('discountType').value);
    formData.append('discount_value', document.getElementById('discountValue').value);
    formData.append('max_uses', document.getElementById('maxUses').value);
    formData.append('valid_until', document.getElementById('validUntil').value);

    try {
        const res = await fetch('/admin/coupons/add', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        if (data.success) {
            closeAddCouponModal();
            loadCoupons();
            alert('Cupom criado com sucesso!');
        } else {
            alert(data.error || 'Erro ao criar cupom');
        }
    } catch (e) {
        alert('Erro de conexão ao salvar cupom');
    }
}

async function deleteCoupon(id) {
    if(!confirm('Tem certeza que deseja apagar este cupom? Cuidado para não quebrar links divulgados.')) return;
    
    try {
        const res = await fetch(`/admin/coupons/delete/${id}`, { method: 'POST' });
        const data = await res.json();
        if(data.success) {
            loadCoupons();
        } else {
            alert(data.error || 'Erro ao deletar');
        }
    } catch (e) {
        alert('Erro ao deletar');
    }
}

async function loadSpins() {
    try {
        const response = await fetch('/admin/spins/list');
        const spins = await response.json();
        
        const tbody = document.getElementById('spinsList');
        tbody.innerHTML = '';
        
        if (spins.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="p-8 text-center text-gray-500">Nenhum giro registrado.</td></tr>';
            return;
        }
        
        spins.forEach(s => {
            const date = new Date(s.created_at).toLocaleString('pt-BR');
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-gray-800/50 transition';
            tr.innerHTML = `
                <td class="p-4 text-white font-medium">${s.email}</td>
                <td class="p-4 font-mono text-cyan-400 font-bold">${s.coupon_code}</td>
                <td class="p-4 text-emerald-400 font-bold">${s.discount_value}%</td>
                <td class="p-4 text-gray-400 text-sm">${date}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error('Erro ao carregar histórico de giros:', e);
        document.getElementById('spinsList').innerHTML = '<tr><td colspan="4" class="p-4 text-center text-red-500">Erro ao carregar.</td></tr>';
    }
}
