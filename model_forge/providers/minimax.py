"""
MiniMax 服务商
官方文档: https://platform.minimaxi.com/docs
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


class MiniMaxProvider(BaseProvider):
    """MiniMax 服务商"""

    provider_type = ProviderType.MINIMAX
    display_name = "MiniMax"
    website = "https://www.minimaxi.com"
    capabilities = [
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.CODE_GENERATION,
        ProviderCapability.LONG_CONTEXT,
        ProviderCapability.EMBEDDING,
    ]

    DEFAULT_BASE_URL = "https://api.minimax.chat/v1"

    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                name="MiniMax-Text-01",
                display_name="MiniMax-01",
                description="4560亿参数，400万token上下文，综合性能与国际领先模型相当",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=16384,
                context_length=4000000,  # 400万token
                price_input=1.0,
                price_output=8.0,
            ),
            ModelInfo(
                name="abab6.5s-chat",
                display_name="abab6.5s",
                description="万亿参数MoE模型，平衡性能和成本",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=8192,
                context_length=245000,
                price_input=1.0,
                price_output=4.0,
            ),
            ModelInfo(
                name="abab6.5g-chat",
                display_name="abab6.5g",
                description="通用对话模型，适合复杂生产力场景",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CODE_GENERATION,
                ],
                max_tokens=8192,
                context_length=245000,
                price_input=2.0,
                price_output=8.0,
            ),
            ModelInfo(
                name="abab5.5s-chat",
                display_name="abab5.5s",
                description="轻量级模型，响应速度快",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=4096,
                context_length=16384,
                price_input=0.5,
                price_output=1.0,
            ),
            ModelInfo(
                name="MiniMax-M2.1",
                display_name="MiniMax M2.1",
                description="最新M系列模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CODE_GENERATION,
                ],
                max_tokens=16384,
                context_length=128000,
                price_input=2.0,
                price_output=8.0,
            ),
        ]

    def _get_base_url(self) -> str:
        return self.config.base_url or self.DEFAULT_BASE_URL

    def _build_headers(self) -> Dict[str, str]:
        """MiniMax使用不同的认证方式"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
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

        # MiniMax特有参数
        if "top_p" in kwargs:
            body["top_p"] = kwargs["top_p"]
        if "tokens_to_generate" in kwargs:
            body["tokens_to_generate"] = kwargs["tokens_to_generate"]
        if "mask_sensitive_info" in kwargs:
            body["mask_sensitive_info"] = kwargs["mask_sensitive_info"]

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
