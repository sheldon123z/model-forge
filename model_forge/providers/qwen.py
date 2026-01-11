"""
通义千问 (Qwen) 服务商 - 阿里云百炼
官方文档: https://help.aliyun.com/zh/model-studio/qwen-api-reference
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


class QwenProvider(BaseProvider):
    """通义千问/阿里云百炼 服务商"""

    provider_type = ProviderType.QWEN
    display_name = "通义千问 (Qwen)"
    website = "https://tongyi.aliyun.com"
    capabilities = [
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.CODE_GENERATION,
        ProviderCapability.IMAGE_GENERATION,
        ProviderCapability.IMAGE_UNDERSTANDING,
        ProviderCapability.FUNCTION_CALLING,
        ProviderCapability.LONG_CONTEXT,
        ProviderCapability.REASONING,
        ProviderCapability.EMBEDDING,
    ]

    # OpenAI兼容模式
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                name="qwen-turbo",
                display_name="通义千问 Turbo",
                description="性价比版本，响应快",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                ],
                max_tokens=8192,
                context_length=131072,
                price_input=0.3,
                price_output=0.6,
            ),
            ModelInfo(
                name="qwen-plus",
                display_name="通义千问 Plus",
                description="能力均衡，支持思考模式",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                    ProviderCapability.REASONING,
                ],
                max_tokens=32768,
                context_length=131072,
                price_input=0.8,
                price_output=2.0,
            ),
            ModelInfo(
                name="qwen-max",
                display_name="通义千问 Max",
                description="最强版本，适合复杂任务",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                    ProviderCapability.REASONING,
                ],
                max_tokens=32768,
                context_length=32768,
                price_input=20.0,
                price_output=60.0,
            ),
            ModelInfo(
                name="qwen-long",
                display_name="通义千问 Long",
                description="超长上下文版本，支持1M tokens",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=8192,
                context_length=1000000,
                price_input=0.5,
                price_output=2.0,
            ),
            ModelInfo(
                name="qwen-vl-plus",
                display_name="通义千问 VL Plus",
                description="视觉理解模型，支持图片理解",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                ],
                max_tokens=8192,
                context_length=32768,
                price_input=8.0,
                price_output=8.0,
                supports_vision=True,
            ),
            ModelInfo(
                name="qwen-vl-max",
                display_name="通义千问 VL Max",
                description="最强视觉理解模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                ],
                max_tokens=8192,
                context_length=32768,
                price_input=20.0,
                price_output=20.0,
                supports_vision=True,
            ),
            ModelInfo(
                name="qwen3-coder-plus",
                display_name="Qwen3 Coder Plus",
                description="专业代码生成模型，擅长工具调用",
                capabilities=[
                    ProviderCapability.CODE_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=16384,
                context_length=131072,
                price_input=2.0,
                price_output=8.0,
            ),
            ModelInfo(
                name="qwen-math-plus",
                display_name="通义千问 Math Plus",
                description="数学推理模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.REASONING,
                ],
                max_tokens=8192,
                context_length=32768,
                price_input=2.0,
                price_output=4.0,
            ),
        ]

    def _get_base_url(self) -> str:
        return self.config.base_url or self.DEFAULT_BASE_URL

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

        # 通义特有参数
        if "enable_thinking" in kwargs:
            body["enable_thinking"] = kwargs["enable_thinking"]
        if "tools" in kwargs:
            body["tools"] = kwargs["tools"]
        if "top_p" in kwargs:
            body["top_p"] = kwargs["top_p"]
        if "seed" in kwargs:
            body["seed"] = kwargs["seed"]
        if "result_format" in kwargs:
            body["result_format"] = kwargs["result_format"]

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
