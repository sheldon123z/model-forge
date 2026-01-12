"""
豆包 (Doubao/ByteDance) 服务商 - 火山引擎
官方文档: https://www.volcengine.com/docs/82379
"""

from typing import Optional, List, Dict, Any, AsyncIterator
import json
import time
import requests
from .base import (
    BaseProvider,
    ProviderType,
    ProviderCapability,
    ProviderConfig,
    ModelInfo,
    ChatMessage,
    ChatResponse,
)


class DoubaoProvider(BaseProvider):
    """豆包/火山引擎 服务商"""

    provider_type = ProviderType.DOUBAO
    display_name = "豆包 (Doubao)"
    website = "https://www.volcengine.com/product/doubao"
    capabilities = [
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.IMAGE_GENERATION,
        ProviderCapability.MODEL_3D_GENERATION,
        ProviderCapability.CODE_GENERATION,
        ProviderCapability.FUNCTION_CALLING,
        ProviderCapability.LONG_CONTEXT,
    ]

    DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

    # 3D模型生成参数配置
    MODEL_3D_CONFIG = {
        "model_name": "doubao-seed3d-1-0-250928",
        "subdivision_levels": {
            "low": 30000,      # 低精度 ~30k面
            "medium": 100000,  # 中等精度 ~100k面
            "high": 200000,    # 高精度 ~200k面
        },
        "file_formats": ["glb", "obj", "usd", "usdz"],
        "default_format": "glb",
        "default_quality": "medium",
        "price_per_model": 2.4,  # 元/个 (固定30000 tokens)
    }

    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                name="doubao-1.5-pro-32k",
                display_name="豆包 1.5 Pro 32K",
                description="豆包大模型1.5版本，支持32K上下文",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.FUNCTION_CALLING,
                ],
                max_tokens=8192,
                context_length=32000,
                price_input=0.8,
                price_output=2.0,
            ),
            ModelInfo(
                name="doubao-1.5-pro-256k",
                display_name="豆包 1.5 Pro 256K",
                description="豆包大模型1.5版本，支持256K超长上下文",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.LONG_CONTEXT,
                ],
                max_tokens=8192,
                context_length=256000,
                price_input=5.0,
                price_output=9.0,
            ),
            ModelInfo(
                name="doubao-seed-1.6",
                display_name="豆包 Seed 1.6",
                description="豆包最新Seed系列模型",
                capabilities=[
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.CODE_GENERATION,
                ],
                max_tokens=16384,
                context_length=128000,
                price_input=1.0,
                price_output=4.0,
            ),
            ModelInfo(
                name="doubao-seed-code",
                display_name="豆包 Seed Code",
                description="专注于代码生成的模型",
                capabilities=[
                    ProviderCapability.CODE_GENERATION,
                ],
                max_tokens=16384,
                context_length=128000,
                price_input=1.0,
                price_output=4.0,
            ),
            ModelInfo(
                name="doubao-seed3d-1-0-250928",
                display_name="豆包 Seed 3D",
                description="3D模型生成模型，支持图像到3D转换",
                capabilities=[
                    ProviderCapability.MODEL_3D_GENERATION,
                ],
                max_tokens=30000,  # 固定token消耗
                context_length=1,
                price_input=0,
                price_output=80.0,  # 2.4元/个，折算为百万tokens
            ),
            ModelInfo(
                name="doubao-seedream-4.0",
                display_name="豆包 Seedream 4.0",
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

    # ========== 3D模型生成相关方法 ==========

    def create_3d_task(
        self,
        image_source: str,
        subdivision_level: str = "medium",
        file_format: str = "glb",
    ) -> Dict[str, Any]:
        """
        创建3D模型生成任务

        Args:
            image_source: 图像源 (base64 data URL 或 URL)
            subdivision_level: 精度级别 (low/medium/high)
                - low: ~30,000 面
                - medium: ~100,000 面
                - high: ~200,000 面
            file_format: 输出格式 (glb/obj/usd/usdz)

        Returns:
            任务信息
        """
        url = f"{self._get_base_url()}/contents/generations/tasks"

        # 转换精度级别到面数
        mesh_faces = self.MODEL_3D_CONFIG["subdivision_levels"].get(
            subdivision_level,
            self.MODEL_3D_CONFIG["subdivision_levels"]["medium"]
        )

        payload = {
            "model": self.MODEL_3D_CONFIG["model_name"],
            "content": [
                {
                    "type": "text",
                    "text": f"--subdivisionlevel {mesh_faces} --fileformat {file_format}"
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_source}
                }
            ]
        }

        response = self.client.post(
            url,
            headers=self._build_headers(),
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_3d_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取3D生成任务状态"""
        url = f"{self._get_base_url()}/contents/generations/tasks/{task_id}"
        response = self.client.get(url, headers=self._build_headers())
        response.raise_for_status()
        return response.json()

    def list_3d_tasks(
        self,
        page_num: int = 1,
        page_size: int = 10,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        列出3D生成任务

        Args:
            page_num: 页码
            page_size: 每页数量
            status: 过滤状态 (pending/running/succeeded/failed/cancelled)
        """
        url = f"{self._get_base_url()}/contents/generations/tasks"
        params = {
            "page_num": page_num,
            "page_size": page_size,
        }
        if status:
            params["status"] = status

        response = self.client.get(
            url,
            headers=self._build_headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()

    def cancel_3d_task(self, task_id: str) -> Dict[str, Any]:
        """取消3D生成任务"""
        url = f"{self._get_base_url()}/contents/generations/tasks/{task_id}/cancel"
        response = self.client.post(url, headers=self._build_headers())
        response.raise_for_status()
        return response.json()

    def wait_for_3d_task(
        self,
        task_id: str,
        timeout: int = 900,
        interval: int = 15,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        等待3D生成任务完成

        Args:
            task_id: 任务ID
            timeout: 超时时间(秒)
            interval: 轮询间隔(秒)
            progress_callback: 进度回调函数

        Returns:
            任务结果
        """
        start_time = time.time()
        last_status = None

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"任务 {task_id} 超时 ({timeout}秒)")

            result = self.get_3d_task_status(task_id)
            status = result.get("status", "unknown")

            if status != last_status:
                last_status = status
                if progress_callback:
                    progress_callback({
                        "task_id": task_id,
                        "status": status,
                        "elapsed": elapsed,
                        "remaining": timeout - elapsed,
                        "progress": result.get("progress", 0)
                    })

            if status == "succeeded":
                return result
            elif status in ["failed", "cancelled"]:
                raise Exception(f"任务失败: {result}")

            time.sleep(interval)

    @classmethod
    def get_3d_config(cls) -> Dict[str, Any]:
        """获取3D模型生成配置信息"""
        return {
            "model_name": cls.MODEL_3D_CONFIG["model_name"],
            "subdivision_levels": [
                {
                    "key": "low",
                    "label": "低精度",
                    "faces": cls.MODEL_3D_CONFIG["subdivision_levels"]["low"],
                    "description": "适用于预览、远景展示，约30,000面"
                },
                {
                    "key": "medium",
                    "label": "中等精度",
                    "faces": cls.MODEL_3D_CONFIG["subdivision_levels"]["medium"],
                    "description": "适用于标准展示，约100,000面"
                },
                {
                    "key": "high",
                    "label": "高精度",
                    "faces": cls.MODEL_3D_CONFIG["subdivision_levels"]["high"],
                    "description": "适用于近景、细节展示，约200,000面"
                },
            ],
            "file_formats": [
                {"key": "glb", "label": "GLB", "description": "二进制GLTF格式，体积小，加载快"},
                {"key": "obj", "label": "OBJ", "description": "通用3D格式，兼容性好"},
                {"key": "usd", "label": "USD", "description": "Pixar通用场景描述格式"},
                {"key": "usdz", "label": "USDZ", "description": "USD压缩格式，适合AR"},
            ],
            "price_per_model": cls.MODEL_3D_CONFIG["price_per_model"],
            "estimated_time": "3-8分钟",
        }
