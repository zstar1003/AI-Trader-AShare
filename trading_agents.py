"""
AI交易Agent基类和具体实现
支持不同的LLM模型作为交易决策引擎
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


@dataclass
class MarketContext:
    """市场上下文信息"""
    date: str
    available_stocks: List[Dict]  # 可交易股票列表
    current_portfolio: Dict  # 当前投资组合
    market_data: Dict  # 市场数据


@dataclass
class TradingDecision:
    """交易决策"""
    action: str  # 'buy', 'sell', 'hold'
    ts_code: Optional[str] = None
    shares: Optional[int] = None
    reason: str = ""


class BaseTradingAgent(ABC):
    """交易Agent基类"""

    def __init__(self, name: str, model_name: str, initial_cash: float = 1000000):
        self.name = name
        self.model_name = model_name
        self.initial_cash = initial_cash
        self.decision_history = []

    @abstractmethod
    def make_decision(self, context: MarketContext) -> TradingDecision:
        """做出交易决策"""
        pass

    def format_portfolio_info(self, portfolio: Dict) -> str:
        """格式化投资组合信息"""
        info = f"总资产: ¥{portfolio.get('total_assets', 0):,.2f}\n"
        info += f"现金: ¥{portfolio.get('cash', 0):,.2f}\n"
        info += f"持仓市值: ¥{portfolio.get('market_value', 0):,.2f}\n"
        info += f"收益率: {portfolio.get('total_return_pct', 0):.2f}%\n"

        positions = portfolio.get('positions', [])
        if positions:
            info += f"\n当前持仓 ({len(positions)}只):\n"
            for pos in positions:
                info += f"  {pos['name']} ({pos['ts_code']}): {pos['shares']}股, "
                info += f"成本¥{pos['avg_price']:.2f}, 现价¥{pos['current_price']:.2f}, "
                info += f"盈亏{pos['profit_loss_pct']:+.2f}%\n"
        else:
            info += "\n当前无持仓\n"

        return info

    def format_stock_list(self, stocks: List[Dict], limit: int = 10) -> str:
        """格式化股票列表"""
        info = f"可交易股票 (前{min(limit, len(stocks))}只):\n"
        for i, stock in enumerate(stocks[:limit], 1):
            info += f"{i}. {stock['name']} ({stock['ts_code']}) - {stock['industry']}\n"
            if 'close' in stock:
                info += f"   当前价格: ¥{stock['close']:.2f}, "
                info += f"涨跌幅: {stock.get('change', 0):+.2f}%\n"
        return info


class LLMTradingAgent(BaseTradingAgent):
    """基于LLM的交易Agent"""

    def __init__(self, name: str, model_name: str, api_key: str,
                 base_url: str, initial_cash: float = 1000000):
        super().__init__(name, model_name, initial_cash)
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.system_prompt = self._create_system_prompt()

    def _create_system_prompt(self) -> str:
        """创建系统提示词"""
        return """你是一位专业的A股量化交易员，负责管理一个投资组合。

你的任务：
1. 分析当前市场情况和投资组合状态
2. 基于技术分析和风险管理做出交易决策
3. 每次只能做出一个决策：买入某只股票、卖出某只股票、或持有不动

交易规则：
- 初始资金100万人民币
- 每次买入时，建议单只股票投入资金不超过总资产的30%
- 考虑分散投资，建议持有3-5只股票
- 注意控制风险，设置止损点
- 考虑交易成本：佣金0.03%，最低5元；卖出时额外0.1%印花税

决策格式要求：
你必须返回一个JSON对象，包含以下字段：
{
    "action": "buy/sell/hold",
    "ts_code": "股票代码(仅买入/卖出时需要)",
    "shares": 股数(仅买入/卖出时需要),
    "reason": "决策理由"
}

注意：
- action只能是 "buy", "sell", "hold" 之一
- 买入时shares建议是100的倍数（A股最小交易单位是100股）
- 卖出时shares不能超过持仓数量
- 必须返回有效的JSON格式
"""

    def make_decision(self, context: MarketContext) -> TradingDecision:
        """使用LLM做出交易决策"""
        # 构建用户消息
        user_message = self._build_user_message(context)

        try:
            # 调用LLM
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            # 解析响应
            content = response.choices[0].message.content.strip()

            # 尝试提取JSON
            decision_json = self._extract_json(content)

            if decision_json:
                decision = TradingDecision(
                    action=decision_json.get('action', 'hold'),
                    ts_code=decision_json.get('ts_code'),
                    shares=decision_json.get('shares'),
                    reason=decision_json.get('reason', '')
                )
            else:
                # 如果解析失败，默认持有
                decision = TradingDecision(
                    action='hold',
                    reason=f"LLM响应解析失败: {content[:100]}"
                )

            # 记录决策
            self.decision_history.append({
                'date': context.date,
                'decision': decision,
                'llm_response': content
            })

            return decision

        except Exception as e:
            print(f"LLM调用失败: {e}")
            return TradingDecision(
                action='hold',
                reason=f"LLM调用失败: {str(e)}"
            )

    def _build_user_message(self, context: MarketContext) -> str:
        """构建用户消息"""
        message = f"交易日期: {context.date}\n\n"
        message += "=" * 60 + "\n"
        message += "当前投资组合:\n"
        message += "=" * 60 + "\n"
        message += self.format_portfolio_info(context.current_portfolio)
        message += "\n" + "=" * 60 + "\n"
        message += "市场信息:\n"
        message += "=" * 60 + "\n"
        message += self.format_stock_list(context.available_stocks, limit=20)
        message += "\n请基于以上信息做出交易决策，返回JSON格式的决策。"

        return message

    def _extract_json(self, text: str) -> Optional[Dict]:
        """从文本中提取JSON"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except:
            pass

        # 尝试提取代码块中的JSON
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end > start:
                try:
                    return json.loads(text[start:end].strip())
                except:
                    pass

        # 尝试查找{ }包围的内容
        if '{' in text and '}' in text:
            start = text.find('{')
            end = text.rfind('}') + 1
            try:
                return json.loads(text[start:end])
            except:
                pass

        return None


class DeepSeekAgent(LLMTradingAgent):
    """DeepSeek模型交易Agent"""

    def __init__(self, name: str = "DeepSeek Trader", initial_cash: float = 1000000):
        api_key = os.getenv("SILICONFLOW_API_KEY")
        super().__init__(
            name=name,
            model_name="deepseek-ai/DeepSeek-V3.2-Exp",
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1",
            initial_cash=initial_cash
        )


class GPT4Agent(LLMTradingAgent):
    """GPT-4模型交易Agent"""

    def __init__(self, name: str = "GPT-4 Trader", initial_cash: float = 1000000):
        api_key = os.getenv("OPENROUTER_API_KEY")
        super().__init__(
            name=name,
            model_name="openai/gpt-4o",
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            initial_cash=initial_cash
        )


class ClaudeAgent(LLMTradingAgent):
    """Claude模型交易Agent"""

    def __init__(self, name: str = "Claude Trader", initial_cash: float = 1000000):
        api_key = os.getenv("OPENROUTER_API_KEY")
        super().__init__(
            name=name,
            model_name="anthropic/claude-3.5-sonnet",
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            initial_cash=initial_cash
        )


class RandomAgent(BaseTradingAgent):
    """随机交易Agent（作为基准）"""

    def __init__(self, name: str = "Random Trader", initial_cash: float = 1000000):
        super().__init__(name, "random", initial_cash)

    def make_decision(self, context: MarketContext) -> TradingDecision:
        """随机决策"""
        import random

        # 70%概率持有，15%买入，15%卖出
        rand = random.random()

        if rand < 0.15 and context.available_stocks:
            # 买入
            stock = random.choice(context.available_stocks)
            cash = context.current_portfolio.get('cash', 0)
            price = stock.get('close', 100)

            # 随机投入10%-20%的现金
            invest_pct = random.uniform(0.1, 0.2)
            invest_amount = cash * invest_pct
            shares = int(invest_amount / price / 100) * 100  # 凑整到100的倍数

            if shares >= 100:
                return TradingDecision(
                    action='buy',
                    ts_code=stock['ts_code'],
                    shares=shares,
                    reason="随机买入决策"
                )

        elif rand < 0.30:
            # 卖出
            positions = context.current_portfolio.get('positions', [])
            if positions:
                pos = random.choice(positions)
                # 随机卖出30%-100%的持仓
                sell_pct = random.uniform(0.3, 1.0)
                shares = int(pos['shares'] * sell_pct / 100) * 100

                if shares >= 100:
                    return TradingDecision(
                        action='sell',
                        ts_code=pos['ts_code'],
                        shares=shares,
                        reason="随机卖出决策"
                    )

        return TradingDecision(action='hold', reason="随机持有决策")


if __name__ == '__main__':
    # 测试Agent
    print("=" * 60)
    print("交易Agent测试")
    print("=" * 60)

    # 创建测试上下文
    context = MarketContext(
        date='20250101',
        available_stocks=[
            {'ts_code': '600000.SH', 'name': '浦发银行', 'industry': '银行',
             'close': 8.5, 'change': 1.2},
            {'ts_code': '600036.SH', 'name': '招商银行', 'industry': '银行',
             'close': 42.3, 'change': -0.5},
        ],
        current_portfolio={
            'cash': 1000000,
            'market_value': 0,
            'total_assets': 1000000,
            'total_return_pct': 0,
            'positions': []
        },
        market_data={}
    )

    # 测试Random Agent
    agent = RandomAgent()
    decision = agent.make_decision(context)
    print(f"\n{agent.name} 决策:")
    print(f"  操作: {decision.action}")
    if decision.ts_code:
        print(f"  股票: {decision.ts_code}")
        print(f"  股数: {decision.shares}")
    print(f"  理由: {decision.reason}")

    print("\n" + "=" * 60)
