/* =========================
   REPORTS - Relatório de Vendas e Dashboard
========================= */
let dashboardInterval = null;
let financeChartInstance = null;
let financeChartCompareInstance = null;
let productsChartInstance = null;
let productsChartCompareInstance = null;
let growthChartInstance = null;
let growthChartCompareInstance = null;
let categoryChartInstance = null;
let categoryChartCompareInstance = null;

function updateChartsLayout(isComparing, mainLabel, compareLabel) {
    // 1. Finance Chart
    const finContainer = document.getElementById('financeChartContainer');
    const finGrid = document.getElementById('financeChartsGrid');
    const finCompareWrapper = document.getElementById('financeCompareWrapper');
    const finLabelMain = document.getElementById('financeLabelMain');
    const finLabelCompare = document.getElementById('financeLabelCompare');

    if (finContainer && finGrid && finCompareWrapper) {
        if (isComparing) {
            finContainer.classList.remove('col-span-1');
            finContainer.classList.add('md:col-span-2');
            finGrid.classList.remove('grid-cols-1');
            finGrid.classList.add('md:grid-cols-2');
            finCompareWrapper.classList.remove('hidden');
            if (finLabelMain) {
                finLabelMain.classList.remove('hidden');
                finLabelMain.textContent = mainLabel;
            }
            if (finLabelCompare) {
                finLabelCompare.classList.remove('hidden');
                finLabelCompare.textContent = compareLabel;
            }
        } else {
            finContainer.classList.add('col-span-1');
            finContainer.classList.remove('md:col-span-2');
            finGrid.classList.add('grid-cols-1');
            finGrid.classList.remove('md:grid-cols-2');
            finCompareWrapper.classList.add('hidden');
            if (finLabelMain) finLabelMain.classList.add('hidden');
            if (finLabelCompare) finLabelCompare.classList.add('hidden');
        }
    }

    // 2. Products Chart
    const prodContainer = document.getElementById('productsChartContainer');
    const prodGrid = document.getElementById('productsChartsGrid');
    const prodCompareWrapper = document.getElementById('productsCompareWrapper');
    const prodLabelMain = document.getElementById('productsLabelMain');
    const prodLabelCompare = document.getElementById('productsLabelCompare');

    if (prodContainer && prodGrid && prodCompareWrapper) {
        if (isComparing) {
            prodContainer.classList.remove('col-span-1');
            prodContainer.classList.add('md:col-span-2');
            prodGrid.classList.remove('grid-cols-1');
            prodGrid.classList.add('md:grid-cols-2');
            prodCompareWrapper.classList.remove('hidden');
            if (prodLabelMain) {
                prodLabelMain.classList.remove('hidden');
                prodLabelMain.textContent = mainLabel;
            }
            if (prodLabelCompare) {
                prodLabelCompare.classList.remove('hidden');
                prodLabelCompare.textContent = compareLabel;
            }
        } else {
            prodContainer.classList.add('col-span-1');
            prodContainer.classList.remove('md:col-span-2');
            prodGrid.classList.add('grid-cols-1');
            prodGrid.classList.remove('md:grid-cols-2');
            prodCompareWrapper.classList.add('hidden');
            if (prodLabelMain) prodLabelMain.classList.add('hidden');
            if (prodLabelCompare) prodLabelCompare.classList.add('hidden');
        }
    }
}

function updateInsightsLayout(isComparing, mainLabel, compareLabel) {
    // 3. Growth Chart
    const growthContainer = document.getElementById('growthChartContainer');
    const growthGrid = document.getElementById('growthChartsGrid');
    const growthCompareWrapper = document.getElementById('growthCompareWrapper');
    const growthLabelMain = document.getElementById('growthLabelMain');
    const growthLabelCompare = document.getElementById('growthLabelCompare');

    if (growthContainer && growthGrid && growthCompareWrapper) {
        if (isComparing) {
            growthContainer.classList.remove('col-span-1');
            growthContainer.classList.add('md:col-span-2');
            growthGrid.classList.remove('grid-cols-1');
            growthGrid.classList.add('md:grid-cols-2');
            growthCompareWrapper.classList.remove('hidden');
            if (growthLabelMain) {
                growthLabelMain.classList.remove('hidden');
                growthLabelMain.textContent = mainLabel;
            }
            if (growthLabelCompare) {
                growthLabelCompare.classList.remove('hidden');
                growthLabelCompare.textContent = compareLabel;
            }
        } else {
            growthContainer.classList.add('col-span-1');
            growthContainer.classList.remove('md:col-span-2');
            growthGrid.classList.add('grid-cols-1');
            growthGrid.classList.remove('md:grid-cols-2');
            growthCompareWrapper.classList.add('hidden');
            if (growthLabelMain) growthLabelMain.classList.add('hidden');
            if (growthLabelCompare) growthLabelCompare.classList.add('hidden');
        }
    }

    // 4. Category Chart
    const catContainer = document.getElementById('categoryChartContainer');
    const catGrid = document.getElementById('categoryChartsGrid');
    const catCompareWrapper = document.getElementById('categoryCompareWrapper');
    const catLabelMain = document.getElementById('categoryLabelMain');
    const catLabelCompare = document.getElementById('categoryLabelCompare');

    if (catContainer && catGrid && catCompareWrapper) {
        if (isComparing) {
            catContainer.classList.remove('col-span-1');
            catContainer.classList.add('md:col-span-2');
            catGrid.classList.remove('grid-cols-1');
            catGrid.classList.add('md:grid-cols-2');
            catCompareWrapper.classList.remove('hidden');
            if (catLabelMain) {
                catLabelMain.classList.remove('hidden');
                catLabelMain.textContent = mainLabel;
            }
            if (catLabelCompare) {
                catLabelCompare.classList.remove('hidden');
                catLabelCompare.textContent = compareLabel;
            }
        } else {
            catContainer.classList.add('col-span-1');
            catContainer.classList.remove('md:col-span-2');
            catGrid.classList.add('grid-cols-1');
            catGrid.classList.remove('md:grid-cols-2');
            catCompareWrapper.classList.add('hidden');
            if (catLabelMain) catLabelMain.classList.add('hidden');
            if (catLabelCompare) catLabelCompare.classList.add('hidden');
        }
    }
}

async function loadSalesReport() {
    // Carrega dados iniciais
    await updateSalesData();
    if (document.getElementById('growthChart')) {
        await loadInsights(); // Load insights if element exists
    }

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
    // ⏰ Definir data padrão como Hoje para corrigir relatórios vazios exibindo todos os tempos
    const tzOffset = new Date().getTimezoneOffset() * 60000; 
    const todayISO = new Date(Date.now() - tzOffset).toISOString().slice(0, 10);
    
    ['reportDateStart', 'reportDateEnd', 'filterDateStart', 'filterDateEnd'].forEach(id => {
        const el = document.getElementById(id);
        if (el && !el.value) el.value = todayISO;
    });

    if (document.getElementById('totalRevenue') || document.getElementById('salesSummary')) {
        loadSalesReport();
    }
});

async function updateSalesData() {
    try {
        const fetchReport = async (startId, endId) => {
            let url = '/admin/sales/report';
            const start = document.getElementById(startId)?.value;
            const end = document.getElementById(endId)?.value;
            const params = new URLSearchParams();
            if (start) params.append('date_start', start);
            if (end) params.append('date_end', end);
            if (params.toString()) url += '?' + params.toString();
            const res = await fetch(url);
            if (!res.ok) throw new Error('Falha na resposta do servidor');
            return await res.json();
        };

        const report = await fetchReport('reportDateStart', 'reportDateEnd');
        
        let compareReport = null;
        if (document.getElementById('enableCompare')?.checked) {
            const cmpStart = document.getElementById('reportCompareStart')?.value;
            const cmpEnd = document.getElementById('reportCompareEnd')?.value;
            if (cmpStart || cmpEnd) {
                compareReport = await fetchReport('reportCompareStart', 'reportCompareEnd');
            }
        }

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

        const mainStart = document.getElementById('reportDateStart')?.value;
        const mainEnd = document.getElementById('reportDateEnd')?.value;
        let mainLabel = 'Período Principal';
        if (mainStart && mainEnd) {
            const formatD = (d) => {
                const p = d.split('-');
                return p.length === 3 ? `${p[2]}/${p[1]}` : d;
            };
            mainLabel = `Principal (${formatD(mainStart)} a ${formatD(mainEnd)})`;
        }

        const cmpStart = document.getElementById('reportCompareStart')?.value;
        const cmpEnd = document.getElementById('reportCompareEnd')?.value;
        let compareLabel = 'Período Comparativo';
        if (cmpStart && cmpEnd) {
            const formatD = (d) => {
                const p = d.split('-');
                return p.length === 3 ? `${p[2]}/${p[1]}` : d;
            };
            compareLabel = `Comparativo (${formatD(cmpStart)} a ${formatD(cmpEnd)})`;
        }

        const isComparing = compareReport !== null;
        updateChartsLayout(isComparing, mainLabel, compareLabel);

        if (document.getElementById('financeChart') && document.getElementById('productsChart')) {
            updateCharts(report, compareReport);
        }

        // --- Deltas (Compare) ---
        const updateDelta = (elementId, current, previous, invertColors = false) => {
            const el = document.getElementById(elementId);
            if (!el) return;
            if (!previous && previous !== 0) {
                el.innerHTML = '';
                return;
            }

            const diff = current - previous;
            let pct = 0;
            if (previous !== 0) {
                pct = (diff / previous) * 100;
            } else if (current > 0) {
                pct = 100;
            }

            const isPositive = diff > 0;
            const isNegative = diff < 0;
            const absPct = Math.abs(pct).toFixed(1) + '%';
            
            const fmt = (n) => n.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
            const prefix = 'R$ ';
            const diffStr = (isPositive ? '+' : (isNegative ? '-' : '')) + prefix + fmt(Math.abs(diff));
            const prevStr = prefix + fmt(previous);
            
            let colorCls = 'text-gray-500';
            let icon = '=';
            
            if (isPositive) {
                colorCls = invertColors ? 'text-red-500' : 'text-emerald-400';
                icon = '↑';
            } else if (isNegative) {
                colorCls = invertColors ? 'text-emerald-400' : 'text-red-500';
                icon = '↓';
            }

            const cmpStart = document.getElementById('reportCompareStart')?.value;
            const cmpEnd = document.getElementById('reportCompareEnd')?.value;
            let compareLabel = 'Período Comparativo';
            if (cmpStart && cmpEnd) {
                const formatD = (d) => {
                    const p = d.split('-');
                    return p.length === 3 ? `${p[2]}/${p[1]}` : d;
                };
                compareLabel = `${formatD(cmpStart)} a ${formatD(cmpEnd)}`;
            }

            el.className = "w-full mt-3 pt-3 border-t border-gray-700/50 flex flex-col gap-1.5";
            el.innerHTML = `
                <div class="flex justify-between items-center gap-2">
                    <span class="text-[10px] text-gray-500 uppercase font-bold tracking-wider truncate" title="${compareLabel}">Anterior</span>
                    <span class="text-xs text-gray-300 font-bold whitespace-nowrap">${prevStr}</span>
                </div>
                <div class="flex justify-between items-center gap-2">
                    <span class="text-[10px] text-gray-400 truncate">Diferença:</span>
                    <span class="text-xs font-bold whitespace-nowrap ${colorCls}">${diffStr}</span>
                </div>
                <div class="flex justify-between items-center gap-2">
                    <span class="text-[10px] text-gray-400 truncate">Percentual:</span>
                    <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-gray-900/80 border border-current shadow-sm whitespace-nowrap ${colorCls}">${icon} ${absPct}</span>
                </div>
            `;
        };

        if (compareReport) {
            updateDelta('onlineRevenueDelta', report.online.revenue, compareReport.online.revenue);
            updateDelta('manualRevenueDelta', report.manual.revenue, compareReport.manual.revenue);
            updateDelta('totalRevenueDelta', report.summary.total_revenue, compareReport.summary.total_revenue);
            updateDelta('totalCostsDelta', report.summary.total_costs, compareReport.summary.total_costs, true);
            updateDelta('totalProfitDelta', report.summary.total_profit, compareReport.summary.total_profit);
        } else {
            ['onlineRevenueDelta', 'manualRevenueDelta', 'totalRevenueDelta', 'totalCostsDelta', 'totalProfitDelta'].forEach(id => {
                if (document.getElementById(id)) document.getElementById(id).innerHTML = '';
            });
        }

    } catch (err) {
        console.error('Erro ao atualizar relatório:', err);
    }
}

async function loadInsights() {
    try {
        const fetchInsights = async (startId, endId) => {
            let url = '/admin/sales/insights';
            const start = document.getElementById(startId)?.value;
            const end = document.getElementById(endId)?.value;
            const params = new URLSearchParams();
            if (start) params.append('date_start', start);
            if (end) params.append('date_end', end);
            if (params.toString()) url += '?' + params.toString();
            const res = await fetch(url);
            if (!res.ok) throw new Error('Falha na resposta dos Insights');
            return await res.json();
        };

        const data = await fetchInsights('reportDateStart', 'reportDateEnd');
                let compareData = null;
        if (document.getElementById('enableCompare')?.checked) {
            const cmpStart = document.getElementById('reportCompareStart')?.value;
            const cmpEnd = document.getElementById('reportCompareEnd')?.value;
            if (cmpStart || cmpEnd) {
                compareData = await fetchInsights('reportCompareStart', 'reportCompareEnd');
            }
        }

        const isComparing = compareData !== null;
        const mainStart = document.getElementById('reportDateStart')?.value;
        const mainEnd = document.getElementById('reportDateEnd')?.value;
        let mainLabel = 'Período Principal';
        if (mainStart && mainEnd) {
            const formatD = (d) => {
                const p = d.split('-');
                return p.length === 3 ? `${p[2]}/${p[1]}` : d;
            };
            mainLabel = `Principal (${formatD(mainStart)} a ${formatD(mainEnd)})`;
        }

        const cmpStartLabel = document.getElementById('reportCompareStart')?.value;
        const cmpEndLabel = document.getElementById('reportCompareEnd')?.value;
        let compareLabel = 'Período Comparativo';
        if (cmpStartLabel && cmpEndLabel) {
            const formatD = (d) => {
                const p = d.split('-');
                return p.length === 3 ? `${p[2]}/${p[1]}` : d;
            };
            compareLabel = `Comparativo (${formatD(cmpStartLabel)} a ${formatD(cmpEndLabel)})`;
        }

        updateInsightsLayout(isComparing, mainLabel, compareLabel);

        const fmt = (n) => 'R$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits: 2 });

        // Update Ticket Médio
        if (document.getElementById('averageTicket')) {
            document.getElementById('averageTicket').textContent = fmt(data.average_ticket);
            document.getElementById('totalOrders').textContent = data.total_orders + ' pedidos totais';
            
            if (compareData && document.getElementById('averageTicketDelta')) {
                const el = document.getElementById('averageTicketDelta');
                const current = data.average_ticket;
                const previous = compareData.average_ticket;
                if (!previous && previous !== 0) {
                    el.innerHTML = '';
                } else {
                    const diff = current - previous;
                    let pct = 0;
                    if (previous !== 0) {
                        pct = (diff / previous) * 100;
                    } else if (current > 0) {
                        pct = 100;
                    }

                    const isPositive = diff > 0;
                    const isNegative = diff < 0;
                    const absPct = Math.abs(pct).toFixed(1) + '%';
                    
                    const fmt = (n) => n.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                    const prefix = 'R$ ';
                    const diffStr = (isPositive ? '+' : (isNegative ? '-' : '')) + prefix + fmt(Math.abs(diff));
                    const prevStr = prefix + fmt(previous);
                    
                    let colorCls = 'text-gray-500';
                    let icon = '=';
                    if (isPositive) { colorCls = 'text-emerald-400'; icon = '↑'; }
                    else if (isNegative) { colorCls = 'text-red-500'; icon = '↓'; }
                    
                    const cmpStart = document.getElementById('reportCompareStart')?.value;
                    const cmpEnd = document.getElementById('reportCompareEnd')?.value;
                    let compareLabel = 'Período Comparativo';
                    if (cmpStart && cmpEnd) {
                        const formatD = (d) => {
                            const p = d.split('-');
                            return p.length === 3 ? `${p[2]}/${p[1]}` : d;
                        };
                        compareLabel = `${formatD(cmpStart)} a ${formatD(cmpEnd)}`;
                    }

                    el.className = "w-full mt-3 pt-3 border-t border-gray-700/50 flex flex-col gap-1.5";
                    el.innerHTML = `
                        <div class="flex justify-between items-center gap-2">
                            <span class="text-[10px] text-gray-500 uppercase font-bold tracking-wider truncate" title="${compareLabel}">Anterior</span>
                            <span class="text-xs text-gray-300 font-bold whitespace-nowrap">${prevStr}</span>
                        </div>
                        <div class="flex justify-between items-center gap-2">
                            <span class="text-[10px] text-gray-400 truncate">Diferença:</span>
                            <span class="text-xs font-bold whitespace-nowrap ${colorCls}">${diffStr}</span>
                        </div>
                        <div class="flex justify-between items-center gap-2">
                            <span class="text-[10px] text-gray-400 truncate">Percentual:</span>
                            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-gray-900/80 border border-current shadow-sm whitespace-nowrap ${colorCls}">${icon} ${absPct}</span>
                        </div>
                    `;
                }
            } else if (document.getElementById('averageTicketDelta')) {
                document.getElementById('averageTicketDelta').innerHTML = '';
            }
        }

        const fmtCustomerRow = (c) => `
            <tr class="border-b border-gray-700 hover:bg-gray-700/30">
                <td class="p-2">
                    <p class="text-white font-bold">${c.name || 'Desconhecido'}</p>
                    <p class="text-xs text-gray-500">${c.email}</p>
                </td>
                <td class="p-2 text-center text-gray-400">${c.orders_count}</td>
                <td class="p-2 text-right text-yellow-400 font-bold">${fmt(c.total_spent)}</td>
            </tr>
        `;

        // Render Top Customers by Value Table
        const topValueTable = document.getElementById('topCustomersValueTable');
        if (topValueTable) {
            if (data.top_customers_value && data.top_customers_value.length > 0) {
                topValueTable.innerHTML = data.top_customers_value.map(fmtCustomerRow).join('');
            } else {
                topValueTable.innerHTML = '<tr><td colspan="3" class="p-4 text-center text-gray-500">Sem clientes no período</td></tr>';
            }
        }

        // Render Top Customers by Order Count Table
        const topCountTable = document.getElementById('topCustomersCountTable');
        if (topCountTable) {
            if (data.top_customers_count && data.top_customers_count.length > 0) {
                topCountTable.innerHTML = data.top_customers_count.map(fmtCustomerRow).join('');
            } else {
                topCountTable.innerHTML = '<tr><td colspan="3" class="p-4 text-center text-gray-500">Sem clientes no período</td></tr>';
            }
        }

        // Render Stock Alerts Table
        const stockTable = document.getElementById('stockAlertsTable');
        if (stockTable) {
            if (data.stock_alerts && data.stock_alerts.length > 0) {
                stockTable.innerHTML = data.stock_alerts.map((s) => {
                    const criticalLevel = typeof s.days_left === 'number' && s.days_left <= 3 ? 'text-red-500 animate-pulse font-bold' : 'text-orange-400';
                    return `
                    <tr class="border-b border-gray-700 hover:bg-gray-700/30">
                        <td class="p-2 text-white">${s.name}</td>
                        <td class="p-2 text-center text-gray-300 font-bold">${s.keys_available}</td>
                        <td class="p-2 text-center text-gray-400">${s.daily_velocity}/dia</td>
                        <td class="p-2 text-right ${criticalLevel}">${s.days_left} dias</td>
                    </tr>
                `}).join('');
            } else {
                stockTable.innerHTML = '<tr><td colspan="4" class="p-4 text-center text-emerald-500">Estoque saudável ou itens sem volume.</td></tr>';
            }
        }
        // --- Insights Charts (Chart.js) ---
        if (typeof Chart === 'undefined') return;
        Chart.defaults.color = '#9ca3af';

        // 1. Growth Line Chart
        const ctxGrowth = document.getElementById('growthChart')?.getContext('2d');
        if (ctxGrowth && data.sales_over_time) {
            const dateLabels = data.sales_over_time.map(s => {
                const parts = s.date.split('-'); 
                return `${parts[2]}/${parts[1]}`;
            });
            const growthData = {
                labels: dateLabels,
                datasets: [{
                    label: 'Faturamento Total (R$)',
                    data: data.sales_over_time.map(s => s.total),
                    borderColor: 'rgb(192, 38, 211)', // fuchsia-600
                    backgroundColor: 'rgba(192, 38, 211, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }]
            };

            if (growthChartInstance) {
                growthChartInstance.data = growthData;
                growthChartInstance.update();
            } else {
                growthChartInstance = new Chart(ctxGrowth, {
                    type: 'line',
                    data: growthData,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true, grid: { color: 'rgba(75, 85, 99, 0.2)' } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            }
        }

        // 1b. Growth Line Chart Compare
        if (isComparing && compareData && compareData.sales_over_time) {
            const ctxGrowthCompare = document.getElementById('growthChartCompare')?.getContext('2d');
            if (ctxGrowthCompare) {
                const dateLabelsCompare = compareData.sales_over_time.map(s => {
                    const parts = s.date.split('-'); 
                    return `${parts[2]}/${parts[1]}`;
                });
                const growthCompareData = {
                    labels: dateLabelsCompare,
                    datasets: [{
                        label: 'Faturamento Total (R$)',
                        data: compareData.sales_over_time.map(s => s.total),
                        borderColor: 'rgb(192, 38, 211)', // fuchsia-600
                        backgroundColor: 'rgba(192, 38, 211, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    }]
                };

                if (growthChartCompareInstance) {
                    growthChartCompareInstance.data = growthCompareData;
                    growthChartCompareInstance.update();
                } else {
                    growthChartCompareInstance = new Chart(ctxGrowthCompare, {
                        type: 'line',
                        data: growthCompareData,
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { beginAtZero: true, grid: { color: 'rgba(75, 85, 99, 0.2)' } },
                                x: { grid: { display: false } }
                            }
                        }
                    });
                }
            }
        } else {
            if (growthChartCompareInstance) {
                growthChartCompareInstance.destroy();
                growthChartCompareInstance = null;
            }
        }

        // 2. Category Profits Chart
        const ctxCategory = document.getElementById('categoryChart')?.getContext('2d');
        if (ctxCategory && data.category_profits) {
            const catLabels = data.category_profits.map(c => c.category);
            const catRevenues = data.category_profits.map(c => c.revenue);
            const catProfits = data.category_profits.map(c => c.profit);

            const catData = {
                labels: catLabels,
                datasets: [
                    {
                        label: 'Receita (R$)',
                        data: catRevenues,
                        backgroundColor: 'rgba(56, 189, 248, 0.6)', // sky
                        borderWidth: 0
                    },
                    {
                        label: 'Lucro (R$)',
                        data: catProfits,
                        backgroundColor: 'rgba(52, 211, 153, 0.6)', // emerald
                        borderWidth: 0
                    }
                ]
            };

            if (categoryChartInstance) {
                categoryChartInstance.data = catData;
                categoryChartInstance.update();
            } else {
                categoryChartInstance = new Chart(ctxCategory, {
                    type: 'bar',
                    data: catData,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { position: 'top', labels: { color: '#9ca3af' } } },
                        scales: {
                            y: { beginAtZero: true, grid: { color: 'rgba(75, 85, 99, 0.2)' } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            }
        }

        // 2b. Category Profits Chart Compare
        if (isComparing && compareData && compareData.category_profits) {
            const ctxCategoryCompare = document.getElementById('categoryChartCompare')?.getContext('2d');
            if (ctxCategoryCompare) {
                const catLabelsCompare = compareData.category_profits.map(c => c.category);
                const catRevenuesCompare = compareData.category_profits.map(c => c.revenue);
                const catProfitsCompare = compareData.category_profits.map(c => c.profit);

                const catCompareData = {
                    labels: catLabelsCompare,
                    datasets: [
                        {
                            label: 'Receita (R$)',
                            data: catRevenuesCompare,
                            backgroundColor: 'rgba(56, 189, 248, 0.6)', // sky
                            borderWidth: 0
                        },
                        {
                            label: 'Lucro (R$)',
                            data: catProfitsCompare,
                            backgroundColor: 'rgba(52, 211, 153, 0.6)', // emerald
                            borderWidth: 0
                        }
                    ]
                };

                if (categoryChartCompareInstance) {
                    categoryChartCompareInstance.data = catCompareData;
                    categoryChartCompareInstance.update();
                } else {
                    categoryChartCompareInstance = new Chart(ctxCategoryCompare, {
                        type: 'bar',
                        data: catCompareData,
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { position: 'top', labels: { color: '#9ca3af' } } },
                            scales: {
                                y: { beginAtZero: true, grid: { color: 'rgba(75, 85, 99, 0.2)' } },
                                x: { grid: { display: false } }
                            }
                        }
                    });
                }
            }
        } else {
            if (categoryChartCompareInstance) {
                categoryChartCompareInstance.destroy();
                categoryChartCompareInstance = null;
            }
        }
    } catch (err) {
        console.error('Erro ao buscar insights:', err);
    }
}
function updateCharts(report, compareReport) {
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

    // 1b. Finance Chart Compare (Bar)
    if (compareReport) {
        const ctxFinanceCompare = document.getElementById('financeChartCompare').getContext('2d');
        const financeCompareData = {
            labels: ['Faturamento Total', 'Custos Totais', 'Lucro Líquido'],
            datasets: [{
                label: 'Valores (R$)',
                data: [
                    compareReport.summary.total_revenue,
                    compareReport.summary.total_costs,
                    compareReport.summary.total_profit
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

        if (financeChartCompareInstance) {
            financeChartCompareInstance.data = financeCompareData;
            financeChartCompareInstance.update();
        } else {
            financeChartCompareInstance = new Chart(ctxFinanceCompare, {
                type: 'bar',
                data: financeCompareData,
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
    } else {
        if (financeChartCompareInstance) {
            financeChartCompareInstance.destroy();
            financeChartCompareInstance = null;
        }
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

    // 2b. Products Chart Compare (Doughnut) - Top 5
    if (compareReport) {
        const ctxProductsCompare = document.getElementById('productsChartCompare').getContext('2d');
        const sortedByQtdCompare = [...(compareReport.by_product || [])].sort((a, b) => b.quantity - a.quantity).slice(0, 5);
        const pLabelsCompare = sortedByQtdCompare.map(p => p.name);
        const pDataCompare = sortedByQtdCompare.map(p => p.quantity);

        const productsCompareData = {
            labels: pLabelsCompare,
            datasets: [{
                data: pDataCompare,
                backgroundColor: [
                    'rgba(56, 189, 248, 0.7)',
                    'rgba(167, 139, 250, 0.7)',
                    'rgba(251, 146, 60, 0.7)',
                    'rgba(244, 114, 182, 0.7)',
                    'rgba(250, 204, 21, 0.7)'
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

        if (productsChartCompareInstance) {
            productsChartCompareInstance.data = productsCompareData;
            productsChartCompareInstance.update();
        } else {
            productsChartCompareInstance = new Chart(ctxProductsCompare, {
                type: 'doughnut',
                data: productsCompareData,
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
    } else {
        if (productsChartCompareInstance) {
            productsChartCompareInstance.destroy();
            productsChartCompareInstance = null;
        }
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
