# AI-Trader-AShare

**AI模型交易大赛** - 让不同的AI大模型通过调用工具在A股市场上PK!

## 项目简介

不同的AI大模型（DeepSeek, GLM-4, Kimi, Ring等）作为交易Agent，通过调用真实的交易工具（Tools）在模拟的A股市场中进行交易对比。

每个AI Agent获得**100万初始资金**，在精选的A股股票池中进行为期7个交易日的模拟交易：

- 通过调用 `get_portfolio_status` 查看持仓和资金状况
- 通过调用 `get_stock_info` 获取股票的实时价格和涨跌幅
- 通过调用 `buy_stock` / `sell_stock` 执行交易
- 所有交易数据来自真实历史行情，包含完整的交易费用计算

**📊 在线演示**: https://xdxsb.top/AI-Trader-AShare

## 核心特性

- 🤖**Agent系统** - 基于LangChain Agent框架，AI通过调用Tools完成交易
- 🛠️ **简洁的工具集** - 提供查询持仓、获取股票信息、买入卖出等核心交易工具
- 💰 **真实模拟** - 100万初始资金，真实A股历史数据，完整的交易费用计算
- 📊 **精美的可视化看板** - 实时资产走势图、AI排行榜、交易记录、持仓分布饼图

## 当前参赛AI模型

| AI模型   | 提供商     | 特点                       |
| -------- | ---------- | -------------------------- |
| DeepSeek | DeepSeek   | 国产开源大模型，推理能力强 |
| GLM-4    | 智谱AI     | 中文理解优秀，工具调用准确 |
| Kimi     | Moonshot   | 长文本处理能力强           |
| Ring     | 多模型混合 | 集成多个模型的优势         |

## 项目架构

```
AI-Trader-AShare/
├── core/                      # 核心模块
│   ├── engine.py             # 基础交易引擎（持仓管理、费用计算）
│   ├── time_aware_engine.py  # 时间感知交易引擎（防止未来数据泄露）
│   ├── market_data.py        # 市场数据提供者（从JSON加载历史数据）
│   └── agent_state.py        # Agent状态持久化管理
│
├── tools/                     # 交易工具模块
│   └── trading_tools.py      # AI Agent调用的交易工具集
│
├── agents/                    # AI Agent模块
│   ├── base_agent.py         # Agent基类
│   └── llm_agents.py         # 各种LLM Agent实现（DeepSeek, GLM, Kimi, Ring）
│
├── scripts/                   # 辅助脚本
│   ├── fetch_market_data.py  # 获取历史行情数据
│   ├── price_data_manager.py # 价格数据管理
│   ├── fetch_index_benchmark.py # 获取上证指数基准数据
│   └── copy_data_to_docs.py  # 复制数据到展示目录
│
├── data/                      # 数据目录
│   ├── agent_data/           # Agent状态文件
│   ├── daily_prices/         # 每日价格数据（JSON）
│   └── index_benchmark.json  # 上证指数基准数据
│
├── docs/                      # GitHub Pages前端
│   ├── index.html            # 竞赛看板页面
│   ├── css/style.css         # 样式文件
│   ├── js/competition.js     # 看板逻辑
│   └── data/                 # 前端数据（Agent状态 + 指数基准）
│
├── run_simulation.py          # 模拟交易主程序
└── README.md
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/yourusername/AI-Trader-AShare.git
cd AI-Trader-AShare

# 安装依赖
uv sync

# 配置API Keys（创建.env文件）
cp .env.example .env
# 编辑.env填入你的API Keys:
```

### 2. 获取历史数据

```bash
# 初始化价格数据
python scripts/price_data_manager.py init

# 获取上证指数基准数据
python scripts/fetch_index_benchmark.py
```

### 3. 运行模拟交易

```bash
# 运行模拟交易（默认7个交易日）
python run_simulation.py --all

# Agent状态会自动保存到 data/agent_data/ 目录
# 包含持仓、交易记录、每日快照等信息
```

### 4. 查看竞赛结果

```bash
# 复制数据到前端目录
python scripts/copy_data_to_docs.py

# 启动本地服务器查看
cd docs
python -m http.server 8000

# 访问 http://localhost:8000
```

## 添加新的AI模型

### 1. 在 `agents/llm_agents.py` 添加新Agent

```python
class YourModelAgent(LLMTradingAgent):
    def __init__(self, name: str = "YourModel Trader"):
        api_key = os.getenv("YOUR_API_KEY")
        super().__init__(
            name=name,
            model_name="your-model-name",
            api_key=api_key,
            base_url="https://your-api-url",
            temperature=0.7
        )
```

### 2. 在 `run_simulation.py` 注册Agent

```python
from agents.llm_agents import YourModelAgent

# 初始化Agents
agents = [
    DeepSeekAgent(),
    GLMAgent(),
    KimiAgent(),
    RingAgent(),
    YourModelAgent()  # 添加你的Agent
]

# 运行模拟
for agent in agents:
    run_agent_simulation(agent, engine, trading_days)
```

### 3. 配置API Key

在 `.env` 文件中添加：

```
YOUR_API_KEY=sk-xxxxxxxx
```

## 可用交易工具

| 工具名称                 | 功能             | 参数                                                                  | 返回值                                                        |
| ------------------------ | ---------------- | --------------------------------------------------------------------- | ------------------------------------------------------------- |
| `get_portfolio_status` | 获取投资组合状态 | `context: dict`                                                     | 现金、持仓市值、总资产、持仓列表                              |
| `get_stock_info`       | 获取股票实时信息 | `ts_code: str<br>``context: dict`                                   | 开盘价、最高价、最低价、收盘价 `<br>`涨跌幅、成交量、成交额 |
| `buy_stock`            | 买入股票         | `ts_code: str<br>``shares: int<br>``reason: str<br>``context: dict` | 成交价格、数量、总金额 `<br>`手续费、剩余资金               |
| `sell_stock`           | 卖出股票         | `ts_code: str<br>``shares: int<br>``reason: str<br>``context: dict` | 成交价格、数量、总金额 `<br>`盈亏、剩余资金                 |

**注意事项**:

- 所有工具都需要 `context` 参数传递引擎实例
- 买卖股票必须是100的整数倍（A股最小交易单位）
- 交易需要支付手续费（买入万0.5，卖出万0.5+印花税千1）
- 不允许做空和融资融券

## 技术栈

- **Agent框架**: LangChain + ReAct模式
- **LLM接口**: OpenAI SDK (兼容多个API提供商)
- **数据源**: Tushare Pro API (获取历史数据) + 本地JSON存储
- **前端**: HTML5 + CSS3 + Vanilla JavaScript + Chart.js
- **可视化**: Chart.js (折线图 + 环形饼图)
- **部署**: GitHub Pages

### Q: 交易费用怎么计算？

严格按照A股规则：

- 买入：交易金额 × 0.05% (佣金)
- 卖出：交易金额 × 0.05% (佣金) + 交易金额 × 0.1% (印花税)

## 免责声明

本项目仅用于教育和研究目的。不构成任何投资建议。股市有风险，投资需谨慎。
