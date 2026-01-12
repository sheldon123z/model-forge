"""
Kimi (月之暗面/Moonshot) 服务商
官方文档: https://platform.moonshot.cn/docs
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


class KimiProvider(BaseProvider):
    """Kimi/月之暗面 服务商"""

    provider_type = ProviderType.KIMI
    display_name = "Kimi (月之暗面)"
    website = "https://platform.moonshot.cn"
    capabilities = [
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.CODE_GENERATION,
        ProviderCapability.FUNCTION_CALLING,
        ProviderCapability.LONG_CONTEXT,
        ProviderCapability.IMAGE_UNDERSTANDING,
        ProviderCapability.REASONING,
    ]

    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"

    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                name="moonshot-v1-8k",
                display_name="Moonshot V1 8K",
                description="基础版本，8K上下文窗口",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=4096,
                context_length=8192,
                price_input=12.0,
                price_output=12.0,
            ),
            ModelInfo(
                name="moonshot-v1-32k",
                display_name="Moonshot V1 32K",
                description="标准版本，32K上下文窗口",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=8192,
                context_length=32768,
                price_input=24.0,
                price_output=24.0,
            ),
            ModelInfo(
                name="moonshot-v1-128k",
                display_name="Moonshot V1 128K",
                description="长文本版本，128K上下文窗口",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=16384,
                context_length=131072,
                price_input=60.0,
                price_output=60.0,
            ),
            ModelInfo(
                name="kimi-k2-0711",
                display_name="Kimi K2",
                description="万亿参数MoE模型，擅长Agent任务和代码生成",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CODE_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=32768,
                context_length=131072,
                price_input=2.0,
                price_output=8.0,
            ),
            ModelInfo(
                name="kimi-k2-thinking",
                display_name="Kimi K2 Thinking",
                description="K2深度推理版本，支持256K上下文",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.REASONING,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=65536,
                context_length=262144,
                price_input=4.0,
                price_output=16.0,
            ),
            ModelInfo(
                name="moonshot-v1-vision-preview",
                display_name="Moonshot Vision",
                description="多模态图片理解模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                ],
                max_tokens=4096,
                context_length=32768,
                price_input=24.0,
                price_output=24.0,
                supports_vision=True,
            ),
        ]

    def _get_base_url(self) -> str:
        return self.config.base_url or self.DEFAULT_BASE_URL

    def _format_messages(self, messages: List[ChatMessage]) -> List[Dict]:
        """格式化消息，支持图片理解"""
        formatted = []
        for msg in messages:
            if msg.images:
                # 多模态消息
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

        # Kimi特有参数
        if "tools" in kwargs:
            body["tools"] = kwargs["tools"]
        if "tool_choice" in kwargs:
            body["tool_choice"] = kwargs["tool_choice"]

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
