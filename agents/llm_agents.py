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

class Qwen3Agent(LLMTradingAgent):
    """通义千问模型交易Agent"""

    def __init__(self, name: str = "Qwen3 Trader"):
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment")

        super().__init__(
            name=name,
            model_name="Qwen/QwQ-32B",
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )

class GLMAgent(LLMTradingAgent):
    """GLM模型交易Agent"""

    def __init__(self, name: str = "GLM Trader"):
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment")

        super().__init__(
            name=name,
            model_name="zai-org/GLM-4.6",
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )

class KimiAgent(LLMTradingAgent):
    """Kimi模型交易Agent"""

    def __init__(self, name: str = "Kimi Trader"):
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment")

        super().__init__(
            name=name,
            model_name="moonshotai/Kimi-K2-Instruct-0905",
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )

class RingAgent(LLMTradingAgent):
    """Ring模型交易Agent"""

    def __init__(self, name: str = "Ring Trader"):
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment")

        super().__init__(
            name=name,
            model_name="inclusionAI/Ring-1T",
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )

class StepAgent(LLMTradingAgent):
    """Step模型交易Agent"""

    def __init__(self, name: str = "Step Trader"):
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment")

        super().__init__(
            name=name,
            model_name="stepfun-ai/step3",
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )