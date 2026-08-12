document.addEventListener('DOMContentLoaded', () => {
    loadCommissions();
});

let commissionsData = { summary: [], history: [] };

function switchTab(tab) {
    document.getElementById('view-summary').classList.add('hidden');
    document.getElementById('view-history').classList.add('hidden');
    
    document.getElementById('tab-summary').className = 'px-4 py-2 text-gray-500 hover:text-gray-300 font-medium transition';
    document.getElementById('tab-history').className = 'px-4 py-2 text-gray-500 hover:text-gray-300 font-medium transition';
    
    document.getElementById(`view-${tab}`).classList.remove('hidden');
    document.getElementById(`tab-${tab}`).className = 'px-4 py-2 text-emerald-500 border-b-2 border-emerald-500 font-medium';
}

async function loadCommissions() {
    try {
        const response = await fetch('/admin/api/commissions/list');
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        commissionsData = data;
        renderSummary();
        renderHistory();
        
    } catch (e) {
        console.error('Erro ao carregar comissões:', e);
    }
}

function renderSummary() {
    const tbody = document.getElementById('summaryList');
    tbody.innerHTML = '';
    
    if (commissionsData.summary.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="p-8 text-center text-gray-500">Nenhum vendedor com comissões.</td></tr>';
        return;
    }
    
    commissionsData.summary.forEach(s => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-800/50 transition';
        
        const isPending = s.total_pending > 0;
        const btnClass = isPending ? 'bg-emerald-600 hover:bg-emerald-500 text-white' : 'bg-gray-700 text-gray-500 cursor-not-allowed';
        const onClick = isPending ? `onclick="payCommissions('${s.seller_coupon}')"` : '';
        
        tr.innerHTML = `
            <td class="p-4 font-mono font-bold text-gray-200">${s.seller_coupon}</td>
            <td class="p-4 text-amber-500 font-bold">R$ ${s.total_pending.toFixed(2)}</td>
            <td class="p-4 text-emerald-500 font-medium">R$ ${s.total_paid.toFixed(2)}</td>
            <td class="p-4 text-right">
                <div class="flex flex-col gap-2 items-end">
                    <button ${onClick} class="${btnClass} px-3 py-1 rounded transition-colors font-medium text-xs">
                        Pagar Pendências
                    </button>
                    <button onclick="debitCommissions('${s.seller_coupon}')" class="bg-red-900/50 hover:bg-red-800 border border-red-500 text-red-300 px-3 py-1 rounded transition-colors font-medium text-xs">
                        Debitar Saldo
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderHistory() {
    const tbody = document.getElementById('historyList');
    tbody.innerHTML = '';
    
    if (commissionsData.history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="p-8 text-center text-gray-500">Nenhum registro encontrado.</td></tr>';
        return;
    }
    
    commissionsData.history.forEach(h => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-800/50 transition';
        
        const dateStr = new Date(h.created_at.replace(' ', 'T') + 'Z').toLocaleString('pt-BR');
        
        let statusBadge = '';
        if (h.status === 'paid') {
            const paidDateStr = h.paid_at ? new Date(h.paid_at.replace(' ', 'T') + 'Z').toLocaleDateString('pt-BR') : '';
            statusBadge = `<span class="bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded text-xs">Pago (${paidDateStr})</span>`;
        } else {
            statusBadge = `<span class="bg-amber-500/20 text-amber-400 px-2 py-1 rounded text-xs">Pendente</span>`;
        }
        
        tr.innerHTML = `
            <td class="p-4 text-gray-400 text-sm">${dateStr}</td>
            <td class="p-4 font-mono text-gray-200">${h.seller_coupon}</td>
            <td class="p-4 text-gray-300 text-sm">${h.order_ref}</td>
            <td class="p-4 text-gray-300">R$ ${h.sale_amount.toFixed(2)}</td>
            <td class="p-4 text-amber-400 font-medium">R$ ${h.commission_amount.toFixed(2)}</td>
            <td class="p-4">${statusBadge}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function payCommissions(sellerCoupon) {
    if(!confirm(`Confirma o pagamento de todas as comissões pendentes para o vendedor ${sellerCoupon}? (Você já enviou o dinheiro via PIX/Transferência?)`)) return;
    
    try {
        const res = await fetch('/admin/api/commissions/pay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seller_coupon: sellerCoupon })
        });
        const data = await res.json();
        
        if (data.success) {
            alert('Sucesso! As comissões foram marcadas como pagas.');
            loadCommissions();
        } else {
            alert(data.error || 'Erro ao processar');
        }
    } catch (e) {
        alert('Erro de conexão.');
    }
}

async function debitCommissions(sellerCoupon) {
    const amountStr = prompt(`Quanto você quer debitar do saldo de ${sellerCoupon}?\n(Use ponto para centavos. Ex: 70.00)`);
    if (!amountStr) return;
    
    const amount = parseFloat(amountStr.replace(',', '.'));
    if (isNaN(amount) || amount <= 0) {
        alert('Valor inválido!');
        return;
    }
    
    if(!confirm(`Confirma o débito de R$ ${amount.toFixed(2)} do saldo pendente de ${sellerCoupon}?`)) return;
    
    try {
        const res = await fetch('/admin/api/commissions/debit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seller_coupon: sellerCoupon, amount: amount })
        });
        const data = await res.json();
        
        if (data.success) {
            alert(data.message);
            loadCommissions();
        } else {
            alert(data.error || 'Erro ao processar');
        }
    } catch (e) {
        alert('Erro de conexão.');
    }
}
