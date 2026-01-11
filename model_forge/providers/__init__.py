"""
AI服务商管理模块

支持多种AI服务商的统一接口管理，包括：
- DeepSeek
- 豆包 (Doubao/ByteDance)
- Kimi (月之暗面/Moonshot)
- MiniMax
- 智谱AI (GLM)
- 百川 (Baichuan)
- 讯飞星火 (Spark)
- 通义千问 (Qwen/阿里云)
- 零一万物 (Yi)
- OpenRouter
- Google Gemini
"""

from .base import (
    BaseProvider,
    ProviderType,
    ProviderCapability,
    ProviderConfig,
)
from .manager import ProviderManager
from .deepseek import DeepSeekProvider
from .doubao import DoubaoProvider
from .kimi import KimiProvider
from .minimax import MiniMaxProvider
from .zhipu import ZhipuProvider
from .baichuan import BaichuanProvider
from .spark import SparkProvider
from .qwen import QwenProvider
from .yi import YiProvider
from .openrouter import OpenRouterProvider
from .gemini import GeminiProvider

__all__ = [
    "BaseProvider",
    "ProviderType",
    "ProviderCapability",
    "ProviderConfig",
    "ProviderManager",
    "DeepSeekProvider",
    "DoubaoProvider",
    "KimiProvider",
    "MiniMaxProvider",
    "ZhipuProvider",
    "BaichuanProvider",
    "SparkProvider",
    "QwenProvider",
    "YiProvider",
    "OpenRouterProvider",
    "GeminiProvider",
]
