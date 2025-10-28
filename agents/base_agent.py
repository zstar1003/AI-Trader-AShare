"""
AI交易Agent基类 - 使用LangChain新API
"""
import os
from abc import ABC, abstractmethod
from typing import List
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


class BaseTradingAgent(ABC):
    """交易Agent基类"""

    def __init__(self, name: str, model_name: str):
        self.name = name
        self.model_name = model_name
        self.agent = None

    @abstractmethod
    def create_agent(self, tools: List):
        """创建Agent"""
        pass

    def make_decision(self, context: str) -> str:
        """
        做出交易决策

        Args:
            context: 市场上下文信息

        Returns:
            str: Agent的决策和执行结果
        """
        if not self.agent:
            raise RuntimeError("Agent未初始化，请先调用create_agent")

        try:
            result = self.agent.invoke({"messages": [{"role": "user", "content": context}]})

            # 提取最后的消息
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif isinstance(last_message, dict):
                    return last_message.get('content', str(last_message))

            return str(result)
        except Exception as e:
            return f"Agent执行失败: {str(e)}"


class LLMTradingAgent(BaseTradingAgent):
    """基于LLM的交易Agent"""

    def __init__(self, name: str, model_name: str, api_key: str, base_url: str):
        super().__init__(name, model_name)
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0.7
        )

    def create_agent(self, tools: List):
        """创建LangChain Agent"""

        # 系统提示词
        system_prompt = """你是一位专业的A股量化交易员，负责管理一个投资组合。

你的任务：
1. 分析当前市场情况和投资组合状态
2. 基于技术分析和风险管理做出交易决策
3. 使用提供的工具执行交易操作

交易规则：
- 初始资金100万人民币
- 每次买入时，建议单只股票投入资金不超过总资产的30%
- 考虑分散投资，建议持有3-5只股票
- 注意控制风险，设置止损点
- 买入股数必须是100的倍数（A股最小交易单位）
- 考虑交易成本：佣金0.03%，最低5元；卖出时额外0.1%印花税

决策流程建议：
1. 首先调用 get_portfolio_status 查看当前持仓状态
2. 调用 get_available_stocks 查看可交易股票列表
3. 如果需要，调用 get_stock_price 查看具体股票的价格信息
4. 根据分析决定是否买入或卖出
5. 如果买入，使用 buy_stock 工具；如果卖出，使用 sell_stock 工具

请认真分析市场，做出理性的投资决策。"""

        # 使用新的create_agent API
        self.agent = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=system_prompt
        )

        return self.agent
