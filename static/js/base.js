// --- SISTEMA DE TOASTS ---
window.showToast = function(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) {
        alert(message); // Fallback
        return;
    }

    const toast = document.createElement('div');
    toast.className = `transform transition-all duration-300 translate-x-full opacity-0 flex items-center justify-between p-4 rounded-lg shadow-lg pointer-events-auto border-l-4 backdrop-blur-md`;

    let bgColor, borderColor, icon;
    switch (type) {
        case 'success':
            bgColor = 'bg-green-900/90';
            borderColor = 'border-green-500';
            icon = '<svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
            break;
        case 'error':
            bgColor = 'bg-red-900/90';
            borderColor = 'border-red-500';
            icon = '<svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';
            break;
        case 'warning':
            bgColor = 'bg-yellow-900/90';
            borderColor = 'border-yellow-500';
            icon = '<svg class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>';
            break;
        default: // info
            bgColor = 'bg-blue-900/90';
            borderColor = 'border-blue-500';
            icon = '<svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
            break;
    }

    toast.classList.add(bgColor, borderColor);
    toast.innerHTML = `
        <div class="flex items-center gap-3">
            ${icon}
            <span class="text-white text-sm font-medium">${message}</span>
        </div>
        <button class="ml-4 text-gray-300 hover:text-white" onclick="this.parentElement.remove()">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
    `;

    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
        toast.classList.add('translate-x-0', 'opacity-100');
    });

    setTimeout(() => {
        toast.classList.remove('translate-x-0', 'opacity-100');
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

document.addEventListener('DOMContentLoaded', () => {
    // Inicialização do AOS (Animações)
    if (typeof AOS !== 'undefined') {
        AOS.init({ duration: 800, easing: 'ease-in-out', once: true });
    }

    // --- MENU MOBILE (HAMBURGER) ---
    const btnMenu = document.getElementById('btn-menu-mobile');
    const menuPanel = document.getElementById('menu-mobile');
    const overlay = document.getElementById('menu-mobile-overlay');
    const btnClose = document.getElementById('btn-close-menu');

    function openMenu() {
        if (menuPanel) menuPanel.classList.remove('translate-x-full');
        if (overlay) overlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
        if (menuPanel) menuPanel.classList.add('translate-x-full');
        if (overlay) overlay.classList.add('hidden');
        document.body.style.overflow = '';
    }

    if (btnMenu) btnMenu.addEventListener('click', openMenu);
    if (overlay) overlay.addEventListener('click', closeMenu);
    if (btnClose) btnClose.addEventListener('click', closeMenu);
    
    document.querySelectorAll('.nav-mobile-link').forEach(link => {
        link.addEventListener('click', closeMenu);
    });

    // --- CAPTURA DE REFERÊNCIA DE VENDEDOR (AFILIADO) ---
    const urlParams = new URLSearchParams(window.location.search);
    const ref = urlParams.get('ref');
    if (ref) {
        // Salva no localStorage e remove da URL para ficar limpo (opcional)
        localStorage.setItem('seller_ref', ref.trim().toUpperCase());
        console.log("Referência de vendedor salva:", ref);
    }
});

// --- LÓGICA DE CHECKOUT AUTOMÁTICO (MERCADO PAGO) ---

let currentProductId = null;
let currentProductPrice = 0;
let currentCouponCode = null;
let paymentCheckInterval = null;

// Abre o modal
function openCheckout(id, name, price, platform = '') {
    currentProductId = id;
    currentProductPrice = parseFloat(price.replace(/[^\d.,]/g, '').replace(',', '.')) || 0;
    currentCouponCode = null;
    
    if(typeof gtag === 'function') {
        gtag('event', 'begin_checkout', { 
            items: [{ item_id: id, item_name: name, price: currentProductPrice }] 
        });
    }
    
    document.getElementById('modalProductName').innerText = name;
    document.getElementById('modalProductPrice').innerText = price;
    
    // Reseta os passos visualmente
    document.getElementById('step-email').classList.remove('hidden');
    document.getElementById('step-payment').classList.add('hidden');
    document.getElementById('step-success').classList.add('hidden');
    document.getElementById('step-success').classList.add('hidden');
    document.getElementById('customerName').value = '';
    document.getElementById('customerEmail').value = '';
    document.getElementById('customerPhone').value = '';
    document.getElementById('customerCoupon').value = '';
    document.getElementById('customerTerms').checked = false;
    
    const msgCoupon = document.getElementById('couponMessage');
    if(msgCoupon) msgCoupon.classList.add('hidden');
    const btnCoupon = document.getElementById('btnApplyCoupon');
    if(btnCoupon) {
        btnCoupon.disabled = false;
        btnCoupon.innerText = 'Aplicar';
    }
    
    // Configura o aviso de plataforma
    const warningDiv = document.getElementById('platformWarning');
    const warningText = document.getElementById('platformWarningText');
    const confirmText = document.getElementById('platformConfirmText');
    const confirmBox = document.getElementById('platformConfirm');
    
    if (warningDiv) {
        if (platform === 'android') {
            warningText.innerHTML = '⚠️ Este produto funciona apenas em dispositivos Android. Compras realizadas para iPhone não poderão ser utilizadas.';
            confirmText.innerText = 'Confirmo que meu dispositivo é Android.';
            confirmBox.checked = false;
            warningDiv.classList.remove('hidden');
        } else if (platform === 'ios') {
            warningText.innerHTML = '⚠️ Este produto funciona apenas em iPhone/iPad (iOS). Compras para Android não são compatíveis.';
            confirmText.innerText = 'Confirmo que meu dispositivo é iOS (iPhone/iPad).';
            confirmBox.checked = false;
            warningDiv.classList.remove('hidden');
        } else {
            warningDiv.classList.add('hidden');
        }
    }
    
    // Reseta visualização do QR Code/Aviso
    document.getElementById('qrImage').style.display = 'block';
    if(document.getElementById('pixCopyPaste').parentNode) {
        document.getElementById('pixCopyPaste').parentNode.style.display = 'block';
    }
    // Remove mensagens de cartão anteriores se houver
    const msgCard = document.getElementById('msg-card-warning');
    if(msgCard) msgCard.remove();
    
    // Mostra o modal com animação Drawer
    const modal = document.getElementById('checkoutModal');
    const content = document.getElementById('checkoutModalContent');
    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.classList.remove('opacity-0');
        if(content) content.classList.remove('translate-x-full');
    }, 10);
}

// Fecha o modal e para a verificação de pagamento
function closeCheckout() {
    const modal = document.getElementById('checkoutModal');
    const content = document.getElementById('checkoutModalContent');
    
    modal.classList.add('opacity-0');
    if(content) content.classList.add('translate-x-full');
    
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
    
    if (paymentCheckInterval) {
        clearInterval(paymentCheckInterval);
        paymentCheckInterval = null;
    }
}

async function applyCouponFront() {
    const code = document.getElementById('customerCoupon').value.trim();
    if (!code) return;
    
    const btn = document.getElementById('btnApplyCoupon');
    const msg = document.getElementById('couponMessage');
    
    btn.disabled = true;
    btn.innerText = '⏳';
    
    try {
        const res = await fetch('/api/check_coupon', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ code: code, product_id: currentProductId })
        });
        const data = await res.json();
        
        msg.classList.remove('hidden');
        if (data.error) {
            msg.className = 'text-xs mt-1 text-red-500';
            msg.innerText = data.error;
            btn.disabled = false;
            btn.innerText = 'Aplicar';
            currentCouponCode = null;
            document.getElementById('modalProductPrice').innerText = `R$ ${currentProductPrice.toFixed(2).replace('.', ',')}`;
        } else {
            msg.className = 'text-xs mt-1 text-green-400 font-bold';
            msg.innerText = `Cupom aplicado! Desconto de ${data.discount_label}`;
            btn.innerText = '✓';
            currentCouponCode = code;
            
            if(typeof gtag === 'function') {
                gtag('event', 'coupon_applied', { coupon: code, discount: data.discount_amount });
            }
            
            const newPrice = Math.max(0, currentProductPrice - data.discount_amount);
            document.getElementById('modalProductPrice').innerHTML = `
                <span class="line-through text-gray-500 text-sm font-normal">R$ ${currentProductPrice.toFixed(2).replace('.', ',')}</span> 
                <span class="text-neon-green ml-2">R$ ${newPrice.toFixed(2).replace('.', ',')}</span>
            `;
        }
    } catch (e) {
        msg.className = 'text-xs mt-1 text-red-500';
        msg.innerText = 'Erro ao validar cupom.';
        btn.disabled = false;
        btn.innerText = 'Aplicar';
    }
}

// Inicia o pagamento (chama o backend)
async function startPayment(type) {
    const name = document.getElementById('customerName').value.trim();
    const cpf = ''; // Removed from UI
    const email = document.getElementById('customerEmail').value.trim();
    const phone = document.getElementById('customerPhone').value.trim();
    const termsChecked = document.getElementById('customerTerms').checked;
    const btnPix = document.getElementById('btnPayPix');
    const btnCard = document.getElementById('btnPayCard');
    
    const nameParts = name.trim().split(/\s+/);
    if (!name || nameParts.length < 2 || nameParts[0].length < 2 || nameParts[1].length < 2) {
        showToast('Por favor, digite seu NOME e SOBRENOME corretamente. Apelidos ou apenas o primeiro nome não são aceitos.', 'warning');
        return;
    }
    if (!email || !email.includes('@')) {
        showToast('Por favor, digite um e-mail válido.', 'warning');
        return;
    }
    
    const warningDiv = document.getElementById('platformWarning');
    const confirmBox = document.getElementById('platformConfirm');
    if (warningDiv && !warningDiv.classList.contains('hidden')) {
        if (!confirmBox.checked) {
            showToast('Você precisa confirmar o sistema operacional do seu dispositivo para continuar.', 'warning');
            return;
        }
    }
    
    if (!termsChecked) {
        showToast('Você precisa aceitar os Termos de Serviço para prosseguir.', 'warning');
        return;
    }

    // Bloqueia botões e mostra loading
    btnPix.disabled = true; 
    btnCard.disabled = true;
    const originalPix = btnPix.innerHTML;
    const originalCard = btnCard.innerHTML;
    
    if(type === 'pix') btnPix.innerHTML = '🔄 Gerando Pix...';
    else btnCard.innerHTML = '🔄 Redirecionando...';

    try {
        const sellerRef = localStorage.getItem('seller_ref');
        
        const response = await fetch('/api/checkout', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                product_id: currentProductId,
                name: name,
                cpf: cpf,
                email: email,
                phone: phone,
                type: type,
                terms_accepted: termsChecked,
                coupon: currentCouponCode,
                seller_coupon: sellerRef,
                init_data: window.TelegramWebApp ? window.TelegramWebApp.initData : null,
                platform_confirmed: document.getElementById('platformConfirm') ? document.getElementById('platformConfirm').checked : false
            })
        });

        const data = await response.json();

        if (data.error) {
            showToast('Erro: ' + data.error, 'error');
            resetButtons();
            return;
        }

        // SE FOR PIX (MOSTRA QR CODE NA TELA)
        if (data.type === 'pix') {
            if(typeof gtag === 'function') {
                gtag('event', 'payment_pix_created', { transaction_id: data.order_ref });
            }
            document.getElementById('step-email').classList.add('hidden');
            document.getElementById('step-payment').classList.remove('hidden');
            
            document.getElementById('qrImage').src = `data:image/png;base64,${data.qr_code_base64}`;
            document.getElementById('pixCopyPaste').value = data.qr_code;

            // Inicia verificação
            startPolling(data.order_ref);
        }
        
        // SE FOR CARTÃO (REDIRECIONA NA MESMA ABA)
        else if (data.type === 'card') {
            if(typeof gtag === 'function') {
                gtag('event', 'payment_card_created', { transaction_id: data.order_ref });
            }
            // Redireciona na mesma aba para evitar o bloqueador de popups do navegador
            window.location.href = data.checkout_url;
            
            // Muda a tela do modal para "Aguardando Pagamento"
            document.getElementById('step-email').classList.add('hidden');
            document.getElementById('step-payment').classList.remove('hidden');
            
            // Esconde QR Code (já que é cartão) e mostra aviso
            document.getElementById('qrImage').style.display = 'none';
            document.getElementById('pixCopyPaste').parentNode.style.display = 'none'; // Esconde text area
            
            // Cria aviso visual (se já não existir)
            if(!document.getElementById('msg-card-warning')) {
                const msgDiv = document.createElement('div');
                msgDiv.id = 'msg-card-warning';
                msgDiv.innerHTML = `
                    <div class="text-center py-8">
                        <p class="text-xl text-white mb-2">Aba de Pagamento Aberta!</p>
                        <p class="text-sm text-gray-400">Conclua o pagamento na aba do Mercado Pago.</p>
                        <p class="text-xs text-yellow-500 mt-4">Assim que pagar, sua chave aparecerá aqui.</p>
                    </div>
                `;
                const container = document.getElementById('step-payment');
                container.insertBefore(msgDiv, container.firstChild);
            }

            // Inicia verificação
            startPolling(data.order_ref);
        }

    } catch (error) {
        console.error(error);
        showToast('Erro ao conectar com o servidor.', 'error');
        resetButtons();
    }

    function resetButtons() {
        btnPix.disabled = false; btnCard.disabled = false;
        btnPix.innerHTML = originalPix;
        btnCard.innerHTML = originalCard;
    }
}

// Funções de Copiar
function copyPix() {
    const copyText = document.getElementById("pixCopyPaste");
    copyText.select();
    document.execCommand("copy");
    showToast("Código PIX copiado!", 'success');
}

function copyKey() {
    const keyText = document.getElementById("finalKey").innerText;
    navigator.clipboard.writeText(keyText).then(() => {
        showToast("Chave copiada!", 'success');
    });
}

// Verifica status a cada 5 segundos
let currentOrderRef = null;

function startPolling(orderId) {
    currentOrderRef = orderId;
    if (paymentCheckInterval) clearInterval(paymentCheckInterval);

    paymentCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/check_status/${orderId}?_t=${new Date().getTime()}`);
            const data = await response.json();

            if (data.status === 'ready_to_reveal') {
                // PAGAMENTO APROVADO COM CHAVE
                clearInterval(paymentCheckInterval);
                showRevealStep();
            } else if (data.status === 'paid_no_key') {
                // PAGAMENTO APROVADO SEM CHAVE (ENTREGA MANUAL)
                clearInterval(paymentCheckInterval);
                showNoKeyStep();
            }
        } catch (e) {
            console.error("Erro no polling", e);
        }
    }, 5000); // 5 segundos
}

// Mostra o passo intermediário com botão "Revelar Minha Chave"
function showRevealStep() {
    document.getElementById('step-payment').classList.add('hidden');
    document.getElementById('step-email').classList.add('hidden');
    document.getElementById('step-reveal').classList.remove('hidden');
    document.getElementById('step-success').classList.add('hidden');
}

// Mostra o passo de sucesso mas sem chave (contato manual)
function showNoKeyStep() {
    document.getElementById('step-payment').classList.add('hidden');
    document.getElementById('step-email').classList.add('hidden');
    document.getElementById('step-reveal').classList.add('hidden');
    
    document.getElementById('step-success').classList.remove('hidden');
    document.getElementById('finalKey').innerText = 'Fale conosco no WhatsApp';
    const copyBtn = document.querySelector('#step-success button[title="Copiar"]');
    if(copyBtn) copyBtn.style.display = 'none';
    
    const msgEl = document.querySelector('#step-success p');
    if(msgEl) msgEl.innerText = 'Pagamento aprovado! Produto será entregue manualmente.';
}

// Chama o backend para registrar prova de consumo e revelar a chave
async function revealKey() {
    const btn = document.getElementById('btnRevealKey');
    btn.disabled = true;
    btn.innerHTML = '🔄 Carregando chave...';

    try {
        const response = await fetch(`/api/reveal_key/${currentOrderRef}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        const data = await response.json();

        if (data.status === 'revealed' && data.key) {
            document.getElementById('finalKey').innerText = data.key;
            document.getElementById('step-reveal').classList.add('hidden');
            document.getElementById('step-success').classList.remove('hidden');
        } else {
            showToast('Erro ao revelar a chave: ' + (data.error || 'Tente novamente.'), 'error');
            btn.disabled = false;
            btn.innerHTML = '🔓 Revelar Minha Chave';
        }
    } catch (err) {
        console.error(err);
        showToast('Erro ao conectar com o servidor.', 'error');
        btn.disabled = false;
        btn.innerHTML = '🔓 Revelar Minha Chave';
    }
}

// Exibe a tela final com a chave
function showSuccess(key) {
    document.getElementById('step-payment').classList.add('hidden');
    document.getElementById('step-reveal').classList.add('hidden');
    document.getElementById('step-success').classList.remove('hidden');
    document.getElementById('finalKey').innerText = key;
}
// Máscara de CPF removida

function copyProductLink(productId) {
    const link = window.location.origin + '/pagamento?product_id=' + productId;
    navigator.clipboard.writeText(link).then(() => {
        showToast("Link do produto copiado! Você pode colar no seu catálogo do WhatsApp.", 'success');
    }).catch(err => {
        console.error('Erro ao copiar: ', err);
        showToast("Erro ao copiar o link. Tente copiar manualmente: " + link, 'error');
    });
}