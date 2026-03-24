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
});

// --- LÓGICA DE CHECKOUT AUTOMÁTICO (MERCADO PAGO) ---

let currentProductId = null;
let currentProductPrice = 0;
let currentCouponCode = null;
let paymentCheckInterval = null;

// Abre o modal
function openCheckout(id, name, price) {
    currentProductId = id;
    currentProductPrice = parseFloat(price.replace(/[^\d.,]/g, '').replace(',', '.')) || 0;
    currentCouponCode = null;
    
    document.getElementById('modalProductName').innerText = name;
    document.getElementById('modalProductPrice').innerText = price;
    
    // Reseta os passos visualmente
    document.getElementById('step-email').classList.remove('hidden');
    document.getElementById('step-payment').classList.add('hidden');
    document.getElementById('step-success').classList.add('hidden');
    document.getElementById('customerName').value = '';
    document.getElementById('customerCPF').value = '';
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
    
    // Reseta visualização do QR Code/Aviso
    document.getElementById('qrImage').style.display = 'block';
    if(document.getElementById('pixCopyPaste').parentNode) {
        document.getElementById('pixCopyPaste').parentNode.style.display = 'block';
    }
    // Remove mensagens de cartão anteriores se houver
    const msgCard = document.getElementById('msg-card-warning');
    if(msgCard) msgCard.remove();
    
    // Mostra o modal
    document.getElementById('checkoutModal').classList.remove('hidden');
}

// Fecha o modal e para a verificação de pagamento
function closeCheckout() {
    document.getElementById('checkoutModal').classList.add('hidden');
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
    const cpf = document.getElementById('customerCPF').value.trim();
    const email = document.getElementById('customerEmail').value.trim();
    const phone = document.getElementById('customerPhone').value.trim();
    const termsChecked = document.getElementById('customerTerms').checked;
    const btnPix = document.getElementById('btnPayPix');
    const btnCard = document.getElementById('btnPayCard');
    
    if (!name) {
        alert('Por favor, digite seu nome completo.');
        return;
    }
    if (!cpf || cpf.replace(/\D/g, '').length < 11) {
        alert('Por favor, digite um CPF válido.');
        return;
    }
    if (!email || !email.includes('@')) {
        alert('Por favor, digite um e-mail válido.');
        return;
    }
    if (!termsChecked) {
        alert('Você precisa aceitar os Termos de Serviço para prosseguir.');
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
        const response = await fetch('/api/checkout', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                product_id: currentProductId,
                name: name,
                cpf: cpf,
                email: email,
                phone: phone,
                coupon: currentCouponCode,
                terms_accepted: termsChecked,
                type: type // 'pix' ou 'card'
            })
        });

        const data = await response.json();

        if (data.error) {
            alert('Erro: ' + data.error);
            resetButtons();
            return;
        }

        // SE FOR PIX (MOSTRA QR CODE NA TELA)
        if (data.type === 'pix') {
            document.getElementById('step-email').classList.add('hidden');
            document.getElementById('step-payment').classList.remove('hidden');
            
            document.getElementById('qrImage').src = `data:image/png;base64,${data.qr_code_base64}`;
            document.getElementById('pixCopyPaste').value = data.qr_code;

            // Inicia verificação
            startPolling(data.order_ref);
        }
        
        // SE FOR CARTÃO (ABRE NOVA ABA E ESPERA PAGAMENTO)
        else if (data.type === 'card') {
            // Abre o checkout do Mercado Pago em outra aba
            window.open(data.checkout_url, '_blank');
            
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
        alert('Erro ao conectar com o servidor.');
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
    alert("Código PIX copiado!");
}

function copyKey() {
    const keyText = document.getElementById("finalKey").innerText;
    navigator.clipboard.writeText(keyText).then(() => {
        alert("Chave copiada!");
    });
}

// Verifica status a cada 5 segundos
let currentOrderRef = null;

function startPolling(orderId) {
    currentOrderRef = orderId;
    if (paymentCheckInterval) clearInterval(paymentCheckInterval);

    paymentCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/check_status/${orderId}`);
            const data = await response.json();

            if (data.status === 'ready_to_reveal') {
                // PAGAMENTO APROVADO — mostra botão de revelar
                clearInterval(paymentCheckInterval);
                showRevealStep();
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
            alert('Erro ao revelar a chave: ' + (data.error || 'Tente novamente.'));
            btn.disabled = false;
            btn.innerHTML = '🔓 Revelar Minha Chave';
        }
    } catch (err) {
        console.error(err);
        alert('Erro ao conectar com o servidor.');
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

// Máscara de CPF (###.###.###-##)
document.addEventListener('DOMContentLoaded', () => {
    const cpfInput = document.getElementById('customerCPF');
    if (cpfInput) {
        cpfInput.addEventListener('input', function(e) {
            let v = e.target.value.replace(/\D/g, '').substring(0, 11);
            if (v.length > 9) v = v.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
            else if (v.length > 6) v = v.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
            else if (v.length > 3) v = v.replace(/(\d{3})(\d{1,3})/, '$1.$2');
            e.target.value = v;
        });
    }
});