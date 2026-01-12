"""
AI服务商基类定义
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, AsyncIterator
import httpx


class ProviderType(str, Enum):
    """服务商类型"""
    DEEPSEEK = "deepseek"
    DOUBAO = "doubao"
    KIMI = "kimi"
    MINIMAX = "minimax"
    ZHIPU = "zhipu"
    BAICHUAN = "baichuan"
    SPARK = "spark"
    QWEN = "qwen"
    YI = "yi"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"


class ProviderCapability(str, Enum):
    """服务商能力"""
    TEXT_GENERATION = "text_generation"      # 文本生成
    IMAGE_GENERATION = "image_generation"    # 图像生成
    IMAGE_UNDERSTANDING = "image_understanding"  # 图像理解
    MODEL_3D_GENERATION = "model_3d_generation"  # 3D模型生成
    CODE_GENERATION = "code_generation"      # 代码生成
    EMBEDDING = "embedding"                  # 向量化
    FUNCTION_CALLING = "function_calling"    # 函数调用
    LONG_CONTEXT = "long_context"            # 长上下文
    REASONING = "reasoning"                  # 深度推理


@dataclass
class ProviderConfig:
    """服务商配置"""
    provider_type: ProviderType
    api_key: str
    base_url: Optional[str] = None
    model: Optional[str] = None
    timeout: int = 120
    max_retries: int = 3
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelInfo:
    """模型信息"""
    name: str
    display_name: str
    description: str
    capabilities: List[ProviderCapability]
    max_tokens: int = 4096
    context_length: int = 8192
    price_input: float = 0.0   # 元/百万tokens
    price_output: float = 0.0  # 元/百万tokens
    supports_streaming: bool = True
    supports_vision: bool = False


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # system, user, assistant
    content: str
    images: Optional[List[str]] = None  # base64或URL


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict] = None


class BaseProvider(ABC):
    """AI服务商基类"""

    provider_type: ProviderType
    display_name: str
    website: str
    capabilities: List[ProviderCapability]

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.client = httpx.Client(timeout=config.timeout)
        self.async_client = httpx.AsyncClient(timeout=config.timeout)

    @property
    @abstractmethod
    def available_models(self) -> List[ModelInfo]:
        """获取可用模型列表"""
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> ChatResponse:
        """同步聊天接口"""
        pass

    @abstractmethod
    async def achat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> ChatResponse:
        """异步聊天接口"""
        pass

    async def astream_chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """流式聊天接口"""
        raise NotImplementedError(f"{self.display_name} 不支持流式聊天")

    def get_default_model(self) -> str:
        """获取默认模型"""
        if self.config.model:
            return self.config.model
        models = self.available_models
        return models[0].name if models else ""

    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }

    def close(self):
        """关闭客户端"""
        self.client.close()

    async def aclose(self):
        """异步关闭客户端"""
        await self.async_client.aclose()
