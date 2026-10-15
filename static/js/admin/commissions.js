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
        const response = await fetch('/painel-mestre/api/commissions/list');
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        commissionsData = data;
        updateKPIs();
        renderSummary();
        renderHistory();
        
    } catch (e) {
        console.error('Erro ao carregar comissões:', e);
    }
}

function updateKPIs() {
    let totalPending = 0;
    let totalPaid = 0;
    
    if (commissionsData.summary && commissionsData.summary.length > 0) {
        commissionsData.summary.forEach(s => {
            totalPending += parseFloat(s.total_pending || 0);
            totalPaid += parseFloat(s.total_paid || 0);
        });
    }

    const pendingEl = document.getElementById('kpiPending');
    const paidEl = document.getElementById('kpiPaid');
    const sellersEl = document.getElementById('kpiSellers');

    if (pendingEl) pendingEl.innerText = `R$ ${totalPending.toFixed(2).replace('.', ',')}`;
    if (paidEl) paidEl.innerText = `R$ ${totalPaid.toFixed(2).replace('.', ',')}`;
    if (sellersEl) sellersEl.innerText = commissionsData.summary ? commissionsData.summary.length : 0;
}

function renderSummary() {
    const tbody = document.getElementById('summaryList');
    tbody.innerHTML = '';
    
    if (!commissionsData.summary || commissionsData.summary.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="p-8 text-center text-gray-500">Nenhum vendedor com comissões registradas.</td></tr>';
        return;
    }
    
    commissionsData.summary.forEach(s => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-800/50 transition border-b border-gray-700/30';
        
        const isPending = s.total_pending > 0;
        const btnClass = isPending ? 'bg-emerald-600 hover:bg-emerald-500 text-white' : 'bg-gray-700 text-gray-500 cursor-not-allowed';
        const onClickPay = isPending ? `onclick="payCommissions('${s.seller_coupon}')"` : '';
        const currentRate = parseFloat(s.commission_percentage || 0);
        
        tr.innerHTML = `
            <td class="p-4">
                <span class="font-mono font-bold text-gray-200 text-base">${s.seller_coupon}</span>
            </td>
            <td class="p-4">
                <div class="flex items-center gap-2">
                    <span class="bg-cyan-950/60 border border-cyan-800/80 text-cyan-300 font-bold px-2 py-0.5 rounded text-xs font-mono">
                        ${currentRate > 0 ? currentRate + '%' : 'Não config.'}
                    </span>
                    <button onclick="openRateModal('${s.seller_coupon}', ${currentRate})" class="text-cyan-400 hover:text-cyan-200 p-1 rounded hover:bg-cyan-900/30 transition text-xs" title="Editar taxa padrão do cupom">
                        ✏️
                    </button>
                </div>
            </td>
            <td class="p-4 text-center">
                <span class="bg-gray-800 px-2.5 py-1 rounded-full text-xs text-gray-300 font-semibold border border-gray-700">
                    ${s.pending_count || 0}
                </span>
            </td>
            <td class="p-4 font-bold ${isPending ? 'text-amber-400 text-base' : 'text-gray-400'}">
                R$ ${(s.total_pending || 0).toFixed(2).replace('.', ',')}
            </td>
            <td class="p-4 text-emerald-400 font-medium">
                R$ ${(s.total_paid || 0).toFixed(2).replace('.', ',')}
            </td>
            <td class="p-4 text-right">
                <div class="flex gap-2 justify-end items-center">
                    <button ${onClickPay} class="${btnClass} px-3 py-1.5 rounded-lg transition-colors font-medium text-xs shadow-sm flex items-center gap-1">
                        💳 Pagar
                    </button>
                    <button onclick="openAdjustModal('${s.seller_coupon}')" class="bg-gray-800 hover:bg-gray-700 border border-gray-600 text-gray-200 px-3 py-1.5 rounded-lg transition font-medium text-xs flex items-center gap-1" title="Adicionar bônus ou desconto">
                        ➕ Ajuste
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
    
    if (!commissionsData.history || commissionsData.history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="p-8 text-center text-gray-500">Nenhum registro de comissão encontrado.</td></tr>';
        return;
    }
    
    commissionsData.history.forEach(h => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-800/50 transition border-b border-gray-700/20';
        
        let dateStr = h.created_at;
        try {
            dateStr = new Date(h.created_at.replace(' ', 'T') + 'Z').toLocaleString('pt-BR');
        } catch (e) {}
        
        let statusBadge = '';
        const isPending = h.status === 'pending';
        if (h.status === 'paid') {
            let paidDateStr = '';
            try {
                paidDateStr = h.paid_at ? new Date(h.paid_at.replace(' ', 'T') + 'Z').toLocaleDateString('pt-BR') : '';
            } catch (e) {}
            statusBadge = `<span class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded text-xs">Pago ${paidDateStr ? '(' + paidDateStr + ')' : ''}</span>`;
        } else {
            statusBadge = `<span class="bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded text-xs font-semibold">Pendente</span>`;
        }
        
        const commAmt = parseFloat(h.commission_amount || 0);
        const saleAmt = parseFloat(h.sale_amount || 0);
        const isNegative = commAmt < 0;
        const commAmtFormatted = `${isNegative ? '-' : ''}R$ ${Math.abs(commAmt).toFixed(2).replace('.', ',')}`;

        let actionBtns = '';
        if (isPending) {
            const escapedNotes = (h.notes || '').replace(/'/g, "\\'");
            actionBtns = `
                <div class="flex items-center justify-end gap-1">
                    <button onclick="openEditCommModal(${h.id}, '${h.seller_coupon}', '${h.order_ref}', ${commAmt}, '${escapedNotes}')" class="p-1.5 text-amber-400 hover:text-amber-300 hover:bg-amber-900/30 rounded transition" title="Editar valor da comissão">
                        ✏️
                    </button>
                    <button onclick="deleteCommission(${h.id})" class="p-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/30 rounded transition" title="Excluir lançamento">
                        🗑️
                    </button>
                </div>
            `;
        } else {
            actionBtns = `<span class="text-xs text-gray-500 font-mono">-</span>`;
        }
        
        tr.innerHTML = `
            <td class="p-3 text-gray-400 text-xs">${dateStr}</td>
            <td class="p-3 font-mono font-bold text-gray-200 text-xs">${h.seller_coupon}</td>
            <td class="p-3 text-gray-300 text-xs font-mono">${h.order_ref}</td>
            <td class="p-3 text-gray-300 text-xs">${h.product_name || '-'}</td>
            <td class="p-3 text-gray-300 text-xs">R$ ${saleAmt.toFixed(2).replace('.', ',')}</td>
            <td class="p-3 font-bold text-sm ${isNegative ? 'text-red-400' : 'text-amber-400'}">
                ${commAmtFormatted}
            </td>
            <td class="p-3 text-xs text-gray-400 max-w-xs truncate" title="${h.notes || ''}">
                ${h.notes || '<span class="text-gray-600">Padrão</span>'}
            </td>
            <td class="p-3">${statusBadge}</td>
            <td class="p-3 text-right">${actionBtns}</td>
        `;
        tbody.appendChild(tr);
    });
}

/* ========================================================
   AÇÕES: Pagar, Excluir, Modais
   ======================================================== */

async function payCommissions(sellerCoupon) {
    if (!confirm(`Confirma a quitação de todas as comissões pendentes para o vendedor ${sellerCoupon}?\n\n(Certifique-se de já ter realizado a transferência via Pix)`)) return;
    
    try {
        const res = await fetch('/painel-mestre/api/commissions/pay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seller_coupon: sellerCoupon })
        });
        const data = await res.json();
        
        if (data.success) {
            alert('✅ Sucesso! As comissões foram marcadas como pagas.');
            loadCommissions();
        } else {
            alert(data.error || 'Erro ao processar');
        }
    } catch (e) {
        alert('Erro de conexão ao processar pagamento.');
    }
}

async function deleteCommission(commId) {
    if (!confirm('Deseja realmente excluir este lançamento de comissão? Esta ação não pode ser desfeita.')) return;

    try {
        const res = await fetch(`/painel-mestre/api/commissions/delete/${commId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.success) {
            alert('✅ Lançamento excluído com sucesso.');
            loadCommissions();
        } else {
            alert(data.error || 'Erro ao excluir');
        }
    } catch (e) {
        alert('Erro de conexão ao excluir.');
    }
}

/* Modal Ajuste Manual */
function openAdjustModal(sellerCoupon = '') {
    const inputSeller = document.getElementById('adj_seller');
    if (inputSeller) inputSeller.value = sellerCoupon;
    document.getElementById('adj_amount').value = '';
    document.getElementById('adj_reason').value = '';
    document.getElementById('adjustModal')?.classList.remove('hidden');
}

function closeAdjustModal() {
    document.getElementById('adjustModal')?.classList.add('hidden');
}

async function submitAdjust(e) {
    e.preventDefault();
    const seller = document.getElementById('adj_seller').value.trim();
    const type = document.getElementById('adj_type').value;
    const amount = document.getElementById('adj_amount').value;
    const reason = document.getElementById('adj_reason').value.trim();

    try {
        const res = await fetch('/painel-mestre/api/commissions/adjust', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                seller_coupon: seller,
                type: type,
                amount: amount,
                reason: reason
            })
        });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            closeAdjustModal();
            loadCommissions();
        } else {
            alert(data.error || 'Erro ao registrar ajuste');
        }
    } catch (e) {
        alert('Erro de conexão.');
    }
}

/* Modal Editar Valor de Comissão */
function openEditCommModal(id, seller, ref, currentAmount, notes) {
    document.getElementById('edit_comm_id').value = id;
    document.getElementById('edit_comm_seller').innerText = seller;
    document.getElementById('edit_comm_ref').innerText = ref;
    document.getElementById('edit_comm_amount').value = Math.abs(currentAmount).toFixed(2);
    document.getElementById('edit_comm_notes').value = notes || '';
    document.getElementById('editCommModal')?.classList.remove('hidden');
}

function closeEditCommModal() {
    document.getElementById('editCommModal')?.classList.add('hidden');
}

async function submitEditComm(e) {
    e.preventDefault();
    const id = document.getElementById('edit_comm_id').value;
    const amount = document.getElementById('edit_comm_amount').value;
    const notes = document.getElementById('edit_comm_notes').value.trim();

    try {
        const res = await fetch(`/painel-mestre/api/commissions/update/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: amount, notes: notes })
        });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            closeEditCommModal();
            loadCommissions();
        } else {
            alert(data.error || 'Erro ao atualizar comissão');
        }
    } catch (e) {
        alert('Erro de conexão.');
    }
}

/* Modal Alterar Taxa Vendedor */
function openRateModal(sellerCoupon, currentRate) {
    document.getElementById('rate_seller').value = sellerCoupon;
    document.getElementById('rate_seller_label').innerText = sellerCoupon;
    document.getElementById('rate_value').value = currentRate || '';
    document.getElementById('rateModal')?.classList.remove('hidden');
}

function closeRateModal() {
    document.getElementById('rateModal')?.classList.add('hidden');
}

async function submitRate(e) {
    e.preventDefault();
    const seller = document.getElementById('rate_seller').value;
    const rate = document.getElementById('rate_value').value;

    try {
        const res = await fetch('/painel-mestre/api/commissions/update-seller-rate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seller_coupon: seller, rate: rate })
        });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            closeRateModal();
            loadCommissions();
        } else {
            alert(data.error || 'Erro ao atualizar taxa');
        }
    } catch (e) {
        alert('Erro de conexão.');
    }
}
