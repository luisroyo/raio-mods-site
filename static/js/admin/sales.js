/* =========================
   SALES - Vendas Manuais
========================= */

let allManualSales = []; // Store only current page sales
let salesPage = 1;
let salesLimit = 10;
let salesTotalPages = 1;

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

async function loadManualSales() {
    try {
        const res = await fetch(`/admin/sales/manual/list?page=${salesPage}&limit=${salesLimit}`);
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
            tbody.innerHTML = '<tr><td colspan="8" class="p-4 text-center text-gray-500">Nenhuma venda registrada</td></tr>';
            return;
        }
        
        tbody.innerHTML = sales.map(sale => {
            const totalVenda = (sale.quantity * sale.unit_price).toFixed(2);
            const totalCusto = (sale.quantity * sale.cost_per_unit_brl).toFixed(2);
            const lucro = (totalVenda - totalCusto).toFixed(2);
            const dataStr = new Date(sale.created_at).toLocaleDateString('pt-BR');
            
            return `<tr class="border-b border-purple-500/30 hover:bg-purple-900/20">
                <td class="p-2">${sale.product_name}</td>
                <td class="p-2 text-center">${sale.quantity}</td>
                <td class="p-2 text-right">R$ ${sale.unit_price.toFixed(2)}</td>
                <td class="p-2 text-right">R$ ${sale.cost_per_unit_brl.toFixed(2)}</td>
                <td class="p-2 text-right font-bold text-green-400">R$ ${totalVenda}</td>
                <td class="p-2 text-right font-bold text-yellow-400">R$ ${lucro}</td>
                <td class="p-2 text-center text-xs">${dataStr}</td>
                <td class="p-2 text-center">
                    <button onclick='openEditManualSale(${sale.id}, ${sale.product_id}, ${sale.quantity}, ${sale.unit_price.toFixed(2)}, ${sale.cost_per_unit_brl.toFixed(2)}, ${JSON.stringify(sale.notes || "")})' class="text-blue-400 hover:text-blue-300 mr-2">✏️</button>
                    <button onclick="deleteManualSale(${sale.id})" class="text-red-400 hover:text-red-300">🗑️</button>
                </td>
            </tr>`;
        }).join('');
    } catch (err) {
        console.error('Erro ao carregar vendas manuais:', err);
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
