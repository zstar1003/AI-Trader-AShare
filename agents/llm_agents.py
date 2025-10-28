"""
具体的AI交易Agent实现
"""
import os
from .base_agent import LLMTradingAgent
from dotenv import load_dotenv

load_dotenv()


class DeepSeekAgent(LLMTradingAgent):
    """DeepSeek模型交易Agent"""

    def __init__(self, name: str = "DeepSeek Trader"):
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment")

        super().__init__(
            name=name,
            model_name="deepseek-ai/DeepSeek-V3.2-Exp",
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )


class GPT4Agent(LLMTradingAgent):
    """GPT-4模型交易Agent"""

    def __init__(self, name: str = "GPT-4 Trader"):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        super().__init__(
            name=name,
            model_name="openai/gpt-4o",
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )


class ClaudeAgent(LLMTradingAgent):
    """Claude模型交易Agent"""

    def __init__(self, name: str = "Claude Trader"):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        super().__init__(
            name=name,
            model_name="anthropic/claude-3.5-sonnet",
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )


class Qwen3Agent(LLMTradingAgent):
    """通义千问模型交易Agent"""

    def __init__(self, name: str = "Qwen3 Trader"):
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment")

        super().__init__(
            name=name,
            model_name="Qwen/Qwen2.5-72B-Instruct",
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
