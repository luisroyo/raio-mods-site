/* =========================
   ADMIN.JS - Main Entry Point
   
   Este arquivo inicializa todos os módulos.
   Os módulos são carregados via <script> tags separadas.
========================= */

document.addEventListener('DOMContentLoaded', () => {

    /* =========================
        INIT
    ========================= */

    if (typeof AOS !== 'undefined') {
        AOS.init({ duration: 800, easing: 'ease-in-out', once: true });
    }

    // Setup functions from modules
    setupFormListeners();
    setupMobileMenu();
    setupKeyForm();
    setupManualSaleForm();
    setupPanelRechargeForm();

});

/* =========================
   CARREGAR DADOS AO INICIAR
========================= */

window.addEventListener('load', () => {
    setTimeout(() => {
        loadManualSales();
        loadPanelRecharges();
        loadSalesReport();
    }, 500);
});