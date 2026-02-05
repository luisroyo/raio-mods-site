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

    // Setup functions from modules (verificar se existem antes de chamar)
    if (typeof setupFormListeners === 'function') setupFormListeners();
    if (typeof setupMobileMenu === 'function') setupMobileMenu();
    if (typeof setupKeyForm === 'function') setupKeyForm();
    if (typeof setupManualSaleForm === 'function') setupManualSaleForm();
    if (typeof setupPanelRechargeForm === 'function') setupPanelRechargeForm();

});

/* =========================
   CARREGAR DADOS AO INICIAR
========================= */

window.addEventListener('load', () => {
    setTimeout(() => {
        if (typeof loadManualSales === 'function') loadManualSales();
        if (typeof loadPanelRecharges === 'function') loadPanelRecharges();
        if (typeof loadSalesReport === 'function') loadSalesReport();
    }, 500);
});