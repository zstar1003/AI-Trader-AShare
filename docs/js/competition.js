// AI-Trader Competition Dashboard

let globalAgentData = {};
let chart = null;
let pieChart = null;

// 名称映射：将内部名称转换为显示名称
const AGENT_NAME_MAP = {
    'DeepSeek_Trader': 'DeepSeek',
    'GLM_Trader': 'GLM',
    'Kimi_Trader': 'Kimi',
    'Ring_Trader': 'Ring'
};

// 股票代码到名称的映射
const STOCK_NAME_MAP = {
    '000001.SZ': '平安银行',
    '000002.SZ': '万科A',
    '000157.SZ': '中联重科',
    '000333.SZ': '美的集团',
    '000538.SZ': '云南白药',
    '000858.SZ': '五粮液',
    '000977.SZ': '浪潮信息',
    '002271.SZ': '东方雨虹',
    '002415.SZ': '海康威视',
    '002475.SZ': '立讯精密',
    '002594.SZ': '比亚迪',
    '300059.SZ': '东方财富',
    '300750.SZ': '宁德时代',
    '600000.SH': '浦发银行',
    '600036.SH': '招商银行',
    '600309.SH': '万华化学',
    '600438.SH': '通威股份',
    '600519.SH': '贵州茅台',
    '600887.SH': '伊利股份',
    '601318.SH': '中国平安',
    '603259.SH': '药明康德',
    '600276.SH': '恒瑞医药',
    '000651.SZ': '格力电器',
    '601012.SH': '隆基绿能'
};

// 获取显示名称
function getDisplayName(agentName) {
    return AGENT_NAME_MAP[agentName] || agentName;
}

// 获取股票名称
function getStockName(ts_code) {
    return STOCK_NAME_MAP[ts_code] || ts_code;
}

// 初始化
document.addEventListener('DOMContentLoaded', async() => {
    // 先设置Tab切换功能（不依赖数据）
    setupTabs();

    // 再加载数据并渲染
    await loadAgentData();
    renderDashboard();
});

// 加载Agent数据
async function loadAgentData() {
    try {
        // 所有可能的Agent文件
        const agentFiles = [
            'DeepSeek_Trader',
            'GLM_Trader',
            'Kimi_Trader',
            'Ring_Trader'
        ];

        for (const agentName of agentFiles) {
            try {
                // 首先尝试从 data/agent_data/ 加载
                let response = await fetch(`../data/agent_data/${agentName}_state.json`);
                if (!response.ok) {
                    // 如果失败，尝试从 docs/data/ 加载
                    response = await fetch(`data/${agentName}_state.json`);
                }

                if (response.ok) {
                    const data = await response.json();
                    globalAgentData[agentName] = data;
                }
            } catch (e) {
                console.warn(`Failed to load ${agentName}:`, e);
            }
        }

        // 加载上证指数数据
        try {
            let response = await fetch(`../data/index_benchmark.json`);
            if (!response.ok) {
                response = await fetch(`data/index_benchmark.json`);
            }
            if (response.ok) {
                const indexData = await response.json();
                window.indexBenchmark = indexData;
                console.log('Loaded index benchmark data');
            }
        } catch (e) {
            console.warn('Failed to load index benchmark:', e);
        }

        console.log('Loaded agent data:', Object.keys(globalAgentData));
    } catch (error) {
        console.error('Error loading agent data:', error);
    }
}

// 渲染整个Dashboard
function renderDashboard() {
    if (Object.keys(globalAgentData).length === 0) {
        showError('暂无数据');
        return;
    }

    // 更新统计信息
    updateStats();

    // 渲染图表
    renderChart();

    // 渲染排行榜
    renderRankings();

    // 渲染交易记录
    setupTradesList();

    // 渲染持仓情况
    setupPositionsList();
}

// 更新顶部统计
function updateStats() {
    const agentCount = Object.keys(globalAgentData).length;
    const returns = Object.values(globalAgentData).map(agent => {
        const dailyValues = Object.values(agent.daily_snapshots || {});
        if (dailyValues.length === 0) return 0;
        const lastValue = dailyValues[dailyValues.length - 1];
        return ((lastValue.total_value - agent.initial_capital) / agent.initial_capital * 100);
    });
    const bestReturn = Math.max(...returns);

    // 计算交易周期
    const firstAgent = Object.values(globalAgentData)[0];
    const startDate = firstAgent.simulation_start_date || '-';

    // 使用最后一个快照的日期作为结束日期
    const snapshotDates = Object.keys(firstAgent.daily_snapshots || {}).sort();
    const endDate = snapshotDates.length > 0 ? snapshotDates[snapshotDates.length - 1] : '-';

    const tradingPeriod = formatTradingPeriod(startDate, endDate);

    document.getElementById('agents-count').textContent = agentCount;
    document.getElementById('trading-period').textContent = tradingPeriod;

    const bestReturnEl = document.getElementById('best-return');
    bestReturnEl.textContent = `${bestReturn >= 0 ? '+' : ''}${bestReturn.toFixed(2)}%`;
    bestReturnEl.className = `stat-value ${bestReturn >= 0 ? 'positive' : 'negative'}`;

    // 更新最后更新时间
    const lastUpdate = firstAgent.last_update || '-';
    document.getElementById('last-update').textContent = lastUpdate;
}

// 格式化交易周期
function formatTradingPeriod(startDate, endDate) {
    if (!startDate || !endDate) return '-';
    const start = formatDate(startDate);
    const end = formatDate(endDate);

    // 计算交易日数量 (实际数据中的交易日数量)
    const snapshots = Object.values(globalAgentData)[0].daily_snapshots;
    const tradingDays = snapshots ? Object.keys(snapshots).length : 0;

    // 显示为交易日数量 - 2 (可能不包含首尾或其他业务逻辑)
    const displayDays = tradingDays > 2 ? tradingDays - 2 : tradingDays;

    return `${displayDays}天 (${start} - ${end})`;
}

// 渲染图表
function renderChart() {
    const ctx = document.getElementById('performance-chart').getContext('2d');

    const datasets = [];
    const colors = [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'
    ];

    let colorIndex = 0;
    for (const [agentName, agent] of Object.entries(globalAgentData)) {
        const snapshots = agent.daily_snapshots || {};
        const dates = Object.keys(snapshots).sort();

        const data = dates.map(date => {
            const snapshot = snapshots[date];
            const returnPct = ((snapshot.total_value - agent.initial_capital) / agent.initial_capital * 100);
            return returnPct;
        });

        datasets.push({
            label: getDisplayName(agentName),
            data: data,
            borderColor: colors[colorIndex % colors.length],
            backgroundColor: colors[colorIndex % colors.length] + '20',
            borderWidth: 2,
            tension: 0.4,
            pointRadius: 3,
            pointHoverRadius: 5
        });

        colorIndex++;
    }

    // Add index benchmark line
    if (window.indexBenchmark && window.indexBenchmark.daily_data) {
        const benchmarkData = window.indexBenchmark.daily_data.map(d => d.return_pct);
        datasets.push({
            label: '上证指数 (基准)',
            data: benchmarkData,
            borderColor: '#000000',
            backgroundColor: '#00000010',
            borderWidth: 2.5,
            tension: 0.4,
            pointRadius: 3,
            pointHoverRadius: 5
        });
    }

    // 获取日期标签
    const firstAgent = Object.values(globalAgentData)[0];
    const dates = Object.keys(firstAgent.daily_snapshots || {}).sort();
    const labels = dates.map(date => formatDate(date));

    if (chart) {
        chart.destroy();
    }

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y >= 0 ? '+' : ''}${context.parsed.y.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(1) + '%';
                        }
                    },
                    grid: {
                        color: '#e2e8f0'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });

    // 设置agent selector
    const agentSelector = document.getElementById('agent-selector');
    agentSelector.innerHTML = '<option value="all">所有AI模型</option>';
    for (const agentName of Object.keys(globalAgentData)) {
        const option = document.createElement('option');
        option.value = agentName;
        option.textContent = getDisplayName(agentName);
        agentSelector.appendChild(option);
    }

    // 监听选择变化
    agentSelector.addEventListener('change', (e) => {
        const selectedAgent = e.target.value;
        if (selectedAgent === 'all') {
            chart.data.datasets.forEach(dataset => dataset.hidden = false);
        } else {
            chart.data.datasets.forEach(dataset => {
                dataset.hidden = dataset.label !== getDisplayName(selectedAgent);
            });
        }
        chart.update();
    });
}

// 渲染排行榜
function renderRankings() {
    const rankingsList = document.getElementById('rankings-list');

    // 计算排名
    const rankings = Object.entries(globalAgentData).map(([agentName, agent]) => {
        const dailyValues = Object.values(agent.daily_snapshots || {});
        let returnPct = 0;
        let finalValue = agent.initial_capital;

        if (dailyValues.length > 0) {
            const lastValue = dailyValues[dailyValues.length - 1];
            finalValue = lastValue.total_value;
            returnPct = ((finalValue - agent.initial_capital) / agent.initial_capital * 100);
        }

        return {
            name: agentName,
            displayName: getDisplayName(agentName),
            return: returnPct,
            finalValue: finalValue,
            trades: agent.trade_history ? agent.trade_history.length : 0
        };
    }).sort((a, b) => b.return-a.return);

    rankingsList.innerHTML = '';
    rankings.forEach((agent, index) => {
        const rank = index + 1;
        const item = document.createElement('div');
        item.className = `ranking-item rank-${rank <= 3 ? rank : 'other'}`;

        item.innerHTML = `
            <div class="rank-badge rank-${rank <= 3 ? rank : 'other'}">#${rank}</div>
            <div class="ranking-info">
                <div class="ranking-name">${agent.displayName}</div>
                <div class="ranking-model">DeepSeek V3</div>
            </div>
            <div class="ranking-return ${agent.return >= 0 ? 'positive' : 'negative'}">
                ${agent.return >= 0 ? '+' : ''}${agent.return.toFixed(2)}%
            </div>
        `;

        rankingsList.appendChild(item);
    });

    // Add benchmark as reference at the bottom
    if (window.indexBenchmark && window.indexBenchmark.daily_data) {
        const benchmarkData = window.indexBenchmark.daily_data;
        const benchmarkReturn = benchmarkData[benchmarkData.length - 1].return_pct;

        const benchmarkItem = document.createElement('div');
        benchmarkItem.className = 'ranking-item rank-other';
        benchmarkItem.style.borderTop = '2px solid #e2e8f0';
        benchmarkItem.style.marginTop = '8px';
        benchmarkItem.style.opacity = '0.8';

        benchmarkItem.innerHTML = `
            <div class="rank-badge rank-other">📊</div>
            <div class="ranking-info">
                <div class="ranking-name">上证指数 (基准)</div>
                <div class="ranking-model">Shanghai Composite</div>
            </div>
            <div class="ranking-return ${benchmarkReturn >= 0 ? 'positive' : 'negative'}">
                ${benchmarkReturn >= 0 ? '+' : ''}${benchmarkReturn.toFixed(2)}%
            </div>
        `;

        rankingsList.appendChild(benchmarkItem);
    }
}

// 设置交易记录列表
function setupTradesList() {
    const tradeAgentSelector = document.getElementById('trade-agent-selector');
    const tradesList = document.getElementById('trades-list');

    // 填充agent选择器
    tradeAgentSelector.innerHTML = '';
    for (const agentName of Object.keys(globalAgentData)) {
        const option = document.createElement('option');
        option.value = agentName;
        option.textContent = getDisplayName(agentName);
        tradeAgentSelector.appendChild(option);
    }

    // 初始渲染第一个agent的交易记录
    if (Object.keys(globalAgentData).length > 0) {
        const firstAgent = Object.keys(globalAgentData)[0];
        renderTrades(firstAgent);
    }

    // 监听选择变化
    tradeAgentSelector.addEventListener('change', (e) => {
        renderTrades(e.target.value);
    });
}

// 渲染交易记录
function renderTrades(agentName) {
    const tradesList = document.getElementById('trades-list');
    const agent = globalAgentData[agentName];

    if (!agent || !agent.trade_history || agent.trade_history.length === 0) {
        tradesList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-text">暂无交易记录</div>
            </div>
        `;
        return;
    }

    // 倒序显示（最新的在前面）
    const trades = [...agent.trade_history].reverse();

    tradesList.innerHTML = '';
    trades.forEach(trade => {
                const item = document.createElement('div');
                item.className = 'trade-item';

                const totalAmount = trade.price * trade.shares;

                item.innerHTML = `
            <div class="trade-header">
                <div class="trade-action ${trade.action}">
                    ${trade.action === 'buy' ? '📈 买入' : '📉 卖出'}
                </div>
                <div class="trade-date">${formatDateTime(trade.date, trade.timestamp)}</div>
            </div>
            <div class="trade-stock">
                ${trade.name}
                <span class="trade-stock-code">${trade.ts_code}</span>
            </div>
            <div class="trade-details">
                <div class="trade-detail-item">
                    <span class="trade-detail-label">价格:</span>
                    <span class="trade-detail-value">¥${trade.price.toFixed(2)}</span>
                </div>
                <div class="trade-detail-item">
                    <span class="trade-detail-label">数量:</span>
                    <span class="trade-detail-value">${trade.shares}股</span>
                </div>
                <div class="trade-detail-item">
                    <span class="trade-detail-label">金额:</span>
                    <span class="trade-detail-value">¥${totalAmount.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                </div>
            </div>
            ${trade.reason ? `
                <div class="trade-reason">
                    <div class="trade-reason-label">决策原因</div>
                    <div class="trade-reason-text">${trade.reason}</div>
                </div>
            ` : ''}
        `;

        tradesList.appendChild(item);
    });
}

// 工具函数：格式化日期
function formatDate(dateStr) {
    if (!dateStr || dateStr === '-') return '-';
    // dateStr format: YYYYMMDD
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    return `${month}/${day}`;
}

// 工具函数：格式化日期时间
function formatDateTime(dateStr, timeStr) {
    const date = formatDate(dateStr);
    if (!timeStr) return date;

    // timeStr format: YYYY-MM-DD HH:MM:SS
    const time = timeStr.split(' ')[1];
    return `${date} ${time}`;
}

// 显示错误
function showError(message) {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div class="container-fluid">
            <div class="error" style="background-color: #fef2f2; color: #ef4444; padding: 2rem; border-radius: 8px; border-left: 4px solid #ef4444; margin: 2rem 0;">
                <h3>⚠️ ${message}</h3>
                <p>请确保已运行模拟交易并生成数据文件</p>
            </div>
        </div>
    `;
}

// 设置Tab切换
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');

            // 移除所有active状态
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanels.forEach(panel => panel.classList.remove('active'));

            // 添加active状态
            button.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });
}

// 设置持仓情况列表
function setupPositionsList() {
    const positionAgentSelector = document.getElementById('position-agent-selector');
    const positionsList = document.getElementById('positions-list');

    console.log('setupPositionsList called');
    console.log('positionAgentSelector:', positionAgentSelector);
    console.log('positionsList:', positionsList);

    if (!positionAgentSelector || !positionsList) {
        console.error('Position elements not found!');
        return;
    }

    // 填充agent选择器
    positionAgentSelector.innerHTML = '';
    for (const agentName of Object.keys(globalAgentData)) {
        const option = document.createElement('option');
        option.value = agentName;
        option.textContent = getDisplayName(agentName);
        positionAgentSelector.appendChild(option);
    }

    // 初始渲染第一个agent的持仓
    if (Object.keys(globalAgentData).length > 0) {
        const firstAgent = Object.keys(globalAgentData)[0];
        console.log('Rendering positions for:', firstAgent);
        renderPositions(firstAgent);
    }

    // 监听选择变化
    positionAgentSelector.addEventListener('change', (e) => {
        console.log('Agent changed to:', e.target.value);
        renderPositions(e.target.value);
    });
}

// 渲染持仓情况
function renderPositions(agentName) {
    console.log('renderPositions called for:', agentName);
    const positionsList = document.getElementById('positions-list');
    const agent = globalAgentData[agentName];

    console.log('Agent data:', agent);
    console.log('Positions:', agent ? agent.positions : 'no agent');

    if (!agent || !agent.positions || Object.keys(agent.positions).length === 0) {
        console.log('No positions found, showing empty state');
        positionsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📦</div>
                <div class="empty-state-text">暂无持仓</div>
            </div>
        `;
        // 清空饼图
        if (pieChart) {
            pieChart.destroy();
            pieChart = null;
        }
        return;
    }

    console.log('Found positions:', Object.keys(agent.positions).length);

    // 获取最新日期的快照数据来计算当前价格
    const dailySnapshots = agent.daily_snapshots || {};
    const dates = Object.keys(dailySnapshots).sort();
    const lastDate = dates[dates.length - 1];
    const lastSnapshot = dailySnapshots[lastDate];

    console.log('Last snapshot date:', lastDate);
    console.log('Last snapshot:', lastSnapshot);

    positionsList.innerHTML = '';

    // 准备饼图数据
    const pieData = {
        labels: [],
        values: [],
        colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']
    };

    // 如果有最新快照，计算总持仓市值用于推算当前价格
    let totalSnapshotValue = 0;
    if (lastSnapshot && lastSnapshot.positions_value) {
        totalSnapshotValue = lastSnapshot.positions_value;
    }

    // 先计算总成本，用于分配市值
    let totalCost = 0;
    for (const [ts_code, position] of Object.entries(agent.positions)) {
        const avgCost = position.avg_cost || position.avg_price || 0;
        const shares = position.shares || 0;
        totalCost += avgCost * shares;
    }

    for (const [ts_code, position] of Object.entries(agent.positions)) {
        console.log('Processing position:', ts_code, position);

        const item = document.createElement('div');
        item.className = 'position-item';

        // 从数据中读取 avg_cost
        const avgCost = position.avg_cost || position.avg_price || 0;
        const shares = position.shares || 0;
        const cost = avgCost * shares;

        // 计算当前价格和市值
        let currentPrice = avgCost;
        let currentValue = cost;
        let profit = 0;
        let profitRate = 0;

        // 如果有总市值数据，按比例分配来估算当前价格
        if (totalSnapshotValue > 0 && totalCost > 0) {
            // 按成本比例分配当前市值
            const valueRatio = totalSnapshotValue / totalCost;
            currentValue = cost * valueRatio;
            currentPrice = currentValue / shares;
            profit = currentValue - cost;
            profitRate = cost > 0 ? (profit / cost) * 100 : 0;
        }

        // 获取股票名称
        let stockName = getStockName(ts_code);

        // 添加到饼图数据
        pieData.labels.push(stockName);
        pieData.values.push(currentValue);

        item.innerHTML = `
            <div class="position-header">
                <div class="position-stock">
                    ${stockName}
                    <span class="position-stock-code">${ts_code}</span>
                </div>
                <div class="position-profit ${profit >= 0 ? 'positive' : 'negative'}">
                    ${profit >= 0 ? '+' : ''}¥${profit.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                </div>
            </div>
            <div class="position-details">
                <div class="position-detail-item">
                    <span class="position-detail-label">持仓:</span>
                    <span class="position-detail-value">${shares}股</span>
                </div>
                <div class="position-detail-item">
                    <span class="position-detail-label">成本价:</span>
                    <span class="position-detail-value">¥${avgCost.toFixed(2)}</span>
                </div>
                <div class="position-detail-item">
                    <span class="position-detail-label">现价:</span>
                    <span class="position-detail-value">¥${currentPrice.toFixed(2)}</span>
                </div>
                <div class="position-detail-item">
                    <span class="position-detail-label">市值:</span>
                    <span class="position-detail-value">¥${currentValue.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                </div>
                <div class="position-detail-item">
                    <span class="position-detail-label">成本:</span>
                    <span class="position-detail-value">¥${cost.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                </div>
                <div class="position-detail-item">
                    <span class="position-detail-label">盈亏:</span>
                    <span class="position-detail-value ${profit >= 0 ? 'positive' : 'negative'}">
                        ${profit >= 0 ? '+' : ''}¥${profit.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                    </span>
                </div>
            </div>
        `;

        positionsList.appendChild(item);
    }

    console.log('Rendered', pieData.labels.length, 'positions');
    console.log('Calling renderPieChart with data:', pieData);

    // 渲染饼图
    renderPieChart(pieData);
}

// 渲染持仓饼图
function renderPieChart(pieData) {
    const ctx = document.getElementById('positions-pie-chart').getContext('2d');

    // 销毁旧的图表
    if (pieChart) {
        pieChart.destroy();
    }

    // 创建新的饼图
    pieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: pieData.labels,
            datasets: [{
                data: pieData.values,
                backgroundColor: pieData.colors.slice(0, pieData.labels.length),
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    align: 'center',
                    labels: {
                        padding: 12,
                        font: {
                            size: 11
                        },
                        boxWidth: 12,
                        boxHeight: 12,
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                return data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return {
                                        text: `${label} ${percentage}%`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        hidden: false,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ¥${value.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}