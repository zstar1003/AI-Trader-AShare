// AI-Trader Competition Dashboard

let globalAgentData = {};
let chart = null;

// 名称映射：将内部名称转换为显示名称
const AGENT_NAME_MAP = {
    'DeepSeek_Trader': 'DeepSeek',
    'GPT4_Trader': 'GPT-4',
    'Claude_Trader': 'Claude',
    // 可以继续添加更多映射
};

// 获取显示名称
function getDisplayName(agentName) {
    return AGENT_NAME_MAP[agentName] || agentName;
}

// 初始化
document.addEventListener('DOMContentLoaded', async() => {
    await loadAgentData();
    renderDashboard();
});

// 加载Agent数据
async function loadAgentData() {
    try {
        // 尝试从多个可能的路径加载数据
        const agentFiles = ['DeepSeek_Trader']; // 可以扩展更多agent

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
    const currentDate = firstAgent.simulation_current_date || '-';
    const tradingPeriod = formatTradingPeriod(startDate, currentDate);

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

    // 计算天数
    const days = Object.values(globalAgentData)[0].daily_snapshots ?
        Object.keys(Object.values(globalAgentData)[0].daily_snapshots).length : 0;

    return `${days}天 (${start} - ${end})`;
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