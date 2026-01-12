"""
Google Gemini 服务商
官方文档: https://ai.google.dev/docs
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


class GeminiProvider(BaseProvider):
    """Google Gemini 服务商"""

    provider_type = ProviderType.GEMINI
    display_name = "Google Gemini"
    website = "https://ai.google.dev"
    capabilities = [
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.IMAGE_GENERATION,
        ProviderCapability.IMAGE_UNDERSTANDING,
        ProviderCapability.CODE_GENERATION,
        ProviderCapability.FUNCTION_CALLING,
        ProviderCapability.LONG_CONTEXT,
        ProviderCapability.REASONING,
    ]

    # 使用OpenAI兼容的API
    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"

    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                name="gemini-2.5-pro-preview",
                display_name="Gemini 2.5 Pro",
                description="最强版本，支持2M上下文，擅长推理和多模态",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                    ProviderCapability.REASONING,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=65536,
                context_length=2097152,
                price_input=1.25,
                price_output=5.0,
                supports_vision=True,
            ),
            ModelInfo(
                name="gemini-2.5-flash-preview",
                display_name="Gemini 2.5 Flash",
                description="快速版本，支持1M上下文",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                ],
                max_tokens=65536,
                context_length=1048576,
                price_input=0.075,
                price_output=0.3,
                supports_vision=True,
            ),
            ModelInfo(
                name="gemini-2.0-flash-exp",
                display_name="Gemini 2.0 Flash",
                description="实验版本，响应极快",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                ],
                max_tokens=8192,
                context_length=1048576,
                price_input=0,  # 实验版免费
                price_output=0,
                supports_vision=True,
            ),
            ModelInfo(
                name="gemini-2.0-flash-exp-image-generation",
                display_name="Gemini 2.0 Flash 图像生成",
                description="支持图像生成的版本",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_GENERATION,
                ],
                max_tokens=8192,
                context_length=32768,
                price_input=0,
                price_output=0,
            ),
            ModelInfo(
                name="gemini-1.5-pro",
                display_name="Gemini 1.5 Pro",
                description="稳定版本，2M上下文",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=8192,
                context_length=2097152,
                price_input=1.25,
                price_output=5.0,
                supports_vision=True,
            ),
            ModelInfo(
                name="gemini-1.5-flash",
                display_name="Gemini 1.5 Flash",
                description="快速稳定版本",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                ],
                max_tokens=8192,
                context_length=1048576,
                price_input=0.075,
                price_output=0.3,
                supports_vision=True,
            ),
        ]

    def _get_base_url(self) -> str:
        return self.config.base_url or self.DEFAULT_BASE_URL

    def _build_headers(self) -> Dict[str, str]:
        """Gemini使用x-goog-api-key头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }

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

        # Gemini特有参数
        if "tools" in kwargs:
            body["tools"] = kwargs["tools"]
        if "safety_settings" in kwargs:
            body["safety_settings"] = kwargs["safety_settings"]
        if "generation_config" in kwargs:
            body["generation_config"] = kwargs["generation_config"]

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
