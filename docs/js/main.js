// A股市场数据可视化主脚本

// 全局变量
let indicesChart = null;
let stocksChart = null;
let indicesData = {};
let stocksData = {};

// 颜色配置
const COLORS = [
    '#2563eb', '#dc2626', '#16a34a', '#ea580c', '#9333ea',
    '#0891b2', '#db2777', '#65a30d', '#ca8a04', '#7c3aed'
];

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setupEventListeners();
});

// 加载数据
async function loadData() {
    try {
        // 加载汇总信息
        const summary = await fetchJSON('data/summary.json');
        updateSummary(summary);

        // 加载指数数据
        indicesData = await fetchJSON('data/indices.json');
        renderIndicesChart();
        renderIndicesLegend();

        // 加载股票数据
        stocksData = await fetchJSON('data/stocks.json');
        renderStocksChart();
        renderStocksLegend();

    } catch (error) {
        console.error('加载数据失败:', error);
        showError('数据加载失败,请稍后重试');
    }
}

// 获取JSON数据
async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// 更新汇总信息
function updateSummary(summary) {
    document.getElementById('indices-count').textContent = summary.indices_count || 0;
    document.getElementById('stocks-count').textContent = summary.stocks_count || 0;
    document.getElementById('trading-period').textContent = formatTradingPeriod(summary.trading_period);
    document.getElementById('last-update').textContent = summary.last_update || '-';
}

// 格式化交易周期
function formatTradingPeriod(period) {
    if (!period) return '-';
    const [start, end] = period.split(' - ');
    return `${formatDate(start)} - ${formatDate(end)}`;
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '';
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    return `${year}-${month}-${day}`;
}

// 渲染指数图表
function renderIndicesChart() {
    const ctx = document.getElementById('indices-chart').getContext('2d');
    const datasets = Object.entries(indicesData).map(([code, data], index) => {
        return {
            label: data.name,
            data: data.data.map(d => ({
                x: formatDate(d.date),
                y: d.close
            })),
            borderColor: COLORS[index % COLORS.length],
            backgroundColor: COLORS[index % COLORS.length] + '20',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.1
        };
    });

    indicesChart = new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'category',
                    ticks: {
                        maxTicksLimit: 10,
                        autoSkip: true
                    }
                },
                y: {
                    type: 'linear',
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

// 渲染股票图表
function renderStocksChart() {
    const ctx = document.getElementById('stocks-chart').getContext('2d');
    const datasets = Object.entries(stocksData).map(([code, data], index) => {
        // 计算归一化值 (以第一天为基准100)
        const firstValue = data.data[0].close;
        return {
            label: data.name,
            data: data.data.map(d => ({
                x: formatDate(d.date),
                y: (d.close / firstValue) * 100
            })),
            borderColor: COLORS[index % COLORS.length],
            backgroundColor: COLORS[index % COLORS.length] + '20',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.1
        };
    });

    stocksChart = new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'category',
                    ticks: {
                        maxTicksLimit: 10,
                        autoSkip: true
                    }
                },
                y: {
                    type: 'linear',
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2) + '%';
                        }
                    }
                }
            }
        }
    });
}

// 渲染指数图例
function renderIndicesLegend() {
    const container = document.getElementById('indices-legend');
    container.innerHTML = '';

    Object.entries(indicesData).forEach(([code, data], index) => {
        const item = createLegendItem(data, COLORS[index % COLORS.length]);
        container.appendChild(item);
    });
}

// 渲染股票图例
function renderStocksLegend() {
    const container = document.getElementById('stocks-legend');
    container.innerHTML = '';

    Object.entries(stocksData).forEach(([code, data], index) => {
        const item = createLegendItem(data, COLORS[index % COLORS.length], true);
        container.appendChild(item);
    });
}

// 创建图例项
function createLegendItem(data, color, showIndustry = false) {
    const div = document.createElement('div');
    div.className = 'legend-item';

    const metrics = data.metrics || {};
    const returnValue = metrics.total_return || 0;
    const returnClass = returnValue >= 0 ? 'positive' : 'negative';

    div.innerHTML = `
        <div class="legend-header">
            <div class="legend-color" style="background-color: ${color}"></div>
            <div class="legend-name">${data.name}</div>
            <div class="legend-code">${data.code}</div>
        </div>
        <div class="legend-stats">
            <div class="stat-item">
                <div class="stat-label">累计收益</div>
                <div class="stat-value ${returnClass}">${returnValue >= 0 ? '+' : ''}${returnValue.toFixed(2)}%</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">最大回撤</div>
                <div class="stat-value negative">-${(metrics.max_drawdown || 0).toFixed(2)}%</div>
            </div>
            ${showIndustry && data.industry ? `
            <div class="stat-item">
                <div class="stat-label">所属行业</div>
                <div class="stat-value neutral">${data.industry}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">市值(亿)</div>
                <div class="stat-value neutral">${(data.market_value / 10000).toFixed(2)}</div>
            </div>
            ` : ''}
        </div>
    `;

    return div;
}

// 设置事件监听
function setupEventListeners() {
    // 指数图表比例切换
    document.getElementById('linear-scale-indices')?.addEventListener('change', (e) => {
        if (indicesChart) {
            indicesChart.options.scales.y.type = e.target.checked ? 'linear' : 'logarithmic';
            indicesChart.update();
        }
    });

    // 股票图表比例切换
    document.getElementById('linear-scale-stocks')?.addEventListener('change', (e) => {
        if (stocksChart) {
            stocksChart.options.scales.y.type = e.target.checked ? 'linear' : 'logarithmic';
            stocksChart.update();
        }
    });
}

// 导出数据
function exportData(type) {
    const data = type === 'indices' ? indicesData : stocksData;
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${type}_data_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 显示错误
function showError(message) {
    const sections = ['indices-legend', 'stocks-legend'];
    sections.forEach(id => {
        const container = document.getElementById(id);
        if (container) {
            container.innerHTML = `<div class="error">${message}</div>`;
        }
    });
}
