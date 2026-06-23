/* ==========================================================================
   PDV.JS - Ponto de Venda Rápido
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    setupPDVCheckoutForm();
});

// Filtragem de produtos por nome na busca rápida
function filterPDVProducts(query) {
    const term = query.trim().toLowerCase();
    const cards = document.querySelectorAll('#pdvProductsGrid .product-card');
    const emptyState = document.getElementById('pdvEmptyState');
    let visibleCount = 0;

    cards.forEach(card => {
        const prodName = card.dataset.productName || '';
        if (prodName.includes(term)) {
            card.classList.remove('hidden');
            visibleCount++;
        } else {
            card.classList.add('hidden');
        }
    });

    if (visibleCount === 0) {
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');
    }
}

// Abrir modal de checkout para o produto selecionado
function openPDVCheckout(id, name, price, promoPrice, stock) {
    document.getElementById('checkout_product_id').value = id;
    document.getElementById('checkout_product_name').innerText = name;
    document.getElementById('checkout_product_stock').innerText = `🟢 ${stock} chaves livres em estoque`;

    // Determinar preço padrão sugerido
    let finalPrice = price;
    if (promoPrice && promoPrice.trim() !== '') {
        finalPrice = promoPrice;
    }
    
    // Limpar formatação
    if (finalPrice) {
        finalPrice = parseFloat(String(finalPrice).replace('R$', '').replace(',', '.').trim()).toFixed(2);
    }
    document.getElementById('checkout_unit_price').value = finalPrice;

    // Limpar campos de cliente
    document.getElementById('pdvClientSearchInput').value = '';
    document.getElementById('pdv_client_name').value = '';
    document.getElementById('pdv_client_email').value = '';
    document.getElementById('pdvClientSearchResults').classList.add('hidden');

    // Mostrar modal
    const modal = document.getElementById('pdvCheckoutModal');
    modal.classList.remove('hidden');
}

// Fechar modal de checkout
function closePDVCheckout() {
    const modal = document.getElementById('pdvCheckoutModal');
    modal.classList.add('hidden');
}

// Autocomplete de Clientes Unificado (Clientes Cadastrados + Vendas Manuais)
let pdvClientSearchTimeout = null;
function searchPDVClients(query) {
    clearTimeout(pdvClientSearchTimeout);
    const resultsDiv = document.getElementById('pdvClientSearchResults');
    if (!query || query.trim().length < 2) {
        resultsDiv.classList.add('hidden');
        return;
    }

    pdvClientSearchTimeout = setTimeout(async () => {
        try {
            const res = await fetch(`/admin/api/pdv/clients/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();

            if (data.clients && data.clients.length > 0) {
                resultsDiv.innerHTML = data.clients.map(c => {
                    const badgeColor = c.source === 'cadastro' ? 'bg-cyan-950 text-cyan-400 border-cyan-500/20' : 'bg-purple-950 text-purple-400 border-purple-500/20';
                    const clientIdLabel = c.client_id === 'Manual' ? 'Manual' : c.client_id;
                    return `
                        <div onclick="selectPDVClient('${c.name}', '${c.email}', '${clientIdLabel}')" 
                             class="p-3 hover:bg-cyan-950/40 border-b border-gray-800/80 cursor-pointer text-sm text-gray-300 hover:text-white transition flex justify-between items-center">
                            <div>
                                <strong class="text-white">${c.name}</strong>
                                <div class="text-xs text-gray-500 font-mono">${c.email || 'Sem e-mail'}</div>
                            </div>
                            <span class="px-1.5 py-0.5 border rounded font-mono text-[9px] font-bold ${badgeColor}">
                                ${c.source.toUpperCase()}
                            </span>
                        </div>
                    `;
                }).join("");
                resultsDiv.classList.remove('hidden');
            } else {
                resultsDiv.innerHTML = `<div class="p-3 text-xs text-gray-500 text-center">Nenhum cliente encontrado.</div>`;
                resultsDiv.classList.remove('hidden');
            }
        } catch (err) {
            console.error("Erro na busca de clientes no PDV:", err);
        }
    }, 300);
}

function selectPDVClient(name, email, clientId) {
    document.getElementById('pdv_client_name').value = name;
    document.getElementById('pdv_client_email').value = email;
    
    const searchInput = document.getElementById('pdvClientSearchInput');
    if (clientId && clientId !== 'Manual') {
        searchInput.value = `${name} (${clientId})`;
    } else {
        searchInput.value = name;
    }
    document.getElementById('pdvClientSearchResults').classList.add('hidden');
}

// Fechar lista ao clicar fora
document.addEventListener('click', function(e) {
    const searchDiv = document.getElementById('pdvClientSearchInput');
    const resultsDiv = document.getElementById('pdvClientSearchResults');
    if (searchDiv && resultsDiv && !searchDiv.contains(e.target) && !resultsDiv.contains(e.target)) {
        resultsDiv.classList.add('hidden');
    }
});

// Configuração do formulário de checkout
function setupPDVCheckoutForm() {
    const form = document.getElementById('pdvCheckoutForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('btnPDVConfirm');
        const originalText = submitBtn.innerText;
        submitBtn.disabled = true;
        submitBtn.innerText = 'Processando venda...';

        const formData = new FormData(form);

        try {
            const res = await fetch('/admin/keys/redeem', { method: 'POST', body: formData });
            const data = await res.json();

            if (data.success) {
                // Fechar modal de checkout
                closePDVCheckout();

                const sale = data.sale || {};
                const key = data.key || '';

                // Formatar texto para o WhatsApp
                let zapText = `🚀 *COMPRA CONFIRMADA!* \n\n`;
                if (sale.client_name) {
                    zapText += `👤 *Cliente:* ${sale.client_name} \n`;
                }
                zapText += `📦 *Produto:* ${sale.product_name} \n`;
                zapText += `🔑 *Chave de Ativação:* ${key.trim()} \n\n`;
                zapText += `⚡ *Obrigado pela preferência! Ative o seu produto agora mesmo.*`;

                const linkZap = `https://api.whatsapp.com/send?text=${encodeURIComponent(zapText)}`;

                const modalHtml = `
                <div class="fixed inset-0 bg-black/90 z-[300] flex items-center justify-center p-4 backdrop-blur-sm" id="pdvSuccessModal">
                    <div class="bg-gray-900 border-2 border-cyan-500 rounded-xl w-full max-w-md overflow-hidden shadow-[0_0_30px_rgba(0,242,255,0.2)]">
                        <div class="bg-cyan-500/10 p-4 border-b border-cyan-500/30 flex justify-between items-center">
                            <h3 class="text-lg font-bold text-cyan-400">🔑 Venda Realizada!</h3>
                            <button onclick="closePDVSuccessModal()" class="text-gray-400 hover:text-white text-xl">&times;</button>
                        </div>
                        <div class="p-6 space-y-4">
                            <p class="text-gray-300 text-sm text-center">Chave resgatada com sucesso. Copie a chave abaixo ou envie diretamente via WhatsApp.</p>
                            
                            <div class="border border-cyan-500/20 rounded-lg p-4 bg-black/40 text-center">
                                <span class="text-[10px] text-gray-500 block mb-1 uppercase tracking-wider font-bold">Chave de Ativação</span>
                                <code id="pdvRedeemedKeyValue" class="text-white text-lg font-mono font-bold select-all break-all">${key}</code>
                            </div>
                            
                            <div class="flex gap-2">
                                <button onclick="copyPDVKey()" id="btnCopyPDV" 
                                    class="flex-1 py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-lg text-xs transition-all uppercase tracking-wider">
                                    📋 Copiar Chave
                                </button>
                                <a href="${linkZap}" target="_blank" 
                                    class="flex-1 py-3 bg-green-600 hover:bg-green-500 text-black font-bold rounded-lg text-xs text-center flex items-center justify-center gap-1.5 transition-all uppercase tracking-wider">
                                    💬 Enviar WhatsApp
                                </a>
                            </div>
                            
                            <div class="text-center pt-2">
                                <button onclick="closePDVSuccessModal()" class="text-gray-500 hover:text-gray-300 text-xs underline">
                                    Fechar e Atualizar Estoque
                                </button>
                            </div>
                        </div>
                    </div>
                </div>`;

                document.getElementById('pdvSuccessModal')?.remove();
                document.body.insertAdjacentHTML('beforeend', modalHtml);
            } else {
                alert('❌ Erro: ' + (data.error || 'Erro desconhecido ao processar venda.'));
            }
        } catch (err) {
            console.error(err);
            alert('❌ Erro de conexão ao enviar dados.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = originalText;
        }
    });
}

function copyPDVKey() {
    const keyEl = document.getElementById('pdvRedeemedKeyValue');
    const btn = document.getElementById('btnCopyPDV');
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

function closePDVSuccessModal() {
    document.getElementById('pdvSuccessModal')?.remove();
    // Recarregar a página para atualizar o estoque e remover produtos que ficaram sem chaves
    location.reload();
}
