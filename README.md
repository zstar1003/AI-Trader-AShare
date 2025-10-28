# AI-Trader A股竞赛

**AI模型交易大赛** - 让不同的AI大模型通过调用工具在A股市场上PK！

## 项目简介

这是一个基于LangChain Agent框架的AI交易竞赛平台。不同的AI大模型（如DeepSeek, GPT-4, Claude等）作为交易Agent，通过调用真实的交易工具（Tools）在模拟的A股市场中进行实盘交易对比。

每个AI Agent获得100万初始资金，在最近10个交易日的真实市场数据中：
- 通过调用 `get_portfolio_status` 查看持仓和资金状况
- 通过调用 `get_available_stocks` 获取所有5000+支股票代码
- 通过调用 `search_stocks` 按条件筛选潜在投资标的
- 通过调用 `get_stock_price` 查询具体股票的详细信息
- 通过调用 `buy_stock` / `sell_stock` 执行交易

看哪个AI模型能获得最高收益！

## 核心特性

- 🤖 **真正的Agent系统** - 基于LangChain Agent框架，AI通过调用Tools完成交易
- 🛠️ **完整的工具集** - 提供查询持仓、获取股票列表、买入卖出等交易工具
- 💰 **真实模拟** - 100万初始资金，真实A股历史数据，完整的交易费用计算
- 📊 **可视化对比** - 实时资产走势图，排行榜，详细的交易记录
- 🔄 **自动化运行** - GitHub Actions每日自动运行竞赛并更新结果

## 项目架构

```
AI-Trader-AShare/
├── core/                      # 核心模块
│   ├── engine.py             # 交易引擎（持仓管理、费用计算）
│   └── market_data.py        # 市场数据提供者（Tushare接口）
│
├── tools/                     # 交易工具模块
│   └── trading_tools.py      # AI Agent调用的交易工具集
│
├── agents/                    # AI Agent模块
│   ├── base_agent.py         # Agent基类
│   └── llm_agents.py         # 各种LLM Agent实现
│
├── run_competition.py         # 竞赛主程序
├── test_new_agent.py          # Agent测试脚本
│
├── docs/                      # GitHub Pages部署
│   ├── index.html            # 竞赛结果页面
│   ├── css/style.css
│   ├── js/competition.js
│   └── data/                 # 竞赛结果数据
│
└── .github/workflows/
    ├── competition.yml       # 竞赛自动运行
    └── deploy.yml           # 页面部署
```

## 快速开始

### 1. 本地运行竞赛

```bash
# 克隆项目
git clone https://github.com/yourusername/AI-Trader-AShare.git
cd AI-Trader-AShare

# 安装依赖
uv pip install tushare pandas python-dotenv openai langchain langchain-openai

# 配置API Keys（创建.env文件）
cp .env.example .env
# 编辑.env填入你的API Keys

# 测试单个Agent
python test_new_agent.py

# 运行完整竞赛
python run_competition.py
```

### 2. 查看结果

```bash
cd docs
python -m http.server 8000
# 访问 http://localhost:8000
```

## Agent架构设计

### 1. 核心组件

**交易引擎 (core/engine.py)**
- `TradingEngine`: 处理买卖、计算费用、管理持仓
- `Portfolio`: 投资组合管理
- `Position`: 个股持仓信息

**交易工具 (tools/trading_tools.py)**
```python
@tool
def get_portfolio_status() -> str:
    """获取当前投资组合状态"""
    pass

@tool
def buy_stock(ts_code: str, shares: int, reason: str) -> str:
    """买入股票"""
    pass

@tool
def sell_stock(ts_code: str, shares: int, reason: str) -> str:
    """卖出股票"""
    pass
```

**AI Agent (agents/)**
```python
class DeepSeekAgent(LLMTradingAgent):
    def create_agent(self, tools):
        # 使用LangChain的create_react_agent
        agent = create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        return AgentExecutor(agent=agent, tools=tools)
```

### 2. 工作流程

```
1. 竞赛开始
   ↓
2. 获取交易日和股票池数据
   ↓
3. 对每个交易日：
   ├─ 为Agent提供交易工具
   ├─ Agent分析市场（调用get_portfolio_status等）
   ├─ Agent做决策（调用buy_stock/sell_stock）
   └─ 更新持仓和资产
   ↓
4. 生成竞赛报告
```

### 3. Agent决策过程（ReAct模式）

```
Question: 当前市场情况和任务

Thought: 我需要先查看投资组合状态
Action: get_portfolio_status
Action Input:
Observation: 现金 ¥1,000,000.00...

Thought: 我想筛选一些涨幅较大的股票
Action: search_stocks
Action Input: {"min_change": 3.0, "max_change": 9.9, "limit": 20}
Observation: 找到 20 只符合条件的股票:
1. 贵州茅台 (600519.SH)
   价格: 1688.50 RMB, 涨跌: +5.23%, 成交量: 12,345,678
...

Thought: 我想了解贵州茅台的详细信息
Action: get_stock_price
Action Input: {"ts_code": "600519.SH"}
Observation: 股票价格 (2025-10-28):
代码: 600519.SH
开盘: 1680.00 RMB
最高: 1690.00 RMB...

Thought: 我决定买入贵州茅台
Action: buy_stock
Action Input: {"ts_code": "600519.SH", "shares": 500, "reason": "涨势良好，成交量放大"}
Observation: 买入成功! 股票: 600519.SH...

Thought: 交易完成
Final Answer: 已买入贵州茅台500股...
```

## 添加新的AI模型

### 1. 在 `agents/llm_agents.py` 添加新Agent

```python
class YourModelAgent(LLMTradingAgent):
    def __init__(self, name: str = "Your Model Trader"):
        api_key = os.getenv("YOUR_API_KEY")
        super().__init__(
            name=name,
            model_name="your-model-name",
            api_key=api_key,
            base_url="https://your-api-url"
        )
```

### 2. 在 `run_competition.py` 注册Agent

```python
competition.register_agent(YourModelAgent())
```

## 可用交易工具

| 工具名称 | 功能 | 参数 | 说明 |
|---------|------|------|------|
| `get_portfolio_status` | 获取投资组合状态 | 无 | 查看持仓、资金、收益等信息 |
| `get_available_stocks` | 获取所有可交易股票代码 | 无 | 返回全部5000+支股票代码列表 |
| `search_stocks` | 按条件筛选股票 | min_change, max_change, min_price, max_price, min_volume, limit | 根据涨跌幅、价格区间、成交量等筛选 |
| `get_stock_price` | 获取股票详细价格信息 | ts_code: str | 获取单只股票的完整价格数据 |
| `buy_stock` | 买入股票 | ts_code, shares, reason | 执行买入操作 |
| `sell_stock` | 卖出股票 | ts_code, shares, reason | 执行卖出操作 |

## 技术栈

- **Agent框架**: LangChain + ReAct模式
- **LLM接口**: OpenAI SDK (兼容多个API)
- **数据源**: Tushare Pro API
- **前端**: HTML5 + Chart.js
- **部署**: GitHub Pages + GitHub Actions

## 与原设计的区别

### ❌ 旧设计（解析JSON）

```python
# AI输出JSON字符串
response = llm.chat("分析市场...")
decision = json.loads(response)  # 解析JSON

# 手动执行
if decision['action'] == 'buy':
    engine.buy(...)
```

问题：
- AI可能输出不规范的JSON
- 需要手动解析和执行
- 工具调用链路不清晰

### ✅ 新设计（Tool Calling）

```python
# AI直接调用工具
agent.create_agent(tools=[get_portfolio, buy_stock, ...])
result = agent.make_decision(context)

# LangChain自动处理tool calling
# Agent自己决定调用哪些工具、何时调用
```

优势：
- 标准化的Tool接口
- 自动处理工具调用和结果
- 支持多轮对话和思考链
- 更符合Agent范式

## 示例：Agent执行日志

```
[DeepSeek Trader] 开始决策...

> Entering new AgentExecutor chain...

Thought: 我需要先了解当前的投资组合状态
Action: get_portfolio_status
Action Input:

Observation: 投资组合状态:
- 现金: ¥1,000,000.00
- 持仓市值: ¥0.00
...

Thought: 现在使用search_stocks筛选涨幅较大的股票
Action: search_stocks
Action Input: {"min_change": 3.0, "max_change": 9.9, "limit": 10}

Observation: 找到 10 只符合条件的股票:
1. 贵州茅台 (600519.SH)
   价格: 1688.50 RMB, 涨跌: +5.23%, 成交量: 12,345,678
2. 宁德时代 (300750.SZ)
   价格: 215.88 RMB, 涨跌: +4.12%, 成交量: 98,765,432
...

Thought: 我想了解宁德时代的详细信息
Action: get_stock_price
Action Input: {"ts_code": "300750.SZ"}

Observation: 股票价格 (2025-10-28):
代码: 300750.SZ
日期: 20251028
开盘: 210.50 RMB
最高: 218.00 RMB
最低: 209.80 RMB
收盘: 215.88 RMB
成交量: 98,765,432

Thought: 我决定买入宁德时代
Action: buy_stock
Action Input: {"ts_code": "300750.SZ", "shares": 4000, "reason": "新能源龙头，涨势良好，成交量放大"}

Observation: 买入成功!
股票: 300750.SZ
价格: 215.88 RMB
...

> Finished chain.

[DeepSeek Trader] 决策完成
```

## 常见问题

### Q: 为什么要用LangChain Agent？
A: Agent框架提供标准化的Tool接口，AI可以自主决定何时调用哪些工具，更符合真实的交易决策过程。

### Q: Agent会无限循环调用工具吗？
A: 不会，AgentExecutor有max_iterations限制（默认10次）。

### Q: 如何调试Agent的决策过程？
A: 设置`verbose=True`可以看到完整的思考链和工具调用过程。

### Q: 可以添加更多工具吗？
A: 可以！在`tools/trading_tools.py`中添加新的`@tool`装饰的函数即可。

## GitHub 部署

1. Fork本项目
2. 配置Secrets: `TUSHARE_API_KEY`, `SILICONFLOW_API_KEY`
3. 启用GitHub Pages
4. Actions会每天自动运行竞赛

## 许可证

MIT License

## 致谢

- [LangChain](https://python.langchain.com/) - Agent框架
- [Tushare](https://tushare.pro/) - 金融数据API
- [SiliconFlow](https://siliconflow.cn) - DeepSeek API
- [Chart.js](https://www.chartjs.org/) - 图表库

## 免责声明

本项目仅用于教育和研究。不构成投资建议。
