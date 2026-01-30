// Função de Copiar
function copyText(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const text = element.innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert('Copiado com sucesso!');
    }).catch(err => {
        console.error('Erro ao copiar', err);
    });
}

// Inicialização
document.addEventListener("DOMContentLoaded", function() {
    console.log('Pagamento JS carregado.');

    const qrcodeElement = document.getElementById("qrcode");
    const avisoEl = document.getElementById("qrcode-aviso");

    if (qrcodeElement) {
        // PIX Copia e Cola funciona ao escanear; só a chave pode dar erro em muitos apps
        const copiaCola = (qrcodeElement.getAttribute('data-copia-cola') || '').trim();
        const pixKey = (qrcodeElement.getAttribute('data-key') || '').trim();
        const textoQR = copiaCola || pixKey;

        if (textoQR) {
            try {
                if (typeof QRCode === 'undefined') {
                    console.error("Biblioteca QRCode não carregada.");
                    if (avisoEl) avisoEl.classList.remove('hidden');
                    return;
                }
                new QRCode(qrcodeElement, {
                    text: textoQR,
                    width: 180,
                    height: 180,
                    colorDark : "#000000",
                    colorLight : "#ffffff",
                    correctLevel : QRCode.CorrectLevel.H
                });
                // Se o QR está só com a chave (não tem Copia e Cola), mostra aviso
                if (!copiaCola && avisoEl) avisoEl.classList.remove('hidden');
            } catch (e) {
                console.error("Erro ao gerar QR Code.", e);
                if (avisoEl) avisoEl.classList.remove('hidden');
            }
        } else {
            if (qrcodeElement.parentElement) {
                qrcodeElement.parentElement.style.display = 'none';
            }
        }
    }
});