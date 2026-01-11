"""
Image Generator - 使用 Gemini API 生成设备图像
"""

import base64
from pathlib import Path
from google import genai
from google.genai import types


class ImageGenerator:
    """使用 Gemini 生成高质量设备图像"""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash-exp-image-generation"

    def generate(self, prompt: str, negative_prompt: str = None,
                 output_path: Path = None) -> dict:
        """
        根据提示词生成图像

        Args:
            prompt: 图像生成提示词
            negative_prompt: 负面提示词
            output_path: 输出路径（可选）

        Returns:
            包含图像数据和路径的字典
        """
        # 构建完整提示词
        full_prompt = prompt
        if negative_prompt:
            full_prompt += f"\n\nNegative: {negative_prompt}"

        # 调用 Gemini API
        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            )
        )

        # 提取图像数据
        image_data = None
        text_response = None

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_data = part.inline_data.data
                    if isinstance(image_data, str):
                        image_data = base64.b64decode(image_data)
                if hasattr(part, 'text') and part.text:
                    text_response = part.text

        if not image_data:
            raise Exception("未能生成图像")

        # 保存图像
        saved_path = None
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_data)
            saved_path = str(output_path)

        return {
            "image_data": image_data,
            "image_base64": base64.b64encode(image_data).decode("utf-8"),
            "saved_path": saved_path,
            "text_response": text_response,
            "size_bytes": len(image_data)
        }

    def generate_multiview(self, prompt: str, negative_prompt: str = None,
                           output_dir: Path = None) -> list:
        """
        生成多视角图像（用于3D重建）

        Args:
            prompt: 基础提示词
            negative_prompt: 负面提示词
            output_dir: 输出目录

        Returns:
            多个视角的图像结果列表
        """
        views = [
            {"name": "front", "suffix": "front view, straight on, symmetrical"},
            {"name": "quarter_left", "suffix": "three-quarter front-left view, 45 degrees"},
            {"name": "left", "suffix": "left side view, 90 degrees"},
            {"name": "quarter_right", "suffix": "three-quarter front-right view, 45 degrees"},
        ]

        results = []
        for view in views:
            view_prompt = f"{prompt}\n\nCamera angle: {view['suffix']}"

            output_path = None
            if output_dir:
                output_path = Path(output_dir) / f"{view['name']}.png"

            try:
                result = self.generate(
                    prompt=view_prompt,
                    negative_prompt=negative_prompt,
                    output_path=output_path
                )
                result["view_name"] = view["name"]
                results.append(result)
            except Exception as e:
                results.append({
                    "view_name": view["name"],
                    "error": str(e)
                })

        return results
