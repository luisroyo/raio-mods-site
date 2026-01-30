document.addEventListener('DOMContentLoaded', () => {
    // Inicializa AOS globalmente se estiver carregado
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
            once: true
        });
    }
    console.log("Base JS carregado.");
});