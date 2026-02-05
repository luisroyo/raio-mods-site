/* =========================
   REPORTS - Relatório de Vendas
========================= */

async function loadSalesReport() {
    try {
        const res = await fetch('/admin/sales/report');
        const report = await res.json();

        const fmt = (n) => 'R$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
        const fmtUSD = (n) => '$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits: 2 });

        // Online
        document.getElementById('onlineRevenue').textContent = fmt(report.online.revenue);
        document.getElementById('onlineCount').textContent = report.online.count + ' vendas';

        // Manual
        document.getElementById('manualRevenue').textContent = fmt(report.manual.revenue);
        document.getElementById('manualCount').textContent = report.manual.count + ' vendas';

        // Totais
        const totalCount = report.online.count + report.manual.count;
        document.getElementById('totalRevenue').textContent = fmt(report.summary.total_revenue);
        document.getElementById('totalCount').textContent = totalCount + ' vendas';

        document.getElementById('totalCosts').textContent = fmt(report.summary.total_costs);

        const profitElement = document.getElementById('totalProfit');
        profitElement.textContent = fmt(report.summary.total_profit);
        profitElement.className = report.summary.total_profit >= 0
            ? 'text-2xl font-bold text-green-500'
            : 'text-2xl font-bold text-red-500';

        document.getElementById('marginProfit').textContent = report.summary.profit_margin + '%';

    } catch (err) {
        console.error('Erro ao carregar relatório:', err);
    }
}
