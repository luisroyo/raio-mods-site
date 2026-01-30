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
    
    if (qrcodeElement) {
        // Pega a chave do atributo 'data-key'
        const pixKey = qrcodeElement.getAttribute('data-key');
        
        if (pixKey && pixKey.trim() !== "") {
            // Gera o QR Code
            try {
                new QRCode(qrcodeElement, {
                    text: pixKey,
                    width: 180,
                    height: 180,
                    colorDark : "#000000",
                    colorLight : "#ffffff",
                    correctLevel : QRCode.CorrectLevel.H
                });
            } catch (e) {
                console.error("Erro ao gerar QR Code. Biblioteca qrcode.js carregada?", e);
            }
        } else {
            // Esconde o container pai se não tiver chave
            if(qrcodeElement.parentElement) {
                qrcodeElement.parentElement.style.display = 'none';
            }
        }
    }
});