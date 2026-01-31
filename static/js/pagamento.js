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
    if (!qrcodeElement) return;

    // Dados PIX vêm do JSON (evita truncar o Copia e Cola em data-attribute)
    let pixKey = '';
    let pixCopiaCola = '';
    try {
        const scriptEl = document.getElementById("pix-qr-data");
        if (scriptEl && scriptEl.textContent) {
            const data = JSON.parse(scriptEl.textContent);
            pixKey = (data.pix_key || '').trim();
            pixCopiaCola = (data.pix_copia_cola || '').trim();
        }
    } catch (e) {
        console.error("Erro ao ler dados PIX.", e);
    }

    // Só mostra o QR se tiver PIX Copia e Cola — senão dá erro no banco ao escanear. Sem sentido exibir.
    if (!pixCopiaCola) {
        const wrapper = document.getElementById('qrcode-wrapper');
        if (wrapper) wrapper.style.display = 'none';
        return;
    }

    // Tem Copia e Cola: mostra "Escaneie ou copie"
    const intro = document.getElementById('pix-intro');
    if (intro) intro.textContent = 'Escaneie o QR Code ou copie a chave.';

    try {
        if (typeof QRCode === 'undefined') {
            console.error("Biblioteca QRCode não carregada.");
            return;
        }
        const tamanho = pixCopiaCola.length > 100 ? 220 : 180;
        new QRCode(qrcodeElement, {
            text: pixCopiaCola,
            width: tamanho,
            height: tamanho,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });
    } catch (e) {
        console.error("Erro ao gerar QR Code.", e);
    }
});