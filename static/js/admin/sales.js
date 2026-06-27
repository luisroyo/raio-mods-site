/* =========================
   SALES - Vendas Manuais
========================= */

let allManualSales = []; // Store only current page sales
let salesPage = 1;
let salesLimit = 10;
let salesTotalPages = 1;

// Filter State
let salesCategory = '';
let salesSupplier = '';
let salesDateStart = '';
let salesDateEnd = '';
let salesSearch = '';

function setupManualSaleForm() {
    document.getElementById('manualSaleForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        try {
            const res = await fetch('/admin/sales/manual/add', { method: 'POST', body: formData });
            const data = await res.json();
            const msg = document.getElementById('manualSaleMessage');
            if (data.success) {
                const sale = data.sale || {};
                const discountVal = document.getElementById('manual_discount')?.value || '';
                
                // Formatar texto do WhatsApp (Sem valores de preço, apenas produto, cliente e desconto)
                let text = `🚀 *NOVA COMPRA REALIZADA!* \n\n`;
                text += `👤 *Cliente:* ${sale.client_name || 'Cliente'} \n`;
                text += `📦 *Produto:* ${sale.product_name || 'Produto'}`;
                if (discountVal) {
                    text += ` \n🎟️ *Benefício:* Ganhou ${discountVal}% de desconto através do Giro da Sorte!`;
                }
                text += `\n\n⚡ *Adquira o seu também no nosso site! Obrigado pela preferência!*`;
                
                const linkZap = `https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`;
                msg.innerHTML = `
                    <div class="flex flex-col sm:flex-row items-center justify-between gap-4 p-3 bg-green-950/40 border border-green-500/50 rounded-lg">
                        <span class="text-green-400 font-semibold text-center sm:text-left">✅ ${data.message}</span>
                        <div class="flex gap-2 w-full sm:w-auto">
                            <a href="${linkZap}" target="_blank" class="flex-1 sm:flex-none px-4 py-2 bg-green-600 hover:bg-green-500 text-black font-bold rounded-lg text-xs flex items-center justify-center gap-1.5 shadow-[0_0_10px_rgba(34,197,94,0.3)] transition-all">
                                💬 WhatsApp
                            </a>
                            <a href="https://t.me/share/url?url=&text=${encodeURIComponent(text)}" target="_blank" class="flex-1 sm:flex-none px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg text-xs flex items-center justify-center gap-1.5 shadow-[0_0_10px_rgba(37,99,235,0.3)] transition-all">
                                ✈️ Telegram
                            </a>
                        </div>
                    </div>
                `;
                msg.className = 'mt-4';
                e.target.reset();
                loadManualSales();
                if (typeof loadSalesReport === 'function') loadSalesReport();
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
            const costUsdInput = document.querySelector('#manualSaleForm input[name="cost_per_unit_usd"]');
            if (!pid) {
                if (costInput) costInput.value = '';
                if (costUsdInput) {
                    costUsdInput.value = '';
                    delete costUsdInput.dataset.applyIof;
                }
                return;
            }

            try {
                const res = await fetch(`/admin/product/info/${pid}`);
                if (!res.ok) return;
                const info = await res.json();
                if (info && typeof info.calculated_cost_brl !== 'undefined') {
                    if (costInput) costInput.value = info.calculated_cost_brl.toFixed(2);
                    if (costUsdInput) {
                        costUsdInput.value = info.cost_usd > 0 ? info.cost_usd.toFixed(2) : '';
                        costUsdInput.dataset.applyIof = info.apply_iof;
                    }
                    if (typeof window.DOLAR_RATE !== 'undefined' && info.dolar_rate) {
                        window.DOLAR_RATE = info.dolar_rate;
                        const drSpan = document.getElementById('dolarRate');
                        if (drSpan) drSpan.textContent = info.dolar_rate.toFixed(4);
                    }
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
                    if (typeof loadSalesReport === 'function') loadSalesReport();
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
    salesSupplier = document.getElementById('filterSupplier')?.value || '';
    salesDateStart = document.getElementById('filterDateStart').value;
    salesDateEnd = document.getElementById('filterDateEnd').value;
    salesSearch = document.getElementById('filterSearch')?.value || '';
    salesPage = 1; // Reset to page 1
    loadManualSales();
}

function clearSalesFilters() {
    salesCategory = '';
    salesSupplier = '';
    salesDateStart = '';
    salesDateEnd = '';
    salesSearch = '';
    
    document.getElementById('filterCategory').value = '';
    const supplierEl = document.getElementById('filterSupplier');
    if (supplierEl) supplierEl.value = '';
    document.getElementById('filterDateStart').value = '';
    document.getElementById('filterDateEnd').value = '';
    const searchEl = document.getElementById('filterSearch');
    if (searchEl) searchEl.value = '';
    
    salesPage = 1;
    loadManualSales();
}

async function loadManualSales() {
    try {
        let url = `/admin/sales/manual/list?page=${salesPage}&limit=${salesLimit}`;
        if (salesCategory) url += `&category=${encodeURIComponent(salesCategory)}`;
        if (salesSupplier) url += `&supplier=${encodeURIComponent(salesSupplier)}`;
        if (salesDateStart) url += `&date_start=${salesDateStart}`;
        if (salesDateEnd) url += `&date_end=${salesDateEnd}`;
        if (salesSearch) url += `&search=${encodeURIComponent(salesSearch)}`;

        const res = await fetch(url);
        const data = await res.json();
        const sales = data.data;
        allManualSales = sales; // Store globally
        
        // Render dynamic totals for the filtered query
        const formatBrl = (val) => 'R$ ' + (val || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        const revEl = document.getElementById('salesTotalRevenue');
        if (revEl) revEl.textContent = formatBrl(data.total_revenue);
        const profEl = document.getElementById('salesTotalProfit');
        if (profEl) profEl.textContent = formatBrl(data.total_profit);
        
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
            let dataStr = '';
            let dateRaw = sale.created_at;
            if (dateRaw && dateRaw.length === 19 && !dateRaw.includes('T') && !dateRaw.includes('Z')) {
                dateRaw = dateRaw.replace(' ', 'T') + 'Z';
            }
            const dt = new Date(dateRaw);
            
            // Fuso horário corrigido para usar a interpretação de hora do navegador (local)
            // Trata as datas como UTC convertendo-as diretamente para Pt-Br
            dataStr = dt.toLocaleDateString('pt-BR') + ' ' + dt.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
            
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
                    <button onclick='openEditManualSale(${sale.id}, ${sale.product_id}, ${sale.quantity}, ${sale.unit_price.toFixed(2)}, ${sale.cost_per_unit_brl.toFixed(2)}, ${JSON.stringify(sale.client_info || "")}, ${JSON.stringify(sale.created_at)})' class="text-blue-400 hover:text-blue-300 mr-2" title="Editar">✏️</button>
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

function openEditManualSale(id, pid, qty, price, cost, notes, createdAt) {
    document.getElementById('edit_sale_id').value = id;
    document.getElementById('edit_sale_product_id').value = pid;
    document.getElementById('edit_sale_quantity').value = qty;
    document.getElementById('edit_sale_unit_price').value = price;
    document.getElementById('edit_sale_cost').value = cost;
    
    let name = notes || '';
    let email = '';
    if (name.includes('(') && name.includes(')')) {
        const parts = name.split('(');
        name = parts[0].trim();
        email = parts[1].replace(')', '').trim();
    }
    
    const clientNameInput = document.getElementById('edit_sale_client_name') || document.getElementById('edit_sale_notes');
    if (clientNameInput) clientNameInput.value = name;
    
    const clientEmailInput = document.getElementById('edit_sale_client_email');
    if (clientEmailInput) clientEmailInput.value = email;
    
    // Formatar data para o input date (YYYY-MM-DD)
    if (createdAt) {
        const date = new Date(createdAt);
        const pad = (n) => n.toString().padStart(2, '0');
        const formatted = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
        document.getElementById('edit_sale_created_at').value = formatted;
    } else {
        document.getElementById('edit_sale_created_at').value = '';
    }
    
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
            if (typeof loadSalesReport === 'function') loadSalesReport();
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
            try { 
                let dateStr = String(d);
                if (dateStr.length === 19 && !dateStr.includes('T') && !dateStr.includes('Z')) {
                    dateStr = dateStr.replace(' ', 'T') + 'Z';
                }
                return new Date(dateStr).toLocaleString('pt-BR'); 
            } catch { return d; }
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
                        <p class="text-gray-300">User-Agent: <span class="text-white font-mono text-[10px] break-all">${p.user_agent_delivery || '—'}</span></p>
                        <p class="text-gray-300">Termos Aceitos em: <span class="text-white">${formatDate(p.terms_accepted_at)}</span></p>
                        <p class="text-gray-300">Compra em: <span class="text-white">${formatDate(p.created_at)}</span></p>
                        <p class="text-gray-300">Chave revelada em: <span class="text-white">${formatDate(p.delivered_at)}</span></p>
                    </div>
                    <div class="border border-yellow-500/20 rounded p-3 bg-black/40">
                        <p class="text-yellow-400 font-bold mb-2">🔑 Chave Entregue</p>
                        <p class="text-white font-mono break-all">${p.key_delivered || '—'}</p>
                        <p class="text-gray-500 text-[10px] mt-1">SHA-256: <span class="font-mono">${p.key_hash || '—'}</span></p>
                    </div>
                    <div class="border border-orange-500/20 rounded p-3 bg-black/40">
                        <p class="text-orange-400 font-bold mb-2">📋 Resposta Padrão p/ Reembolso</p>
                        <p class="text-gray-400 text-[11px] leading-relaxed" id="refundMsg">Prezado(a) ${p.customer_name || 'cliente'},\n\nAgradecemos seu contato. Conforme nossos registros, a compra (Ref: ${p.external_reference}) foi concluída e a chave digital foi revelada e visualizada com sucesso em ${formatDate(p.delivered_at)}, a partir do IP ${p.ip_delivery || '—'}.\n\nOs termos de serviço aceitos no momento da compra informam que, por se tratar de produto digital com entrega imediata, não há possibilidade de reembolso após a visualização da chave.\n\nEstamos à disposição pelo suporte para resolver qualquer questão técnica.</p>
                        <button onclick="navigator.clipboard.writeText(document.getElementById('refundMsg').innerText);this.innerText='✅ Copiado!';setTimeout(()=>this.innerText='Copiar',1500)" class="mt-2 text-[10px] bg-orange-500/20 text-orange-400 px-3 py-1 rounded hover:bg-orange-500/30">Copiar</button>
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


// --- RESGATE DE CHAVES (ADMIN) ---

async function onRedeemProductChange() {
    const pid = document.getElementById('redeem_product_id').value;
    const stockStatus = document.getElementById('redeem_stock_status');
    const priceInput = document.getElementById('redeem_unit_price');
    const submitBtn = document.getElementById('btnSubmitRedeem');
    
    if (!pid) {
        stockStatus.innerHTML = '<span>Selecione um produto para verificar estoque</span>';
        priceInput.value = '';
        submitBtn.disabled = true;
        return;
    }
    
    stockStatus.innerHTML = '<span class="text-gray-400">Verificando estoque...</span>';
    
    try {
        const res = await fetch(`/admin/product/info/${pid}`);
        if (!res.ok) throw new Error('Falha ao buscar dados');
        const info = await res.json();
        
        // Exibir quantidade de chaves disponíveis
        const qty = info.stock || 0;
        let colorClass = 'text-red-500 font-bold';
        let icon = '🔴';
        if (qty > 5) {
            colorClass = 'text-green-400 font-bold';
            icon = '🟢';
        } else if (qty > 0) {
            colorClass = 'text-yellow-400 font-bold';
            icon = '🟡';
        }
        
        stockStatus.innerHTML = `
            <span class="${colorClass}">${icon} ${qty} chaves disponíveis</span>
            <span class="text-xs text-gray-500 font-mono">ID: ${pid}</span>
        `;
        
        // Preencher preço sugerido (verificar se tem preço promocional)
        let price = info.price || '';
        if (info.promo_price) {
            price = info.promo_price;
        }
        
        // Limpar o prefixo R$ e espaços se houver no banco
        if (price) {
            price = parseFloat(String(price).replace('R$', '').replace(',', '.').trim()).toFixed(2);
        }
        priceInput.value = price;
        
        // Habilitar ou desabilitar o botão com base no estoque
        submitBtn.disabled = (qty <= 0);
    } catch (err) {
        console.error(err);
        stockStatus.innerHTML = '<span class="text-red-500">Erro ao carregar informações</span>';
        submitBtn.disabled = true;
    }
}

function setupKeyRedeemForm() {
    const form = document.getElementById('keyRedeemForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('btnSubmitRedeem');
        const originalText = submitBtn.innerText;
        submitBtn.disabled = true;
        submitBtn.innerText = 'Processando resgate...';
        
        const msg = document.getElementById('keyRedeemMessage');
        const formData = new FormData(form);
        
        try {
            const res = await fetch('/admin/keys/redeem', { method: 'POST', body: formData });
            const data = await res.json();
            
            if (data.success) {
                // Fechar mensagens antigas
                msg.classList.add('hidden');
                
                // Exibir modal de resgate com sucesso contendo feedback visual de cópia e WhatsApp
                const sale = data.sale || {};
                const key = data.key || '';
                
                // Formatar texto para divulgação no WhatsApp
                let zapText = `🚀 *CHAVE DE ATIVAÇÃO RECEBIDA!* \n\n`;
                if (sale.client_name) {
                    zapText += `👤 *Cliente:* ${sale.client_name} \n`;
                }
                zapText += `📦 *Produto:* ${sale.product_name} \n`;
                zapText += `🔑 *Chave:* ${key.trim()} \n\n`;
                zapText += `⚡ *Obrigado pela preferência! Ative seu produto agora mesmo.*`;
                
                const linkZap = `https://api.whatsapp.com/send?text=${encodeURIComponent(zapText)}`;
                
                const modalHtml = `
                <div class="fixed inset-0 bg-black/90 z-[300] flex items-center justify-center p-4 backdrop-blur-sm" id="redeemSuccessModal">
                    <div class="bg-gray-900 border-2 border-cyan-500 rounded-xl w-full max-w-md overflow-hidden shadow-[0_0_30px_rgba(0,242,255,0.2)]">
                        <div class="bg-cyan-500/10 p-4 border-b border-cyan-500/30 flex justify-between items-center">
                            <h3 class="text-lg font-bold text-cyan-400">🔑 Chave Resgatada!</h3>
                            <button onclick="document.getElementById('redeemSuccessModal').remove()" class="text-gray-400 hover:text-white text-xl">&times;</button>
                        </div>
                        <div class="p-6 space-y-4">
                            <p class="text-gray-300 text-sm text-center">A chave foi resgatada e a venda registrada com sucesso no sistema.</p>
                            
                            <div class="border border-cyan-500/20 rounded-lg p-4 bg-black/40 text-center">
                                <span class="text-[10px] text-gray-500 block mb-1 uppercase tracking-wider font-bold">Chave de Ativação</span>
                                <code id="redeemedKeyValue" class="text-white text-lg font-mono font-bold select-all break-all">${key}</code>
                            </div>
                            
                            <div class="space-y-2">
                                <button onclick="copyRedeemedKey()" id="btnCopyRedeem" 
                                    class="w-full py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-lg text-xs transition-all uppercase tracking-wider">
                                    📋 Copiar Chave
                                </button>
                                <div class="flex gap-2">
                                    <a href="${linkZap}" target="_blank" 
                                        class="flex-1 py-3 bg-green-600 hover:bg-green-500 text-black font-bold rounded-lg text-xs text-center flex items-center justify-center gap-1.5 transition-all uppercase tracking-wider">
                                        💬 WhatsApp
                                    </a>
                                    <a href="https://t.me/share/url?url=&text=${encodeURIComponent(zapText)}" target="_blank" 
                                        class="flex-1 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg text-xs text-center flex items-center justify-center gap-1.5 transition-all uppercase tracking-wider">
                                        ✈️ Telegram
                                    </a>
                                </div>
                            </div>
                            
                            <div class="text-center">
                                <button onclick="document.getElementById('redeemSuccessModal').remove()" class="text-gray-500 hover:text-gray-300 text-xs underline">
                                    Fechar Janela
                                </button>
                            </div>
                        </div>
                    </div>
                </div>`;
                
                document.getElementById('redeemSuccessModal')?.remove();
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                // Limpar campos
                form.reset();
                document.getElementById('redeemClientSearchInput').value = '';
                
                // Recarregar vendas, estoque do produto e relatório financeiro
                onRedeemProductChange();
                loadManualSales();
                if (typeof loadSalesReport === 'function') loadSalesReport();
            } else {
                msg.textContent = '❌ ' + (data.error || 'Erro ao resgatar chave');
                msg.className = 'mt-4 p-3 bg-red-900/30 border border-red-500 text-red-400 rounded-lg text-sm';
                msg.classList.remove('hidden');
            }
        } catch (err) {
            console.error(err);
            msg.textContent = '❌ Erro de conexão com o servidor';
            msg.className = 'mt-4 p-3 bg-red-900/30 border border-red-500 text-red-400 rounded-lg text-sm';
            msg.classList.remove('hidden');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = originalText;
        }
    });
}

function copyRedeemedKey() {
    const keyEl = document.getElementById('redeemedKeyValue');
    const btn = document.getElementById('btnCopyRedeem');
    if (!keyEl || !btn) return;
    
    navigator.clipboard.writeText(keyEl.innerText.trim()).then(() => {
        const originalText = btn.innerText;
        btn.innerText = '✅ Copiado!';
        btn.classList.remove('bg-cyan-600', 'hover:bg-cyan-500');
        btn.classList.add('bg-green-600');
        setTimeout(() => {
            btn.innerText = originalText;
            btn.classList.add('bg-cyan-600', 'hover:bg-cyan-500');
            btn.classList.remove('bg-green-600');
        }, 1500);
    }).catch(err => {
        console.error('Erro ao copiar chave:', err);
    });
}
