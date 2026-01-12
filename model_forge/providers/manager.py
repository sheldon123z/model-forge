"""
服务商管理器 - 统一管理所有AI服务商
"""

from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass
from .base import (
    BaseProvider,
    ProviderType,
    ProviderCapability,
    ProviderConfig,
    ModelInfo,
    ChatMessage,
    ChatResponse,
)
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


@dataclass
class ProviderInfo:
    """服务商信息"""
    provider_type: ProviderType
    display_name: str
    website: str
    capabilities: List[ProviderCapability]
    description: str
    api_doc_url: str
    models: List[ModelInfo]


class ProviderManager:
    """服务商管理器"""

    # 注册的服务商类
    PROVIDER_CLASSES: Dict[ProviderType, Type[BaseProvider]] = {
        ProviderType.DEEPSEEK: DeepSeekProvider,
        ProviderType.DOUBAO: DoubaoProvider,
        ProviderType.KIMI: KimiProvider,
        ProviderType.MINIMAX: MiniMaxProvider,
        ProviderType.ZHIPU: ZhipuProvider,
        ProviderType.BAICHUAN: BaichuanProvider,
        ProviderType.SPARK: SparkProvider,
        ProviderType.QWEN: QwenProvider,
        ProviderType.YI: YiProvider,
        ProviderType.OPENROUTER: OpenRouterProvider,
        ProviderType.GEMINI: GeminiProvider,
    }

    # 服务商描述信息
    PROVIDER_DESCRIPTIONS = {
        ProviderType.DEEPSEEK: {
            "description": "深度求索，国产顶尖开源大模型，以极低成本提供强大的代码和推理能力",
            "api_doc_url": "https://api-docs.deepseek.com/",
        },
        ProviderType.DOUBAO: {
            "description": "字节跳动豆包，火山引擎大模型平台，支持文本、图像、3D模型生成",
            "api_doc_url": "https://www.volcengine.com/docs/82379",
        },
        ProviderType.KIMI: {
            "description": "月之暗面Kimi，万亿参数K2模型，擅长Agent任务和代码生成，支持256K超长上下文",
            "api_doc_url": "https://platform.moonshot.cn/docs",
        },
        ProviderType.MINIMAX: {
            "description": "MiniMax，4560亿参数模型，支持400万token超长上下文",
            "api_doc_url": "https://platform.minimaxi.com/docs",
        },
        ProviderType.ZHIPU: {
            "description": "智谱AI GLM系列，提供永久免费的GLM-4-Flash模型，支持1M超长上下文",
            "api_doc_url": "https://open.bigmodel.cn/dev/api",
        },
        ProviderType.BAICHUAN: {
            "description": "百川智能，支持搜索增强和192K长窗口，角色扮演能力出色",
            "api_doc_url": "https://platform.baichuan-ai.com/docs/api",
        },
        ProviderType.SPARK: {
            "description": "讯飞星火，支持联网搜索、内置插件、Function Call等功能",
            "api_doc_url": "https://www.xfyun.cn/doc/spark/Web.html",
        },
        ProviderType.QWEN: {
            "description": "阿里通义千问，阿里云百炼平台，支持思考模式和多种专业模型",
            "api_doc_url": "https://help.aliyun.com/zh/model-studio/qwen-api-reference",
        },
        ProviderType.YI: {
            "description": "零一万物Yi，LMSYS榜单TOP10唯一中国模型，支持200K超长上下文",
            "api_doc_url": "https://platform.lingyiwanwu.com/docs",
        },
        ProviderType.OPENROUTER: {
            "description": "OpenRouter，AI模型聚合平台，统一API访问400+模型，无地域限制",
            "api_doc_url": "https://openrouter.ai/docs",
        },
        ProviderType.GEMINI: {
            "description": "Google Gemini，支持2M超长上下文，擅长多模态理解和推理",
            "api_doc_url": "https://ai.google.dev/docs",
        },
    }

    def __init__(self):
        self._providers: Dict[ProviderType, BaseProvider] = {}
        self._configs: Dict[ProviderType, ProviderConfig] = {}

    def configure(self, provider_type: ProviderType, api_key: str, **kwargs) -> None:
        """
        配置服务商

        Args:
            provider_type: 服务商类型
            api_key: API密钥
            **kwargs: 其他配置参数 (base_url, model, timeout等)
        """
        config = ProviderConfig(
            provider_type=provider_type,
            api_key=api_key,
            base_url=kwargs.get("base_url"),
            model=kwargs.get("model"),
            timeout=kwargs.get("timeout", 120),
            max_retries=kwargs.get("max_retries", 3),
            extra_params=kwargs.get("extra_params", {}),
        )
        self._configs[provider_type] = config

        # 如果已经有实例，重新创建
        if provider_type in self._providers:
            self._providers[provider_type].close()
            del self._providers[provider_type]

    def get_provider(self, provider_type: ProviderType) -> BaseProvider:
        """
        获取服务商实例

        Args:
            provider_type: 服务商类型

        Returns:
            服务商实例
        """
        if provider_type not in self._providers:
            if provider_type not in self._configs:
                raise ValueError(f"服务商 {provider_type.value} 未配置，请先调用 configure()")

            provider_class = self.PROVIDER_CLASSES.get(provider_type)
            if not provider_class:
                raise ValueError(f"不支持的服务商类型: {provider_type.value}")

            self._providers[provider_type] = provider_class(self._configs[provider_type])

        return self._providers[provider_type]

    def chat(
        self,
        provider_type: ProviderType,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """
        使用指定服务商进行聊天

        Args:
            provider_type: 服务商类型
            messages: 消息列表
            model: 模型名称
            **kwargs: 其他参数

        Returns:
            聊天响应
        """
        provider = self.get_provider(provider_type)
        return provider.chat(messages, model, **kwargs)

    async def achat(
        self,
        provider_type: ProviderType,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """异步聊天"""
        provider = self.get_provider(provider_type)
        return await provider.achat(messages, model, **kwargs)

    @classmethod
    def list_providers(cls) -> List[ProviderInfo]:
        """
        列出所有支持的服务商

        Returns:
            服务商信息列表
        """
        providers = []
        for provider_type, provider_class in cls.PROVIDER_CLASSES.items():
            desc_info = cls.PROVIDER_DESCRIPTIONS.get(provider_type, {})

            # 临时创建实例获取模型列表
            dummy_config = ProviderConfig(
                provider_type=provider_type,
                api_key="dummy"
            )
            try:
                temp_provider = provider_class(dummy_config)
                models = temp_provider.available_models
            except Exception:
                models = []

            providers.append(ProviderInfo(
                provider_type=provider_type,
                display_name=provider_class.display_name,
                website=provider_class.website,
                capabilities=provider_class.capabilities,
                description=desc_info.get("description", ""),
                api_doc_url=desc_info.get("api_doc_url", ""),
                models=models,
            ))

        return providers

    @classmethod
    def get_provider_info(cls, provider_type: ProviderType) -> Optional[ProviderInfo]:
        """获取单个服务商信息"""
        providers = cls.list_providers()
        for p in providers:
            if p.provider_type == provider_type:
                return p
        return None

    @classmethod
    def list_providers_by_capability(
        cls,
        capability: ProviderCapability
    ) -> List[ProviderInfo]:
        """
        按能力筛选服务商

        Args:
            capability: 所需能力

        Returns:
            支持该能力的服务商列表
        """
        return [
            p for p in cls.list_providers()
            if capability in p.capabilities
        ]

    def close_all(self) -> None:
        """关闭所有服务商连接"""
        for provider in self._providers.values():
            provider.close()
        self._providers.clear()

    async def aclose_all(self) -> None:
        """异步关闭所有服务商连接"""
        for provider in self._providers.values():
            await provider.aclose()
        self._providers.clear()


# 全局管理器实例
_global_manager: Optional[ProviderManager] = None


def get_provider_manager() -> ProviderManager:
    """获取全局服务商管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = ProviderManager()
    return _global_manager


def configure_provider(provider_type: ProviderType, api_key: str, **kwargs) -> None:
    """配置服务商的快捷函数"""
    get_provider_manager().configure(provider_type, api_key, **kwargs)


def chat(
    provider_type: ProviderType,
    messages: List[ChatMessage],
    model: Optional[str] = None,
    **kwargs
) -> ChatResponse:
    """聊天的快捷函数"""
    return get_provider_manager().chat(provider_type, messages, model, **kwargs)
