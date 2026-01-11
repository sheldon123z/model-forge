"""
DeepSeek AI 服务商
官方文档: https://api-docs.deepseek.com/
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


class DeepSeekProvider(BaseProvider):
    """DeepSeek AI 服务商"""

    provider_type = ProviderType.DEEPSEEK
    display_name = "DeepSeek"
    website = "https://www.deepseek.com"
    capabilities = [
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.CODE_GENERATION,
        ProviderCapability.REASONING,
        ProviderCapability.FUNCTION_CALLING,
        ProviderCapability.LONG_CONTEXT,
    ]

    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"

    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                name="deepseek-chat",
                display_name="DeepSeek V3",
                description="DeepSeek-V3 通用对话模型，685B参数MoE架构",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CODE_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=8192,
                context_length=128000,
                price_input=0.2,  # 0.002元/千tokens
                price_output=0.8,  # 0.008元/千tokens
            ),
            ModelInfo(
                name="deepseek-reasoner",
                display_name="DeepSeek R1",
                description="DeepSeek-R1 深度推理模型，支持思维链输出",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.REASONING,
                ],
                max_tokens=64000,
                context_length=128000,
                price_input=0.4,
                price_output=1.6,
            ),
            ModelInfo(
                name="deepseek-coder",
                display_name="DeepSeek Coder",
                description="专注于代码生成和理解的模型",
                capabilities=[
                    ProviderCapability.CODE_GENERATION,
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=8192,
                context_length=128000,
                price_input=0.2,
                price_output=0.8,
            ),
        ]

    def _get_base_url(self) -> str:
        return self.config.base_url or self.DEFAULT_BASE_URL

    def _build_request_body(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        stream: bool,
        **kwargs
    ) -> Dict[str, Any]:
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        body = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            "stream": stream,
        }

        if max_tokens:
            body["max_tokens"] = max_tokens

        # 添加额外参数
        for key in ["top_p", "frequency_penalty", "presence_penalty", "tools"]:
            if key in kwargs:
                body[key] = kwargs[key]

        return body

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
        body = self._build_request_body(
            messages, model, temperature, max_tokens, stream, **kwargs
        )

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
        body = self._build_request_body(
            messages, model, temperature, max_tokens, stream, **kwargs
        )

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
        body = self._build_request_body(
            messages, model, temperature, max_tokens, True, **kwargs
        )

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
