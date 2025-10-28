// AI交易竞赛结果可视化脚本

let performanceChart = null;
let competitionData = {};
let agentsData = {};

// 颜色配置
const COLORS = [
    '#2563eb', '#dc2626', '#16a34a', '#ea580c', '#9333ea',
    '#0891b2', '#db2777', '#65a30d', '#ca8a04', '#7c3aed'
];

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadCompetitionData();
    setupEventListeners();
});

// 加载竞赛数据
async function loadCompetitionData() {
    try {
        // 加载竞赛摘要
        const summary = await fetchJSON('data/competition_summary.json');
        competitionData = summary;
        updateSummary(summary);
        renderRankings(summary.rankings);

        // 加载每个Agent的详细数据
        await loadAgentsData(summary.rankings);

        // 渲染图表和详情
        renderPerformanceChart();
        renderAgentsDetails();

    } catch (error) {
        console.error('加载数据失败:', error);
        showError('数据加载失败，请稍后重试');
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

// 加载所有Agent的详细数据
async function loadAgentsData(rankings) {
    const promises = rankings.map(async (ranking) => {
        const filename = `agent_${ranking.name.replace(/ /g, '_').toLowerCase()}.json`;
        try {
            const data = await fetchJSON(`data/${filename}`);
            agentsData[ranking.name] = data;
        } catch (error) {
            console.error(`加载${ranking.name}数据失败:`, error);
        }
    });

    await Promise.all(promises);
}

// 更新摘要信息
function updateSummary(summary) {
    document.getElementById('agents-count').textContent = summary.agents_count || 0;
    document.getElementById('initial-cash').textContent = `¥${formatNumber(summary.initial_cash)}`;
    document.getElementById('trading-period').textContent =
        `${formatDate(summary.start_date)} - ${formatDate(summary.end_date)}`;

    // 最佳收益率
    const bestReturn = summary.rankings && summary.rankings.length > 0
        ? summary.rankings[0].return_pct
        : 0;
    const returnEl = document.getElementById('best-return');
    returnEl.textContent = `${bestReturn >= 0 ? '+' : ''}${bestReturn.toFixed(2)}%`;
    returnEl.className = 'metric-value ' + (bestReturn >= 0 ? 'positive' : 'negative');

    document.getElementById('last-update').textContent = summary.last_update || '-';
}

// 渲染排行榜
function renderRankings(rankings) {
    const container = document.getElementById('rankings-list');
    container.innerHTML = '';

    rankings.forEach((ranking, index) => {
        const rank = index + 1;
        const rankClass = rank <= 3 ? `rank-${rank}` : 'rank-other';
        const returnClass = ranking.return_pct >= 0 ? 'positive' : 'negative';

        const rankBadge = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : rank;

        const item = document.createElement('div');
        item.className = `ranking-item rank-${rank}`;
        item.innerHTML = `
            <div class="rank-badge ${rankClass}">${rankBadge}</div>
            <div class="ranking-info">
                <div class="ranking-name">${ranking.name}</div>
                <div class="ranking-model">${ranking.model}</div>
            </div>
            <div class="ranking-stats">
                <div class="ranking-return ${returnClass}">
                    ${ranking.return_pct >= 0 ? '+' : ''}${ranking.return_pct.toFixed(2)}%
                </div>
                <div class="ranking-details">
                    <div>最终资产: ¥${formatNumber(ranking.final_assets)}</div>
                    <div>交易次数: ${ranking.trades_count}</div>
                </div>
            </div>
        `;

        container.appendChild(item);
    });
}

// 渲染资产走势图
function renderPerformanceChart() {
    const ctx = document.getElementById('performance-chart').getContext('2d');

    const datasets = Object.entries(agentsData).map(([name, data], index) => {
        return {
            label: name,
            data: data.daily_values.map(d => ({
                x: formatDate(d.date),
                y: d.total_assets
            })),
            borderColor: COLORS[index % COLORS.length],
            backgroundColor: COLORS[index % COLORS.length] + '20',
            borderWidth: 3,
            pointRadius: 4,
            pointHoverRadius: 6,
            tension: 0.2
        };
    });

    performanceChart = new Chart(ctx, {
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
                    labels: {
                        font: {
                            size: 14,
                            weight: '500'
                        },
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ¥${formatNumber(context.parsed.y)}`;
                        }
                    },
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: { size: 14 },
                    bodyFont: { size: 13 },
                    padding: 12
                }
            },
            scales: {
                x: {
                    type: 'category',
                    ticks: {
                        maxTicksLimit: 10,
                        font: { size: 12 }
                    }
                },
                y: {
                    type: 'linear',
                    ticks: {
                        callback: function(value) {
                            return '¥' + formatNumber(value);
                        },
                        font: { size: 12 }
                    }
                }
            }
        }
    });
}

// 渲染Agent详情卡片
function renderAgentsDetails() {
    const container = document.getElementById('agents-details');
    container.innerHTML = '';

    Object.entries(agentsData).forEach(([name, data], index) => {
        const summary = data.summary;
        const returnClass = summary.total_return_pct >= 0 ? 'positive' : 'negative';

        const card = document.createElement('div');
        card.className = 'agent-card';
        card.style.borderTopColor = COLORS[index % COLORS.length];
        card.innerHTML = `
            <div class="agent-header">
                <div class="agent-name">${data.agent_name}</div>
                <div class="agent-model">${data.model_name}</div>
            </div>
            <div class="agent-stats">
                <div class="agent-stat">
                    <div class="agent-stat-label">收益率</div>
                    <div class="agent-stat-value ${returnClass} highlight">
                        ${summary.total_return_pct >= 0 ? '+' : ''}${summary.total_return_pct.toFixed(2)}%
                    </div>
                </div>
                <div class="agent-stat">
                    <div class="agent-stat-label">最终资产</div>
                    <div class="agent-stat-value">
                        ¥${formatNumber(summary.total_assets)}
                    </div>
                </div>
                <div class="agent-stat">
                    <div class="agent-stat-label">盈亏金额</div>
                    <div class="agent-stat-value ${returnClass}">
                        ${summary.total_profit_loss >= 0 ? '+' : ''}¥${formatNumber(Math.abs(summary.total_profit_loss))}
                    </div>
                </div>
                <div class="agent-stat">
                    <div class="agent-stat-label">交易次数</div>
                    <div class="agent-stat-value">${summary.trades_count}</div>
                </div>
                <div class="agent-stat">
                    <div class="agent-stat-label">当前持仓</div>
                    <div class="agent-stat-value">${summary.positions_count}只</div>
                </div>
                <div class="agent-stat">
                    <div class="agent-stat-label">剩余现金</div>
                    <div class="agent-stat-value">
                        ¥${formatNumber(summary.cash)}
                    </div>
                </div>
            </div>
        `;

        container.appendChild(card);
    });
}

// 设置事件监听
function setupEventListeners() {
    // 图表比例切换
    document.getElementById('linear-scale')?.addEventListener('change', (e) => {
        if (performanceChart) {
            performanceChart.options.scales.y.type = e.target.checked ? 'linear' : 'logarithmic';
            performanceChart.update();
        }
    });
}

// 导出数据
function exportData() {
    const exportData = {
        competition: competitionData,
        agents: agentsData
    };

    const json = JSON.stringify(exportData, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `competition_results_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '';
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    return `${year}-${month}-${day}`;
}

// 格式化数字
function formatNumber(num) {
    if (typeof num !== 'number') return num;
    return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// 显示错误
function showError(message) {
    const sections = ['rankings-list', 'agents-details'];
    sections.forEach(id => {
        const container = document.getElementById(id);
        if (container) {
            container.innerHTML = `<div class="error">${message}</div>`;
        }
    });
}
