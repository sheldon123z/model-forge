"""
百川 (Baichuan) 服务商
官方文档: https://platform.baichuan-ai.com/docs/api
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


class BaichuanProvider(BaseProvider):
    """百川 服务商"""

    provider_type = ProviderType.BAICHUAN
    display_name = "百川 (Baichuan)"
    website = "https://www.baichuan-ai.com"
    capabilities = [
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.LONG_CONTEXT,
        ProviderCapability.FUNCTION_CALLING,
    ]

    DEFAULT_BASE_URL = "https://api.baichuan-ai.com/v1"

    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                name="Baichuan4",
                display_name="Baichuan 4",
                description="最新旗舰模型，支持搜索增强和192K长窗口",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.LONG_CONTEXT,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=8192,
                context_length=192000,
                price_input=100.0,
                price_output=100.0,
            ),
            ModelInfo(
                name="Baichuan3-Turbo",
                display_name="Baichuan 3 Turbo",
                description="性价比版本，响应速度快",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=4096,
                context_length=32000,
                price_input=12.0,
                price_output=12.0,
            ),
            ModelInfo(
                name="Baichuan3-Turbo-128k",
                display_name="Baichuan 3 Turbo 128K",
                description="长上下文版本",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=8192,
                context_length=128000,
                price_input=24.0,
                price_output=24.0,
            ),
            ModelInfo(
                name="Baichuan2-Turbo",
                display_name="Baichuan 2 Turbo",
                description="基础版本，成本低",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=4096,
                context_length=8192,
                price_input=8.0,
                price_output=8.0,
            ),
            ModelInfo(
                name="Baichuan-NPC-Turbo",
                display_name="Baichuan NPC",
                description="角色扮演优化版本",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=4096,
                context_length=8192,
                price_input=8.0,
                price_output=8.0,
            ),
        ]

    def _get_base_url(self) -> str:
        return self.config.base_url or self.DEFAULT_BASE_URL

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

        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        body = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens

        # 百川特有参数
        if "top_p" in kwargs:
            body["top_p"] = kwargs["top_p"]
        if "top_k" in kwargs:
            body["top_k"] = kwargs["top_k"]
        if "with_search_enhance" in kwargs:
            body["with_search_enhance"] = kwargs["with_search_enhance"]

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

        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        body = {
            "model": model,
            "messages": formatted_messages,
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

        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        body = {
            "model": model,
            "messages": formatted_messages,
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
