/* =========================
   SALES - Vendas Manuais
========================= */

let allManualSales = []; // Store only current page sales
let salesPage = 1;
let salesLimit = 10;
let salesTotalPages = 1;

// Filter State
let salesCategory = '';
let salesDateStart = '';
let salesDateEnd = '';

function setupManualSaleForm() {
    document.getElementById('manualSaleForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        try {
            const res = await fetch('/admin/sales/manual/add', { method: 'POST', body: formData });
            const data = await res.json();
            const msg = document.getElementById('manualSaleMessage');
            if (data.success) {
                msg.textContent = '✅ ' + data.message;
                msg.className = 'mt-4 p-2 bg-green-900/30 border border-green-500 text-green-400 rounded';
                e.target.reset();
                loadManualSales();
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

    // Auto-fill custo unitário em BRL ao selecionar produto
    const prodSelect = document.querySelector('#manualSaleForm select[name="product_id"]');
    if (prodSelect) {
        prodSelect.addEventListener('change', async (e) => {
            const pid = e.target.value;
            const costInput = document.querySelector('#manualSaleForm input[name="cost_per_unit_brl"]');
            if (!pid) {
                if (costInput) costInput.value = '';
                return;
            }

            try {
                const res = await fetch(`/admin/product/info/${pid}`);
                if (!res.ok) return;
                const info = await res.json();
                if (info && typeof info.calculated_cost_brl !== 'undefined') {
                    if (costInput) costInput.value = info.calculated_cost_brl.toFixed(2);
                }
            } catch (err) {
                console.error('Erro ao buscar info do produto:', err);
            }
        });
    }

    // Event listener para o formulário de edição de venda manual
    document.getElementById('editManualSaleForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('edit_sale_id').value;
        const formData = new FormData(e.target);
        const msg = document.getElementById('editManualSaleMessage');

        try {
            const res = await fetch(`/admin/sales/manual/edit/${id}`, { method: 'POST', body: formData });
            const data = await res.json();

            if (data.success) {
                msg.textContent = '✅ ' + data.message;
                msg.className = 'mt-4 p-2 bg-green-900/30 border border-green-500 text-green-400 rounded text-center font-bold';
                setTimeout(() => {
                    closeModal('editManualSaleModal');
                    loadManualSales();
                    loadSalesReport();
                    msg.textContent = '';
                    msg.classList.add('hidden');
                }, 1000);
            } else {
                msg.textContent = '❌ ' + data.error;
                msg.className = 'mt-4 p-2 bg-red-900/30 border border-red-500 text-red-400 rounded text-center font-bold';
            }
            msg.classList.remove('hidden');
        } catch (err) {
            alert('Erro: ' + err);
        }
    });
}

function changeSalesLimit() {
    salesLimit = parseInt(document.getElementById('salesLimit').value);
    salesPage = 1;
    loadManualSales();
}

function prevSalesPage() {
    if (salesPage > 1) {
        salesPage--;
        loadManualSales();
    }
}

function nextSalesPage() {
    if (salesPage < salesTotalPages) {
        salesPage++;
        loadManualSales();
    }
}

function applySalesFilters() {
    salesCategory = document.getElementById('filterCategory').value;
    salesDateStart = document.getElementById('filterDateStart').value;
    salesDateEnd = document.getElementById('filterDateEnd').value;
    salesPage = 1; // Reset to page 1
    loadManualSales();
}

function clearSalesFilters() {
    salesCategory = '';
    salesDateStart = '';
    salesDateEnd = '';
    
    document.getElementById('filterCategory').value = '';
    document.getElementById('filterDateStart').value = '';
    document.getElementById('filterDateEnd').value = '';
    
    salesPage = 1;
    loadManualSales();
}

async function loadManualSales() {
    try {
        let url = `/admin/sales/manual/list?page=${salesPage}&limit=${salesLimit}`;
        if (salesCategory) url += `&category=${encodeURIComponent(salesCategory)}`;
        if (salesDateStart) url += `&date_start=${salesDateStart}`;
        if (salesDateEnd) url += `&date_end=${salesDateEnd}`;

        const res = await fetch(url);
        const data = await res.json();
        const sales = data.data;
        allManualSales = sales; // Store globally
        
        salesTotalPages = data.pages;
        document.getElementById('salesPageDisplay').textContent = salesPage;
        document.getElementById('salesTotalPages').textContent = salesTotalPages;
        
        document.getElementById('btnPrevSales').disabled = salesPage <= 1;
        document.getElementById('btnNextSales').disabled = salesPage >= salesTotalPages;

        const tbody = document.getElementById('manualSalesTable');
        
        if (sales.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="p-4 text-center text-gray-500">Nenhuma venda registrada</td></tr>';
            return;
        }
        
        tbody.innerHTML = sales.map(sale => {
            const totalVenda = (sale.total_price).toFixed(2);
            // Custo pode ser 0 para online se não calculado
            const totalCusto = (sale.quantity * sale.cost_per_unit_brl).toFixed(2);
            const lucro = (sale.profit).toFixed(2);
            const dataStr = new Date(sale.created_at).toLocaleDateString('pt-BR') + ' ' + new Date(sale.created_at).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
            
            let typeBadge = '';
            let clientInfo = '';
            let actions = '';

            if (sale.type === 'online') {
                typeBadge = '<span class="px-2 py-1 bg-green-900/50 text-green-400 rounded text-xs border border-green-500/30">Online</span>';
                clientInfo = `<span class="text-xs text-gray-300">${sale.client_info || 'N/A'}</span>`;
                actions = `<button onclick="viewOrderProof(${sale.id})" class="text-cyan-400 hover:text-cyan-300" title="Dossiê Anti-Fraude">🛡️</button>`;
            } else {
                typeBadge = '<span class="px-2 py-1 bg-purple-900/50 text-purple-400 rounded text-xs border border-purple-500/30">Manual</span>';
                clientInfo = `<span class="text-xs text-gray-400 italic">${sale.client_info || '-'}</span>`;
                actions = `
                    <button onclick='openEditManualSale(${sale.id}, ${sale.product_id}, ${sale.quantity}, ${sale.unit_price.toFixed(2)}, ${sale.cost_per_unit_brl.toFixed(2)}, ${JSON.stringify(sale.client_info || "")})' class="text-blue-400 hover:text-blue-300 mr-2" title="Editar">✏️</button>
                    <button onclick="deleteManualSale(${sale.id})" class="text-red-400 hover:text-red-300" title="Excluir">🗑️</button>
                `;
            }

            return `<tr class="border-b border-purple-500/30 hover:bg-purple-900/20">
                <td class="p-2 text-center">${typeBadge}</td>
                <td class="p-2">${sale.product_name}</td>
                <td class="p-2 text-center">${sale.quantity}</td>
                <td class="p-2 text-right">R$ ${sale.unit_price.toFixed(2)}</td>
                <td class="p-2 text-right text-gray-500">R$ ${sale.cost_per_unit_brl.toFixed(2)}</td>
                <td class="p-2 text-right font-bold text-green-400">R$ ${totalVenda}</td>
                <td class="p-2 text-right font-bold text-yellow-400">R$ ${lucro}</td>
                <td class="p-2 text-left">${clientInfo}</td>
                <td class="p-2 text-center text-xs text-gray-500">${dataStr}</td>
                <td class="p-2 text-center">
                    ${actions}
                </td>
            </tr>`;
        }).join('');
    } catch (err) {
        console.error('Erro ao carregar vendas:', err);
    }
}

function openEditManualSale(id, pid, qty, price, cost, notes) {
    document.getElementById('edit_sale_id').value = id;
    document.getElementById('edit_sale_product_id').value = pid;
    document.getElementById('edit_sale_quantity').value = qty;
    document.getElementById('edit_sale_unit_price').value = price;
    document.getElementById('edit_sale_cost').value = cost;
    document.getElementById('edit_sale_notes').value = notes || '';
    
    const modal = document.getElementById('editManualSaleModal');
    modal?.classList.remove('hidden');
    modal?.classList.add('modal-active');
}

async function deleteManualSale(id) {
    if (!confirm('Excluir esta venda?')) return;
    try {
        const res = await fetch(`/admin/sales/manual/delete/${id}`, { method: 'POST' });
        if (res.ok) {
            loadManualSales();
            loadSalesReport();
        }
    } catch {
        alert('Erro ao excluir');
    }
}

// --- DOSSIÊ ANTI-FRAUDE ---
async function viewOrderProof(orderId) {
    try {
        const res = await fetch(`/admin/sales/proof/${orderId}`);
        const data = await res.json();
        if (!data.success) {
            alert('Erro: ' + (data.error || 'Pedido não encontrado'));
            return;
        }
        const p = data.proof;

        const formatDate = (d) => {
            if (!d) return '—';
            try { return new Date(d).toLocaleString('pt-BR'); } catch { return d; }
        };

        // Build modal content
        const html = `
        <div class="fixed inset-0 bg-black/90 z-[300] flex items-center justify-center p-4 backdrop-blur-sm" id="proofModal" onclick="if(event.target===this)this.remove()">
            <div class="bg-gray-900 border-2 border-cyan-500 rounded-xl w-full max-w-lg overflow-y-auto max-h-[90vh] shadow-[0_0_30px_rgba(0,242,255,0.2)] relative">
                <div class="bg-cyan-500/10 p-4 border-b border-cyan-500/30 flex justify-between items-center">
                    <h3 class="text-lg font-bold text-cyan-400">🛡️ Dossiê Anti-Fraude</h3>
                    <button onclick="document.getElementById('proofModal').remove()" class="text-gray-400 hover:text-white text-xl">&times;</button>
                </div>
                <div class="p-5 space-y-3 text-sm">
                    <div class="border border-cyan-500/20 rounded p-3 bg-black/40">
                        <p class="text-cyan-400 font-bold mb-2">📦 Pedido</p>
                        <p class="text-gray-300">Ref: <span class="text-white font-mono">${p.external_reference || '—'}</span></p>
                        <p class="text-gray-300">Produto: <span class="text-white">${p.product_name}</span></p>
                        <p class="text-gray-300">Valor: <span class="text-green-400 font-bold">R$ ${(p.amount || 0).toFixed(2)}</span></p>
                        <p class="text-gray-300">Status: <span class="text-yellow-400">${p.status}</span></p>
                    </div>
                    <div class="border border-purple-500/20 rounded p-3 bg-black/40">
                        <p class="text-purple-400 font-bold mb-2">👤 Comprador</p>
                        <p class="text-gray-300">Nome: <span class="text-white">${p.customer_name || '—'}</span></p>
                        <p class="text-gray-300">CPF: <span class="text-white font-mono">${p.customer_cpf || '—'}</span></p>
                        <p class="text-gray-300">E-mail: <span class="text-white">${p.customer_email || '—'}</span></p>
                        <p class="text-gray-300">WhatsApp: <span class="text-white">${p.customer_phone || '—'}</span></p>
                    </div>
                    <div class="border border-green-500/20 rounded p-3 bg-black/40">
                        <p class="text-green-400 font-bold mb-2">🌐 IPs & Datas</p>
                        <p class="text-gray-300">IP da Compra: <span class="text-white font-mono">${p.ip_purchase || '—'}</span></p>
                        <p class="text-gray-300">IP da Entrega: <span class="text-white font-mono">${p.ip_delivery || '—'}</span></p>
                        <p class="text-gray-300">Termos Aceitos em: <span class="text-white">${formatDate(p.terms_accepted_at)}</span></p>
                        <p class="text-gray-300">Compra em: <span class="text-white">${formatDate(p.created_at)}</span></p>
                        <p class="text-gray-300">Chave entregue em: <span class="text-white">${formatDate(p.delivered_at)}</span></p>
                    </div>
                    <div class="border border-yellow-500/20 rounded p-3 bg-black/40">
                        <p class="text-yellow-400 font-bold mb-2">🔑 Chave Entregue</p>
                        <p class="text-white font-mono break-all">${p.key_delivered || '—'}</p>
                    </div>
                    <p class="text-[10px] text-gray-600 text-center mt-4">Tire um print desta tela para utilizar como prova em disputas.</p>
                </div>
            </div>
        </div>`;

        // Remove existing modal if any
        document.getElementById('proofModal')?.remove();
        document.body.insertAdjacentHTML('beforeend', html);
    } catch (err) {
        alert('Erro ao carregar provas: ' + err);
    }
}
