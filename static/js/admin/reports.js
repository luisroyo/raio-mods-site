/* =========================
   REPORTS - Relatório de Vendas e Dashboard
========================= */

let dashboardInterval = null;

async function loadSalesReport() {
    // Carrega dados iniciais
    await updateSalesData();

    // Configura atualização automática se não estiver configurada (evita duplicação)
    if (!dashboardInterval) {
        // Atualiza a cada 30 segundos
        dashboardInterval = setInterval(updateSalesData, 30000);
        console.log('Auto-refresh do dashboard iniciado (30s)');

        // Configura listener do botão de atualizar dólar
        setupDollarRefresh();
    }
}

async function updateSalesData() {
    try {
        const res = await fetch('/admin/sales/report');
        if (!res.ok) throw new Error('Falha na resposta do servidor');
        
        const report = await res.json();

        const fmt = (n) => 'R$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
        // const fmtUSD = (n) => '$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits: 2 });

        // Online
        const elOnlineRev = document.getElementById('onlineRevenue');
        if (elOnlineRev) elOnlineRev.textContent = fmt(report.online.revenue);
        // document.getElementById('onlineCount').textContent = report.online.count + ' vendas';

        // Manual
        const elManualRev = document.getElementById('manualRevenue');
        if (elManualRev) elManualRev.textContent = fmt(report.manual.revenue);
        // document.getElementById('manualCount').textContent = report.manual.count + ' vendas';

        // Totais
        const totalCount = report.online.count + report.manual.count;
        const sumCosts = report.summary.total_costs;
        const sumProfit = report.summary.total_profit;

        const elTotalRev = document.getElementById('totalRevenue');
        if (elTotalRev) elTotalRev.textContent = fmt(report.summary.total_revenue);
        
        const elTotalCount = document.getElementById('totalCount');
        if (elTotalCount) elTotalCount.textContent = totalCount;

        const elTotalCosts = document.getElementById('totalCosts');
        if (elTotalCosts) elTotalCosts.textContent = fmt(sumCosts);

        // Atualiza Lucros (Cartão Principal + Lista inferior + Detalhes)
        const profitClass = sumProfit >= 0 ? 'text-emerald-400' : 'text-red-500';
        const profitUncheckedClass = sumProfit >= 0 ? 'text-emerald-400' : 'text-red-500'; // Class string without 'text-2xl font-bold' etc if needed, or just replace classList

        // 1. Cartão Inferior
        const profitElement = document.getElementById('totalProfit');
        if (profitElement) {
            profitElement.textContent = fmt(sumProfit);
            profitElement.className = 'text-2xl font-bold ' + profitClass;
        }

        // 2. Cartão Superior (Main Profit)
        const mainProfit = document.getElementById('mainProfit');
        if (mainProfit) {
            mainProfit.textContent = fmt(sumProfit);
            // Preserva classes base que não são de cor, assumindo que a cor é a última ou controlada. 
            // Simplificando: resetar classes de cor.
            mainProfit.classList.remove('text-emerald-400', 'text-red-500');
            mainProfit.classList.add(sumProfit >= 0 ? 'text-emerald-400' : 'text-red-500');
        }

        // 3. Detalhes
        // Custo Produtos = (Online total cost - panel fees if any?) -> Actually report.online.cost_brl + report.manual.cost_brl
        // Mas report.summary.total_costs = online_cost + manual_cost + report.panel.total_cost_brl
        const costProducts = (report.online.cost_brl || 0) + (report.manual.cost_brl || 0);
        const costPanel = report.panel.total_cost_brl || 0;

        if (document.getElementById('detailCostProducts')) 
            document.getElementById('detailCostProducts').textContent = fmt(costProducts);
        
        if (document.getElementById('detailCostPanel')) 
            document.getElementById('detailCostPanel').textContent = fmt(costPanel);

        if (document.getElementById('detailDolar')) 
            document.getElementById('detailDolar').textContent = report.summary.dolar_rate;

        if (document.getElementById('detailRevenue')) 
            document.getElementById('detailRevenue').textContent = fmt(report.summary.total_revenue);

        if (document.getElementById('detailTotalCosts')) 
            document.getElementById('detailTotalCosts').textContent = fmt(sumCosts);

        const detailProfit = document.getElementById('detailProfit');
        if (detailProfit) detailProfit.textContent = fmt(sumProfit);

        const detailProfitLine = document.getElementById('detailProfitLine');
        if (detailProfitLine) {
            detailProfitLine.classList.remove('text-emerald-400', 'text-red-500');
            detailProfitLine.classList.add(sumProfit >= 0 ? 'text-emerald-400' : 'text-red-500');
        }

    } catch (err) {
        console.error('Erro ao atualizar relatório:', err);
    }
}

function setupDollarRefresh() {
    const btn = document.getElementById('refresh_dolar');
    if (!btn) return;

    btn.addEventListener('click', async (e) => {
        e.preventDefault();
        btn.classList.add('animate-spin'); // Tailwind utility

        try {
            const res = await fetch('/admin/debug/dolar');
            const data = await res.json();

            // Atualiza valor (mantendo o "R$ " que está no HTML fora do span)
            const valEl = document.getElementById('dolarValue');
            if (valEl) {
                valEl.textContent = parseFloat(data.dolar_rate).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
            }

            // Atualiza data
            const dateEl = document.getElementById('dolarUpdated');
            if (dateEl) {
                // Converte timestamp (s) para milissegundos
                const date = new Date(data.timestamp * 1000);
                // Formato: YYYY-MM-DD HH:MM:SS
                const formatted = date.getFullYear() + '-' +
                    String(date.getMonth() + 1).padStart(2, '0') + '-' +
                    String(date.getDate()).padStart(2, '0') + ' ' +
                    String(date.getHours()).padStart(2, '0') + ':' +
                    String(date.getMinutes()).padStart(2, '0') + ':' +
                    String(date.getSeconds()).padStart(2, '0');
                
                dateEl.textContent = formatted;
            }

        } catch (err) {
            console.error('Erro ao atualizar dólar:', err);
            alert('Erro ao atualizar cotação do dólar');
        } finally {
            setTimeout(() => btn.classList.remove('animate-spin'), 500);
        }
    });
}
