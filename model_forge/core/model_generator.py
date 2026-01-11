"""
Model Generator - 使用火山引擎 Ark API 将图像转换为3D模型
"""

import os
import time
import base64
import zipfile
import tempfile
import requests
from pathlib import Path
from typing import Callable, Union


class ModelGenerator:
    """使用火山引擎 Ark API 生成3D模型"""

    API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
    MODEL_NAME = "doubao-seed3d-1-0-250928"

    # 面数质量说明
    MESH_QUALITY_INFO = {
        "high": "高质量 (~50k面) - 适用于近景展示、大型复杂设备",
        "medium": "中等质量 (~30k面) - 适用于标准展示、一般设备",
        "low": "低质量 (~10k面) - 适用于远景、简单设备、批量渲染"
    }

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def _image_to_base64_url(self, image_path: Path) -> str:
        """将图像文件转换为 base64 data URL"""
        with open(image_path, "rb") as f:
            image_data = f.read()
        base64_data = base64.b64encode(image_data).decode("utf-8")
        return f"data:image/png;base64,{base64_data}"

    def _image_bytes_to_base64_url(self, image_data: bytes) -> str:
        """将图像字节数据转换为 base64 data URL"""
        base64_data = base64.b64encode(image_data).decode("utf-8")
        return f"data:image/png;base64,{base64_data}"

    def create_task(self, image_source: Union[str, bytes, Path],
                    mesh_quality: str = "medium",
                    file_format: str = "glb") -> dict:
        """
        创建图生3D任务

        Args:
            image_source: 图像源（可以是URL、bytes或文件路径）
            mesh_quality: 面数质量 (high/medium/low)
            file_format: 输出格式 (glb/obj/fbx)

        Returns:
            任务创建结果
        """
        # 处理图像源
        if isinstance(image_source, bytes):
            image_url = self._image_bytes_to_base64_url(image_source)
        elif isinstance(image_source, Path) or (isinstance(image_source, str) and os.path.exists(image_source)):
            image_url = self._image_to_base64_url(Path(image_source))
        else:
            image_url = image_source  # 假设是URL

        url = f"{self.API_BASE}/contents/generations/tasks"
        payload = {
            "model": self.MODEL_NAME,
            "content": [
                {
                    "type": "text",
                    "text": f"--meshquality {mesh_quality} --fileformat {file_format}"
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ]
        }

        response = requests.post(url, headers=self.headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()

    def get_task_status(self, task_id: str) -> dict:
        """获取任务状态"""
        url = f"{self.API_BASE}/contents/generations/tasks/{task_id}"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def wait_for_task(self, task_id: str, timeout: int = 900,
                      interval: int = 15,
                      progress_callback: Callable = None) -> dict:
        """
        等待任务完成

        Args:
            task_id: 任务ID
            timeout: 超时时间(秒)
            interval: 轮询间隔(秒)
            progress_callback: 进度回调函数

        Returns:
            最终任务状态
        """
        start_time = time.time()
        last_status = None

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"任务 {task_id} 超时 ({timeout}秒)")

            result = self.get_task_status(task_id)
            status = result.get("status", "unknown")

            if status != last_status:
                last_status = status
                if progress_callback:
                    progress_callback({
                        "task_id": task_id,
                        "status": status,
                        "elapsed": elapsed,
                        "remaining": timeout - elapsed
                    })

            if status == "succeeded":
                return result
            elif status in ["failed", "cancelled"]:
                raise Exception(f"任务失败: {result}")

            time.sleep(interval)

    def download_model(self, task_result: dict, output_dir: Path) -> dict:
        """
        下载3D模型文件

        Args:
            task_result: 任务结果（包含file_url）
            output_dir: 输出目录

        Returns:
            下载结果
        """
        # 获取文件URL
        file_url = task_result.get("content", {}).get("file_url")
        if not file_url:
            raise Exception("任务结果中没有文件URL")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 下载文件
        response = requests.get(file_url, stream=True, timeout=120)
        response.raise_for_status()

        # 保存并解压
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_path = tmp_file.name

        # 解压
        extracted_files = []
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            zip_ref.extractall(output_dir)

            for file_name in file_list:
                extracted_path = output_dir / file_name
                if extracted_path.exists():
                    extracted_files.append({
                        "path": str(extracted_path),
                        "name": file_name,
                        "size_bytes": extracted_path.stat().st_size
                    })

        os.unlink(tmp_path)

        return {
            "output_dir": str(output_dir),
            "files": extracted_files,
            "zip_contents": file_list
        }

    def generate(self, image_source: Union[str, bytes, Path],
                 output_dir: Path,
                 mesh_quality: str = "medium",
                 file_format: str = "glb",
                 progress_callback: Callable = None) -> dict:
        """
        完整的3D模型生成流程

        Args:
            image_source: 图像源
            output_dir: 输出目录
            mesh_quality: 面数质量
            file_format: 输出格式
            progress_callback: 进度回调

        Returns:
            生成结果
        """
        # 创建任务
        if progress_callback:
            progress_callback({"stage": "creating_task", "message": "正在创建3D生成任务..."})

        create_result = self.create_task(image_source, mesh_quality, file_format)
        task_id = create_result.get("id")

        if not task_id:
            raise Exception(f"创建任务失败: {create_result}")

        if progress_callback:
            progress_callback({"stage": "task_created", "task_id": task_id, "message": f"任务已创建: {task_id}"})

        # 等待完成
        if progress_callback:
            progress_callback({"stage": "waiting", "message": "等待3D模型生成..."})

        task_result = self.wait_for_task(
            task_id,
            progress_callback=lambda p: progress_callback({
                "stage": "processing",
                **p
            }) if progress_callback else None
        )

        # 下载模型
        if progress_callback:
            progress_callback({"stage": "downloading", "message": "正在下载3D模型..."})

        download_result = self.download_model(task_result, output_dir)

        if progress_callback:
            progress_callback({"stage": "completed", "message": "3D模型生成完成!"})

        return {
            "task_id": task_id,
            "mesh_quality": mesh_quality,
            "file_format": file_format,
            **download_result
        }
