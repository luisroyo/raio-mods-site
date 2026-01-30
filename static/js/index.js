document.addEventListener('DOMContentLoaded', () => {
    // Inicializa animações se ainda não foram iniciadas no base.html
    if (typeof AOS !== 'undefined') {
        AOS.init();
    }

    console.log('Index JS carregado com sucesso!');

    // Exemplo: Você pode adicionar lógica de clique aqui no futuro
    // const buyButtons = document.querySelectorAll('.btn-buy');
    // buyButtons.forEach(btn => { ... });
});