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
let paymentCheckInterval = null;

// Abre o modal
function openCheckout(id, name, price) {
    currentProductId = id;
    document.getElementById('modalProductName').innerText = name;
    document.getElementById('modalProductPrice').innerText = price;
    
    // Reseta os passos visualmente
    document.getElementById('step-email').classList.remove('hidden');
    document.getElementById('step-payment').classList.add('hidden');
    document.getElementById('step-success').classList.add('hidden');
    document.getElementById('customerEmail').value = '';
    
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

// Inicia o pagamento (Envia dados para o Python)
async function startPayment() {
    const email = document.getElementById('customerEmail').value;
    const btn = document.getElementById('btnPay');
    
    if (!email || !email.includes('@')) {
        alert('Por favor, digite um e-mail válido.');
        return;
    }

    // Efeito de carregamento
    const originalText = btn.innerHTML;
    btn.innerHTML = '🔄 Gerando...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/checkout', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                product_id: currentProductId,
                email: email
            })
        });

        const data = await response.json();

        if (data.error) {
            alert('Erro: ' + data.error);
            btn.innerHTML = originalText;
            btn.disabled = false;
            return;
        }

        // Sucesso: Mostra o QR Code
        document.getElementById('step-email').classList.add('hidden');
        document.getElementById('step-payment').classList.remove('hidden');
        
        // Insere a imagem e o código copia-e-cola
        document.getElementById('qrImage').src = `data:image/png;base64,${data.qr_code_base64}`;
        document.getElementById('pixCopyPaste').value = data.qr_code;

        // Inicia verificação de status (Polling)
        startPolling(data.order_id);

    } catch (error) {
        console.error(error);
        alert('Erro ao conectar com o servidor.');
        btn.innerHTML = originalText;
        btn.disabled = false;
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
function startPolling(orderId) {
    if (paymentCheckInterval) clearInterval(paymentCheckInterval);

    paymentCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/check_status/${orderId}`);
            const data = await response.json();

            if (data.status === 'approved' && data.key) {
                // PAGAMENTO APROVADO!
                clearInterval(paymentCheckInterval);
                showSuccess(data.key);
            }
        } catch (e) {
            console.error("Erro no polling", e);
        }
    }, 5000); // 5 segundos
}

// Exibe a tela final com a chave
function showSuccess(key) {
    document.getElementById('step-payment').classList.add('hidden');
    document.getElementById('step-success').classList.remove('hidden');
    document.getElementById('finalKey').innerText = key;
}