"""
零一万物 (Yi) 服务商
官方文档: https://platform.lingyiwanwu.com/docs
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


class YiProvider(BaseProvider):
    """零一万物 服务商"""

    provider_type = ProviderType.YI
    display_name = "零一万物 (Yi)"
    website = "https://www.lingyiwanwu.com"
    capabilities = [
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.CODE_GENERATION,
        ProviderCapability.IMAGE_UNDERSTANDING,
        ProviderCapability.LONG_CONTEXT,
    ]

    DEFAULT_BASE_URL = "https://api.lingyiwanwu.com/v1"

    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                name="yi-large",
                display_name="Yi Large",
                description="旗舰模型，LMSYS榜单TOP10唯一中国模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CODE_GENERATION,
                ],
                max_tokens=16384,
                context_length=32768,
                price_input=20.0,
                price_output=20.0,
            ),
            ModelInfo(
                name="yi-large-turbo",
                display_name="Yi Large Turbo",
                description="性价比版本，响应速度快",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=16384,
                context_length=16384,
                price_input=12.0,
                price_output=12.0,
            ),
            ModelInfo(
                name="yi-medium",
                display_name="Yi Medium",
                description="中等版本，平衡性能和成本",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=16384,
                context_length=16384,
                price_input=2.5,
                price_output=2.5,
            ),
            ModelInfo(
                name="yi-medium-200k",
                display_name="Yi Medium 200K",
                description="超长上下文版本，支持20-30万汉字",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=16384,
                context_length=200000,
                price_input=12.0,
                price_output=12.0,
            ),
            ModelInfo(
                name="yi-spark",
                display_name="Yi Spark",
                description="轻量版本，成本低",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=16384,
                context_length=16384,
                price_input=1.0,
                price_output=1.0,
            ),
            ModelInfo(
                name="yi-vision",
                display_name="Yi Vision",
                description="多模态视觉理解模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                ],
                max_tokens=4096,
                context_length=16384,
                price_input=6.0,
                price_output=6.0,
                supports_vision=True,
            ),
        ]

    def _get_base_url(self) -> str:
        return self.config.base_url or self.DEFAULT_BASE_URL

    def _format_messages(self, messages: List[ChatMessage]) -> List[Dict]:
        """格式化消息，支持视觉理解"""
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

        # Yi特有参数
        if "top_p" in kwargs:
            body["top_p"] = kwargs["top_p"]
        if "top_k" in kwargs:
            body["top_k"] = kwargs["top_k"]

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
