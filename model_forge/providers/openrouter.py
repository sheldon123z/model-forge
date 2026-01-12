"""
OpenRouter 服务商 - AI模型聚合平台
官方文档: https://openrouter.ai/docs
"""

from typing import Optional, List, Dict, Any, AsyncIterator
import json
from .base import (
    BaseProvider,
    ProviderType,
    ProviderCapability,
    ProviderConfig,
    ModelInfo,
    ChatMessage,
    ChatResponse,
)


class OpenRouterProvider(BaseProvider):
    """OpenRouter 服务商 - 聚合400+模型"""

    provider_type = ProviderType.OPENROUTER
    display_name = "OpenRouter"
    website = "https://openrouter.ai"
    capabilities = [
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.CODE_GENERATION,
        ProviderCapability.IMAGE_UNDERSTANDING,
        ProviderCapability.FUNCTION_CALLING,
        ProviderCapability.LONG_CONTEXT,
        ProviderCapability.REASONING,
    ]

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

    @property
    def available_models(self) -> List[ModelInfo]:
        """返回常用模型列表 - OpenRouter支持400+模型"""
        return [
            # Anthropic Claude
            ModelInfo(
                name="anthropic/claude-sonnet-4",
                display_name="Claude Sonnet 4",
                description="Anthropic最新Claude模型，擅长编程和Agent任务",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CODE_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=8192,
                context_length=200000,
                price_input=3.0,
                price_output=15.0,
            ),
            ModelInfo(
                name="anthropic/claude-3.5-sonnet",
                display_name="Claude 3.5 Sonnet",
                description="Claude 3.5版本，性能出色",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CODE_GENERATION,
                ],
                max_tokens=8192,
                context_length=200000,
                price_input=3.0,
                price_output=15.0,
            ),
            # Google Gemini
            ModelInfo(
                name="google/gemini-2.5-pro",
                display_name="Gemini 2.5 Pro",
                description="Google最新模型，擅长长文本分析和多模态",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=8192,
                context_length=2000000,
                price_input=1.25,
                price_output=5.0,
                supports_vision=True,
            ),
            ModelInfo(
                name="google/gemini-2.5-flash",
                display_name="Gemini 2.5 Flash",
                description="快速响应版本，适合实时交互",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                ],
                max_tokens=8192,
                context_length=1000000,
                price_input=0.075,
                price_output=0.3,
                supports_vision=True,
            ),
            # OpenAI
            ModelInfo(
                name="openai/gpt-4o",
                display_name="GPT-4o",
                description="OpenAI多模态旗舰模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=16384,
                context_length=128000,
                price_input=2.5,
                price_output=10.0,
                supports_vision=True,
            ),
            ModelInfo(
                name="openai/gpt-4o-mini",
                display_name="GPT-4o Mini",
                description="性价比版本",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=16384,
                context_length=128000,
                price_input=0.15,
                price_output=0.6,
            ),
            ModelInfo(
                name="openai/o1",
                display_name="OpenAI o1",
                description="深度推理模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.REASONING,
                ],
                max_tokens=100000,
                context_length=200000,
                price_input=15.0,
                price_output=60.0,
            ),
            # DeepSeek
            ModelInfo(
                name="deepseek/deepseek-chat",
                display_name="DeepSeek V3",
                description="DeepSeek最新模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CODE_GENERATION,
                ],
                max_tokens=8192,
                context_length=64000,
                price_input=0.14,
                price_output=0.28,
            ),
            ModelInfo(
                name="deepseek/deepseek-r1",
                display_name="DeepSeek R1",
                description="DeepSeek推理模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.REASONING,
                ],
                max_tokens=64000,
                context_length=64000,
                price_input=0.55,
                price_output=2.19,
            ),
            # Meta Llama
            ModelInfo(
                name="meta-llama/llama-3.3-70b-instruct",
                display_name="Llama 3.3 70B",
                description="Meta开源模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=8192,
                context_length=131072,
                price_input=0.35,
                price_output=0.4,
            ),
            # Qwen
            ModelInfo(
                name="qwen/qwen-2.5-72b-instruct",
                display_name="Qwen 2.5 72B",
                description="阿里通义千问开源模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CODE_GENERATION,
                ],
                max_tokens=8192,
                context_length=131072,
                price_input=0.35,
                price_output=0.4,
            ),
        ]

    def _get_base_url(self) -> str:
        return self.config.base_url or self.DEFAULT_BASE_URL

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }
        # OpenRouter特有的可选headers
        extra = self.config.extra_params
        if "site_url" in extra:
            headers["HTTP-Referer"] = extra["site_url"]
        if "site_name" in extra:
            headers["X-Title"] = extra["site_name"]
        return headers

    def _format_messages(self, messages: List[ChatMessage]) -> List[Dict]:
        """格式化消息，支持多模态"""
        formatted = []
        for msg in messages:
            if msg.images:
                content = [{"type": "text", "text": msg.content}]
                for img in msg.images:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": img}
                    })
                formatted.append({"role": msg.role, "content": content})
            else:
                formatted.append({"role": msg.role, "content": msg.content})
        return formatted

    def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> ChatResponse:
        model = model or self.get_default_model()
        url = f"{self._get_base_url()}/chat/completions"

        body = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens

        # OpenRouter特有参数
        if "transforms" in kwargs:
            body["transforms"] = kwargs["transforms"]
        if "route" in kwargs:
            body["route"] = kwargs["route"]
        if "tools" in kwargs:
            body["tools"] = kwargs["tools"]
        if "provider" in kwargs:
            body["provider"] = kwargs["provider"]

        response = self.client.post(
            url,
            headers=self._build_headers(),
            json=body
        )
        response.raise_for_status()
        data = response.json()

        return ChatResponse(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", model),
            usage=data.get("usage"),
            finish_reason=data["choices"][0].get("finish_reason"),
            raw_response=data
        )

    async def achat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> ChatResponse:
        model = model or self.get_default_model()
        url = f"{self._get_base_url()}/chat/completions"

        body = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens

        response = await self.async_client.post(
            url,
            headers=self._build_headers(),
            json=body
        )
        response.raise_for_status()
        data = response.json()

        return ChatResponse(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", model),
            usage=data.get("usage"),
            finish_reason=data["choices"][0].get("finish_reason"),
            raw_response=data
        )

    async def astream_chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        model = model or self.get_default_model()
        url = f"{self._get_base_url()}/chat/completions"

        body = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens

        async with self.async_client.stream(
            "POST",
            url,
            headers=self._build_headers(),
            json=body
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue
