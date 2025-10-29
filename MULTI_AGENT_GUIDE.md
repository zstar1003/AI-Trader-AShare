# 多Agent运行指南

`run_simulation.py` 现在支持灵活运行单个或多个AI Agent！

## 🎯 快速开始

### 1. 运行单个Agent

```bash
# 运行 DeepSeek（默认）
python run_simulation.py

# 或明确指定
python run_simulation.py --agent deepseek
```

### 2. 运行多个Agent

```bash
# 运行多个指定的Agent
python run_simulation.py --agents deepseek,gpt4

# 运行所有已启用的Agent
python run_simulation.py --all
```

### 3. 查看可用Agent

```bash
python run_simulation.py --list
```

输出示例：
```
可用的Agent:

  deepseek   - DeepSeek        ✓ 已启用
  gpt4       - GPT-4           ✗ 未启用
             提示: 需要在.env中配置API密钥
  claude     - Claude          ✗ 未启用
             提示: 需要在.env中配置API密钥
  qwen3      - Qwen3           ✗ 未启用
             提示: 需要在.env中配置API密钥
```

## 📋 Agent配置

在 `run_simulation.py` 中的 `AVAILABLE_AGENTS` 字典：

```python
AVAILABLE_AGENTS = {
    'deepseek': {
        'class': DeepSeekAgent,
        'name': 'DeepSeek_Trader',      # 数据文件名
        'display_name': 'DeepSeek',      # 显示名称
        'enabled': True                  # 是否默认启用
    },
    'gpt4': {
        'class': GPT4Agent,
        'name': 'GPT4_Trader',
        'display_name': 'GPT-4',
        'enabled': False                 # 需要API key
    },
    # ... 更多Agent
}
```

## 🔑 配置API密钥

在 `.env` 文件中添加：

```bash
# DeepSeek (通过SiliconFlow)
SILICONFLOW_API_KEY=your_siliconflow_key

# GPT-4 / Claude (通过OpenRouter)
OPENROUTER_API_KEY=your_openrouter_key

# Tushare (必须)
TUSHARE_API_KEY=your_tushare_key
```

## 📊 启用/禁用Agent

### 方法1: 修改配置文件

编辑 `run_simulation.py`，将 `enabled` 设置为 `True` 或 `False`：

```python
'gpt4': {
    'class': GPT4Agent,
    'name': 'GPT4_Trader',
    'display_name': 'GPT-4',
    'enabled': True  # 改为 True 启用
}
```

### 方法2: 使用命令行参数

不管 `enabled` 状态如何，都可以通过命令行运行：

```bash
# 强制运行gpt4，即使未启用
python run_simulation.py --agent gpt4

# 运行多个，包括未启用的
python run_simulation.py --agents deepseek,gpt4,claude
```

## 🎨 添加新的Agent

### 1. 创建Agent类

在 `agents/llm_agents.py` 中添加：

```python
class YourModelAgent(LLMTradingAgent):
    """你的模型Agent"""

    def __init__(self, name: str = "Your Model Trader"):
        api_key = os.getenv("YOUR_API_KEY")
        if not api_key:
            raise ValueError("YOUR_API_KEY not found in environment")

        super().__init__(
            name=name,
            model_name="your-model-name",
            api_key=api_key,
            base_url="https://your-api-url"
        )
```

### 2. 注册到配置

在 `run_simulation.py` 中添加：

```python
from agents.llm_agents import YourModelAgent  # 导入

AVAILABLE_AGENTS = {
    # ... 现有Agent
    'yourmodel': {
        'class': YourModelAgent,
        'name': 'YourModel_Trader',
        'display_name': 'Your Model',
        'enabled': False
    }
}
```

### 3. 更新名称映射

在 `docs/js/competition.js` 中添加：

```javascript
const AGENT_NAME_MAP = {
    'DeepSeek_Trader': 'DeepSeek',
    'GPT4_Trader': 'GPT-4',
    'YourModel_Trader': 'Your Model',  // 新增
    // ...
};
```

### 4. 运行测试

```bash
python run_simulation.py --agent yourmodel
```

## 📁 数据文件

每个Agent运行后会生成对应的状态文件：

```
data/agent_data/
├── DeepSeek_Trader_state.json
├── GPT4_Trader_state.json
├── Claude_Trader_state.json
└── Qwen3_Trader_state.json
```

## 🔄 更新Dashboard

运行完成后，复制数据到docs目录：

```bash
python scripts/copy_data_to_docs.py
```

Dashboard会自动加载所有可用的Agent数据并显示。

## ⚙️ 高级用法

### 并发运行（未来功能）

目前Agent是串行运行的，每个Agent之间有5秒延迟。未来可以添加并发支持：

```python
# 待实现
python run_simulation.py --all --parallel
```

### 自定义交易天数

修改 `get_recent_trading_dates` 函数：

```python
def get_recent_trading_dates(n_days: int = 10):
    """获取最近N个交易日"""
    dates = MarketDataProvider.get_recent_trading_dates(pro, n_days=n_days + 5)
    return dates[-n_days:]

# 调用时
trading_dates = get_recent_trading_dates(20)  # 20天
```

### 自定义初始资金

修改 `simulate_trading` 函数：

```python
engine = TimeAwareTradingEngine(
    agent_name=agent_name,
    initial_capital=2000000.0,  # 改为200万
    market_data=market_data
)
```

## 📝 使用示例

### 示例1: 测试新Agent

```bash
# 1. 添加新Agent配置
# 2. 运行单个测试
python run_simulation.py --agent yourmodel

# 3. 检查输出和数据文件
ls data/agent_data/YourModel_Trader_state.json
```

### 示例2: 比赛模式

```bash
# 启用所有Agent
# 在 run_simulation.py 中设置 enabled: True

# 运行所有Agent
python run_simulation.py --all

# 复制数据
python scripts/copy_data_to_docs.py

# 启动Dashboard
cd docs && python -m http.server 8000
```

### 示例3: A/B测试

```bash
# 只运行DeepSeek和GPT-4对比
python run_simulation.py --agents deepseek,gpt4
```

## 🐛 故障排查

### 问题1: Agent创建失败

```
错误: 无法创建Agent - OPENROUTER_API_KEY not found in environment
```

**解决**: 在 `.env` 中添加对应的API密钥

### 问题2: 数据文件未生成

**解决**: 检查 `data/agent_data/` 目录是否存在，查看控制台错误信息

### 问题3: Dashboard不显示某个Agent

**解决**:
1. 确认数据文件存在: `ls docs/data/AgentName_state.json`
2. 检查浏览器控制台是否有加载错误
3. 运行 `python scripts/copy_data_to_docs.py` 复制最新数据

## 🎉 完整工作流

```bash
# 1. 列出可用Agent
python run_simulation.py --list

# 2. 运行模拟（选择方式）
python run_simulation.py                    # 默认DeepSeek
python run_simulation.py --agent gpt4       # 单个Agent
python run_simulation.py --agents deepseek,gpt4  # 多个Agent
python run_simulation.py --all              # 所有启用的Agent

# 3. 复制数据到docs
python scripts/copy_data_to_docs.py

# 4. 启动Dashboard
cd docs
python -m http.server 8000

# 5. 打开浏览器
# http://localhost:8000
```
