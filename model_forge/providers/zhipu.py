"""
智谱AI (GLM) 服务商
官方文档: https://open.bigmodel.cn/dev/api
"""

from typing import Optional, List, Dict, Any, AsyncIterator
import json
import time
import jwt
from .base import (
    BaseProvider,
    ProviderType,
    ProviderCapability,
    ProviderConfig,
    ModelInfo,
    ChatMessage,
    ChatResponse,
)


class ZhipuProvider(BaseProvider):
    """智谱AI 服务商"""

    provider_type = ProviderType.ZHIPU
    display_name = "智谱AI (GLM)"
    website = "https://www.bigmodel.cn"
    capabilities = [
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.CODE_GENERATION,
        ProviderCapability.IMAGE_GENERATION,
        ProviderCapability.IMAGE_UNDERSTANDING,
        ProviderCapability.FUNCTION_CALLING,
        ProviderCapability.EMBEDDING,
    ]

    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                name="glm-4-flash",
                display_name="GLM-4 Flash (免费)",
                description="永久免费模型，支持多轮对话、内容生成、工具调用",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=4096,
                context_length=128000,
                price_input=0,
                price_output=0,
            ),
            ModelInfo(
                name="glm-4-plus",
                display_name="GLM-4 Plus",
                description="高性能版本，适合复杂任务",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=8192,
                context_length=128000,
                price_input=50.0,
                price_output=50.0,
            ),
            ModelInfo(
                name="glm-4-0520",
                display_name="GLM-4 0520",
                description="最新版GLM-4模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CODE_GENERATION,
                ],
                max_tokens=8192,
                context_length=128000,
                price_input=100.0,
                price_output=100.0,
            ),
            ModelInfo(
                name="glm-4-long",
                display_name="GLM-4 Long",
                description="超长上下文版本，支持1M tokens",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=8192,
                context_length=1000000,
                price_input=1.0,
                price_output=1.0,
            ),
            ModelInfo(
                name="glm-4v-plus",
                display_name="GLM-4V Plus",
                description="多模态视觉理解模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.IMAGE_UNDERSTANDING,
                ],
                max_tokens=4096,
                context_length=8192,
                price_input=15.0,
                price_output=15.0,
                supports_vision=True,
            ),
            ModelInfo(
                name="glm-4.6",
                display_name="GLM-4.6 (ARC)",
                description="355B参数MoE架构，融合智能体、推理、编码能力",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CODE_GENERATION,
                    ProviderCapability.REASONING,
                ],
                max_tokens=16384,
                context_length=200000,
                price_input=4.0,
                price_output=16.0,
            ),
            ModelInfo(
                name="codegeex-4",
                display_name="CodeGeeX 4",
                description="专业代码生成模型",
                capabilities=[
                    ProviderCapability.CODE_GENERATION,
                ],
                max_tokens=8192,
                context_length=128000,
                price_input=0.1,
                price_output=0.1,
            ),
            ModelInfo(
                name="cogview-3-plus",
                display_name="CogView-3 Plus",
                description="图像生成模型",
                capabilities=[
                    ProviderCapability.IMAGE_GENERATION,
                ],
                max_tokens=1,
                context_length=1,
                price_input=0,
                price_output=0,
            ),
        ]

    def _get_base_url(self) -> str:
        return self.config.base_url or self.DEFAULT_BASE_URL

    def _generate_token(self) -> str:
        """生成JWT Token (智谱AI特有的认证方式)"""
        api_key = self.config.api_key
        try:
            id, secret = api_key.split(".")
        except Exception:
            # 如果API Key格式不对，直接使用Bearer方式
            return api_key

        payload = {
            "api_key": id,
            "exp": int(time.time()) + 3600,
            "timestamp": int(time.time() * 1000),
        }

        return jwt.encode(
            payload,
            secret,
            algorithm="HS256",
            headers={"alg": "HS256", "sign_type": "SIGN"}
        )

    def _build_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._generate_token()}"
        }

    def _format_messages(self, messages: List[ChatMessage]) -> List[Dict]:
        """格式化消息"""
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

        # 智谱特有参数
        if "tools" in kwargs:
            body["tools"] = kwargs["tools"]
        if "top_p" in kwargs:
            body["top_p"] = kwargs["top_p"]
        if "do_sample" in kwargs:
            body["do_sample"] = kwargs["do_sample"]

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
