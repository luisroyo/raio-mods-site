/* =========================
   REPORTS - Relatório de Vendas e Dashboard
========================= */
let dashboardInterval = null;
let financeChartInstance = null;
let productsChartInstance = null;

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

// Auto-initialize on load if elements exist
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('totalRevenue') || document.getElementById('salesSummary')) {
        loadSalesReport();
    }
});

async function updateSalesData() {
    try {
        let url = '/admin/sales/report';
        const start = document.getElementById('reportDateStart')?.value;
        const end = document.getElementById('reportDateEnd')?.value;
        
        const params = new URLSearchParams();
        if (start) params.append('date_start', start);
        if (end) params.append('date_end', end);
        
        if (params.toString()) {
            url += '?' + params.toString();
        }

        const res = await fetch(url);
        if (!res.ok) throw new Error('Falha na resposta do servidor');
        
        const report = await res.json();

        const fmt = (n) => 'R$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
        // const fmtUSD = (n) => '$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits: 2 });

        // Online & Manual (Upper Cards in Sales / Bottom Cards in Dashboard)
        if (document.getElementById('onlineRevenue')) 
            document.getElementById('onlineRevenue').textContent = fmt(report.online.revenue);
        
        if (document.getElementById('manualRevenue')) 
            document.getElementById('manualRevenue').textContent = fmt(report.manual.revenue);

        // Totais
        const totalCount = report.online.count + report.manual.count;
        const sumCosts = report.summary.total_costs;
        const sumProfit = report.summary.total_profit;

        if (document.getElementById('totalRevenue')) 
            document.getElementById('totalRevenue').textContent = fmt(report.summary.total_revenue);
        
        if (document.getElementById('totalCount')) 
            document.getElementById('totalCount').textContent = totalCount;

        // Custos (Regime de Caixa)
        if (document.getElementById('totalCosts')) 
            document.getElementById('totalCosts').textContent = fmt(sumCosts);

        // Atualiza Lucros
        
        // 1. Cartão Inferior (Vendas Page) e Cartão de Lucro (Dashboard)
        const profitElements = ['totalProfit', 'mainProfit'];
        
        profitElements.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = fmt(sumProfit);
                el.classList.remove('text-emerald-400', 'text-red-500'); // Reset colors
                el.classList.add(sumProfit >= 0 ? 'text-emerald-400' : 'text-red-500');
            }
        });

        // Atualiza contadores específicos (Vendas Page)
        if (document.getElementById('onlineCount'))
            document.getElementById('onlineCount').textContent = report.online.count + ' vendas';

        if (document.getElementById('manualCount'))
            document.getElementById('manualCount').textContent = report.manual.count + ' vendas';

        // Atualiza Margem de Lucro (Vendas Page)
        if (document.getElementById('marginProfit')) {
            const margin = report.summary.profit_margin;
            const marginEl = document.getElementById('marginProfit');
            marginEl.textContent = margin + '%';
            marginEl.classList.remove('text-emerald-400', 'text-red-500', 'text-gray-500');
            
            if (margin > 0) marginEl.classList.add('text-emerald-400');
            else if (margin < 0) marginEl.classList.add('text-red-500');
            else marginEl.classList.add('text-gray-500');
        }

        // 3. Detalhes (Dashboard)
        // Atualizados para refletir Regime de Caixa
        if (document.getElementById('detailOnlineRev')) 
            document.getElementById('detailOnlineRev').textContent = fmt(report.online.revenue);

        if (document.getElementById('detailManualRev')) 
            document.getElementById('detailManualRev').textContent = fmt(report.manual.revenue);

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

        // Update Product Performance Table
        const productTable = document.getElementById('productPerformanceTable');
        if (productTable && report.by_product) {
            if (report.by_product.length === 0) {
                productTable.innerHTML = '<tr><td colspan="4" class="p-4 text-center text-gray-500">Nenhuma venda registrada</td></tr>';
            } else {
                productTable.innerHTML = report.by_product.map((p, index) => `
                    <tr class="border-b border-gray-700 hover:bg-gray-700/50">
                        <td class="p-3 text-center text-gray-400 font-bold">#${index + 1}</td>
                        <td class="p-3 text-white">${p.name}</td>
                        <td class="p-3 text-center text-cyan-400 font-bold">${p.quantity}</td>
                        <td class="p-3 text-right text-green-400">R$ ${p.total.toFixed(2)}</td>
                    </tr>
                `).join('');
            }
        }

        // Update Charts if canvas exists
        if (document.getElementById('financeChart') && document.getElementById('productsChart')) {
            updateCharts(report);
        }

    } catch (err) {
        console.error('Erro ao atualizar relatório:', err);
    }
}

function updateCharts(report) {
    if (typeof Chart === 'undefined') return;

    // Chart.js Default Texts Colors for Dark Theme
    Chart.defaults.color = '#9ca3af';

    // 1. Finance Chart (Bar)
    const ctxFinance = document.getElementById('financeChart').getContext('2d');
    const financeData = {
        labels: ['Faturamento Total', 'Custos Totais', 'Lucro Líquido'],
        datasets: [{
            label: 'Valores (R$)',
            data: [
                report.summary.total_revenue,
                report.summary.total_costs,
                report.summary.total_profit
            ],
            backgroundColor: [
                'rgba(34, 197, 94, 0.5)',   // Faturamento (Green)
                'rgba(239, 68, 68, 0.5)',   // Custo (Red)
                'rgba(16, 185, 129, 0.7)'   // Lucro (Emerald)
            ],
            borderColor: [
                'rgb(34, 197, 94)',
                'rgb(239, 68, 68)',
                'rgb(16, 185, 129)'
            ],
            borderWidth: 1
        }]
    };

    if (financeChartInstance) {
        financeChartInstance.data = financeData;
        financeChartInstance.update();
    } else {
        financeChartInstance = new Chart(ctxFinance, {
            type: 'bar',
            data: financeData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(75, 85, 99, 0.2)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    // 2. Products Chart (Doughnut) - Top 5
    const ctxProducts = document.getElementById('productsChart').getContext('2d');
    
    // Sort and slice top 5 products by quantity
    const sortedByQtd = [...(report.by_product || [])].sort((a, b) => b.quantity - a.quantity).slice(0, 5);
    const pLabels = sortedByQtd.map(p => p.name);
    const pData = sortedByQtd.map(p => p.quantity);
    
    const productsData = {
        labels: pLabels,
        datasets: [{
            data: pData,
            backgroundColor: [
                'rgba(56, 189, 248, 0.7)',  // sky
                'rgba(167, 139, 250, 0.7)', // purple
                'rgba(251, 146, 60, 0.7)',  // orange
                'rgba(244, 114, 182, 0.7)', // pink
                'rgba(250, 204, 21, 0.7)'   // yellow
            ],
            borderColor: [
                'rgb(56, 189, 248)',
                'rgb(167, 139, 250)',
                'rgb(251, 146, 60)',
                'rgb(244, 114, 182)',
                'rgb(250, 204, 21)'
            ],
            borderWidth: 1
        }]
    };

    if (productsChartInstance) {
        productsChartInstance.data = productsData;
        productsChartInstance.update();
    } else {
        productsChartInstance = new Chart(ctxProducts, {
            type: 'doughnut',
            data: productsData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        position: 'right',
                        labels: {
                            color: '#9ca3af',
                            font: { size: 11 }
                        }
                    }
                }
            }
        });
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
