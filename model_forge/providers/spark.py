"""
讯飞星火 (Spark) 服务商
官方文档: https://www.xfyun.cn/doc/spark/Web.html
"""

from typing import Optional, List, Dict, Any, AsyncIterator
import json
import hmac
import hashlib
import base64
from datetime import datetime
from urllib.parse import urlencode
from .base import (
    BaseProvider,
    ProviderType,
    ProviderCapability,
    ProviderConfig,
    ModelInfo,
    ChatMessage,
    ChatResponse,
)


class SparkProvider(BaseProvider):
    """讯飞星火 服务商"""

    provider_type = ProviderType.SPARK
    display_name = "讯飞星火 (Spark)"
    website = "https://xinghuo.xfyun.cn"
    capabilities = [
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.CODE_GENERATION,
        ProviderCapability.FUNCTION_CALLING,
        ProviderCapability.LONG_CONTEXT,
        ProviderCapability.IMAGE_UNDERSTANDING,
    ]

    # HTTP API 地址
    DEFAULT_BASE_URL = "https://spark-api-open.xf-yun.com/v1"

    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                name="4.0Ultra",
                display_name="星火 4.0 Ultra",
                description="最强版本，支持联网搜索、Function Call、System角色",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=8192,
                context_length=8192,
                price_input=0,  # 讯飞按次计费
                price_output=0,
            ),
            ModelInfo(
                name="generalv3.5",
                display_name="星火 Max",
                description="高性能版本，支持128K上下文",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=8192,
                context_length=8192,
                price_input=0,
                price_output=0,
            ),
            ModelInfo(
                name="max-32k",
                display_name="星火 Max 32K",
                description="长上下文版本",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=8192,
                context_length=32768,
                price_input=0,
                price_output=0,
            ),
            ModelInfo(
                name="pro-128k",
                display_name="星火 Pro 128K",
                description="超长上下文版本",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=4096,
                context_length=131072,
                price_input=0,
                price_output=0,
            ),
            ModelInfo(
                name="generalv3",
                display_name="星火 Pro",
                description="专业版本，支持搜索等内置插件",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=8192,
                context_length=8192,
                price_input=0,
                price_output=0,
            ),
            ModelInfo(
                name="lite",
                display_name="星火 Lite",
                description="轻量版本，响应快，免费使用",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=4096,
                context_length=8192,
                price_input=0,
                price_output=0,
            ),
        ]

    def _get_base_url(self) -> str:
        return self.config.base_url or self.DEFAULT_BASE_URL

    def _build_headers(self) -> Dict[str, str]:
        """星火API使用Bearer Token认证"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }

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

        # 星火特有参数
        if "top_k" in kwargs:
            body["top_k"] = kwargs["top_k"]
        if "tools" in kwargs:
            body["tools"] = kwargs["tools"]

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
