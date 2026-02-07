/* =========================
   RECHARGES - Recargas de Painel
========================= */

function setupPanelRechargeForm() {
    document.getElementById('panelRechargeForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        try {
            const res = await fetch('/admin/panel/recharge', { method: 'POST', body: formData });
            const data = await res.json();
            const msg = document.getElementById('panelRechargeMessage');
            if (data.success) {
                msg.textContent = '✅ ' + data.message;
                msg.className = 'mt-4 p-2 bg-green-900/30 border border-green-500 text-green-400 rounded';
                e.target.reset();
                loadPanelRecharges();
                loadSalesReport();
            } else {
                msg.textContent = '❌ ' + data.error;
                msg.className = 'mt-4 p-2 bg-red-900/30 border border-red-500 text-red-400 rounded';
            }
            msg.classList.remove('hidden');
        } catch (err) {
            alert('Erro: ' + err);
        }
    });

    document.getElementById('editPanelRechargeForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('edit_recharge_id').value;
        const formData = new FormData(e.target);
        const msg = document.getElementById('editRechargeMessage');

        try {
            const res = await fetch(`/admin/panel/recharge/edit/${id}`, { method: 'POST', body: formData });
            const data = await res.json();

            if (data.success) {
                msg.textContent = '✅ ' + data.message;
                msg.className = 'mt-4 text-center font-bold text-green-400';
                loadPanelRecharges();
                loadSalesReport();
                setTimeout(() => closeModal('editPanelRechargeModal'), 1500);
            } else {
                msg.textContent = '❌ ' + data.error;
                msg.className = 'mt-4 text-center font-bold text-red-400';
            }
            msg.classList.remove('hidden');
        } catch (err) {
            alert('Erro: ' + err);
        }
    });
}

// Global variable to store recharges
window.panelRecharges = [];

async function loadPanelRecharges() {
    try {
        const res = await fetch('/admin/panel/recharge/list');
        const recharges = await res.json();

        if (!recharges.data || recharges.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="p-4 text-center text-gray-500">Nenhuma recarga registrada</td></tr>';
            return;
        }

        // Update global variable
        window.panelRecharges = recharges.data;

        tbody.innerHTML = recharges.data.map((r, index) => {
            const totalBRL = (r.total_cost_usd * r.dolar_rate).toFixed(2);
            const data = new Date(r.created_at).toLocaleDateString('pt-BR');

            // Using index to pass to openEditPanelRecharge
            return `<tr class="border-b border-orange-500/30 hover:bg-orange-900/20">
                <td class="p-2 text-center">${r.quantity}</td>
                <td class="p-2 text-right">$${r.cost_per_unit_usd.toFixed(2)}</td>
                <td class="p-2 text-right font-bold text-cyan-400">$${r.total_cost_usd.toFixed(2)}</td>
                <td class="p-2 text-right">R$ ${r.dolar_rate.toFixed(2)}</td>
                <td class="p-2 text-right font-bold text-red-400">R$ ${totalBRL}</td>
                <td class="p-2 text-sm">${r.notes || '-'}</td>
                <td class="p-2 text-center text-xs">${data}</td>
                <td class="p-2 text-center flex justify-center gap-2">
                    <button type="button" onclick="openEditPanelRecharge(${index})" class="text-blue-400 hover:text-blue-300" title="Editar">✏️</button>
                    <button type="button" onclick="deletePanelRecharge(${r.id})" class="text-red-400 hover:text-red-300" title="Excluir">🗑️</button>
                </td>
            </tr>`;
        }).join('');
    } catch (err) {
        console.error('Erro ao carregar recargas:', err);
    }
}

async function deletePanelRecharge(id) {
    if (!confirm('Excluir esta recarga?')) return;
    try {
        const res = await fetch(`/admin/panel/recharge/delete/${id}`, { method: 'POST' });
        if (res.ok) {
            loadPanelRecharges();
            loadSalesReport();
        }
    } catch {
        alert('Erro ao excluir');
    }
}

function openEditPanelRecharge(index) {
    const r = window.panelRecharges[index];
    if (!r) {
        console.error('Recarga não encontrada no índice:', index);
        return;
    }

    document.getElementById('edit_recharge_id').value = r.id;
    document.getElementById('edit_recharge_quantity').value = r.quantity;
    document.getElementById('edit_recharge_cost_usd').value = r.cost_per_unit_usd;
    document.getElementById('edit_recharge_dolar').value = r.dolar_rate;
    document.getElementById('edit_recharge_notes').value = r.notes || '';

    document.getElementById('editRechargeMessage').classList.add('hidden');
    openModal('editPanelRechargeModal');
}
