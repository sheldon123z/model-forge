"""
Model Forge Pipeline - 完整的需求->Prompt->图像->3D模型流水线

支持多行业领域的通用3D模型生成
"""

import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

from .prompt_generator import PromptGenerator, PromptConfig, IndustryDomain, RenderStyle
from .image_generator import ImageGenerator
from .model_generator import ModelGenerator


class PipelineStage(str, Enum):
    """流水线阶段"""
    INIT = "init"
    PROMPT_GENERATION = "prompt_generation"
    IMAGE_GENERATION = "image_generation"
    MODEL_GENERATION = "model_generation"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineConfig:
    """流水线配置"""
    gemini_api_key: str
    ark_api_key: str
    output_base_dir: Path = None
    mesh_quality: str = "medium"
    file_format: str = "glb"
    generate_multiview: bool = False
    # Prompt 工程配置
    use_few_shot: bool = True
    use_chain_of_thought: bool = True
    use_self_verification: bool = True
    optimize_iterations: int = 1

    def __post_init__(self):
        if self.output_base_dir is None:
            self.output_base_dir = Path("./output")
        elif isinstance(self.output_base_dir, str):
            self.output_base_dir = Path(self.output_base_dir)


@dataclass
class PipelineResult:
    """流水线结果"""
    job_id: str
    stage: PipelineStage
    description: str
    folder_name: Optional[str] = None
    display_name: Optional[str] = None
    prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    analysis: Optional[str] = None
    confidence: Optional[str] = None
    detected_domain: Optional[str] = None
    style: Optional[str] = None
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    model_dir: Optional[str] = None
    model_files: Optional[list] = None
    error: Optional[str] = None
    created_at: str = None
    completed_at: str = None

    def to_dict(self):
        result = asdict(self)
        result["stage"] = self.stage.value if isinstance(self.stage, PipelineStage) else self.stage
        return result


class ModelForgePipeline:
    """
    Model Forge 完整流水线

    流程：需求描述 -> AI生成Prompt -> AI生成图像 -> AI生成3D模型

    支持多行业领域：电力系统、制造业、建筑、汽车、航空航天、医疗、机器人、家具、电子等
    """

    def __init__(self, config: PipelineConfig):
        self.config = config

        # 创建 Prompt 配置
        prompt_config = PromptConfig(
            use_few_shot=config.use_few_shot,
            use_chain_of_thought=config.use_chain_of_thought,
            use_self_verification=config.use_self_verification,
            optimize_iterations=config.optimize_iterations
        )

        self.prompt_generator = PromptGenerator(config.gemini_api_key, prompt_config)
        self.image_generator = ImageGenerator(config.gemini_api_key)
        self.model_generator = ModelGenerator(config.ark_api_key)

        # 确保输出目录存在
        self.config.output_base_dir = Path(config.output_base_dir)
        self.config.output_base_dir.mkdir(parents=True, exist_ok=True)

    def run(self, description: str,
            equipment_type: str = None,
            voltage_level: str = None,
            domain: IndustryDomain = None,
            style: RenderStyle = None,
            custom_prompt: str = None,
            progress_callback: Callable = None) -> PipelineResult:
        """
        运行完整流水线

        Args:
            description: 对象描述/需求（支持中英文）
            equipment_type: 设备/对象类型（可选）
            voltage_level: 电压等级（仅电力设备，可选）
            domain: 行业领域（可选，自动检测）
            style: 渲染风格（可选）
            custom_prompt: 自定义提示词（跳过prompt生成阶段）
            progress_callback: 进度回调函数

        Returns:
            流水线结果
        """
        # 初始化（使用临时 UUID，后续根据 LLM 生成的 folder_name 重命名）
        temp_job_id = str(uuid.uuid4())[:8]
        job_dir = self.config.output_base_dir / temp_job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        result = PipelineResult(
            job_id=temp_job_id,
            stage=PipelineStage.INIT,
            description=description,
            display_name=description[:50],  # 截取前50字符作为显示名
            created_at=datetime.now().isoformat()
        )

        def update_progress(stage: PipelineStage, message: str, **kwargs):
            result.stage = stage
            if progress_callback:
                progress_callback({
                    "job_id": job_id,
                    "stage": stage.value,
                    "message": message,
                    "description": description,
                    "detected_domain": result.detected_domain,
                    "style": result.style,
                    **kwargs
                })

        try:
            # 阶段1: 生成Prompt
            if custom_prompt:
                result.prompt = custom_prompt
                result.negative_prompt = "cartoon, anime, stylized, fantasy, damaged, rusty, low quality, blurry"
                result.detected_domain = domain.value if domain else "general"
                result.style = style.value if style else "photorealistic"
                update_progress(PipelineStage.PROMPT_GENERATION, "使用自定义提示词")
            else:
                update_progress(PipelineStage.PROMPT_GENERATION, "正在使用高级Prompt工程生成提示词...")
                prompt_result = self.prompt_generator.generate(
                    description=description,
                    equipment_type=equipment_type,
                    voltage_level=voltage_level,
                    domain=domain,
                    style=style
                )
                result.prompt = prompt_result["prompt"]
                result.negative_prompt = prompt_result["negative_prompt"]
                result.analysis = prompt_result.get("analysis")
                result.confidence = prompt_result.get("confidence")
                result.detected_domain = prompt_result["detected_domain"]
                result.style = prompt_result["style"]

                # 获取 LLM 生成的 folder_name
                llm_folder_name = prompt_result.get("folder_name", "")
                if llm_folder_name:
                    result.folder_name = llm_folder_name
                    # 检查是否存在冲突，如有则添加短 UUID 后缀
                    target_dir = self.config.output_base_dir / llm_folder_name
                    if target_dir.exists():
                        llm_folder_name = f"{llm_folder_name}_{temp_job_id[:4]}"
                        target_dir = self.config.output_base_dir / llm_folder_name
                    result.folder_name = llm_folder_name

                    # 重命名目录
                    job_dir.rename(target_dir)
                    job_dir = target_dir
                    result.job_id = llm_folder_name

                update_progress(
                    PipelineStage.PROMPT_GENERATION,
                    f"提示词生成完成 (领域: {result.detected_domain}, 置信度: {result.confidence})",
                    prompt=result.prompt
                )

            # 保存prompt
            prompt_file = job_dir / "prompt.json"
            with open(prompt_file, "w", encoding="utf-8") as f:
                json.dump({
                    "description": description,
                    "prompt": result.prompt,
                    "negative_prompt": result.negative_prompt,
                    "analysis": result.analysis,
                    "confidence": result.confidence,
                    "detected_domain": result.detected_domain,
                    "style": result.style
                }, f, ensure_ascii=False, indent=2)

            # 保存 metadata.json
            metadata_file = job_dir / "metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump({
                    "display_name": result.display_name,
                    "folder_name": result.folder_name or result.job_id,
                    "description": description,
                    "equipment_type": equipment_type,
                    "voltage_level": voltage_level,
                    "domain": result.detected_domain,
                    "style": result.style,
                    "created_at": result.created_at
                }, f, ensure_ascii=False, indent=2)

            # 阶段2: 生成图像
            update_progress(PipelineStage.IMAGE_GENERATION, "正在生成图像...")
            image_path = job_dir / "image.png"
            image_result = self.image_generator.generate(
                prompt=result.prompt,
                negative_prompt=result.negative_prompt,
                output_path=image_path
            )
            result.image_path = str(image_path)
            result.image_base64 = image_result["image_base64"]
            update_progress(PipelineStage.IMAGE_GENERATION, "图像生成完成", image_size=image_result["size_bytes"])

            # 阶段3: 生成3D模型
            update_progress(PipelineStage.MODEL_GENERATION, "正在生成3D模型...")
            model_dir = job_dir / "model"
            model_result = self.model_generator.generate(
                image_source=image_result["image_data"],
                output_dir=model_dir,
                mesh_quality=self.config.mesh_quality,
                file_format=self.config.file_format,
                progress_callback=lambda p: update_progress(
                    PipelineStage.MODEL_GENERATION,
                    p.get("message", "处理中..."),
                    **p
                )
            )
            result.model_dir = str(model_dir)
            result.model_files = model_result["files"]

            # 完成
            result.stage = PipelineStage.COMPLETED
            result.completed_at = datetime.now().isoformat()
            update_progress(PipelineStage.COMPLETED, "流水线完成!")

            # 保存结果
            result_file = job_dir / "result.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

        except Exception as e:
            result.stage = PipelineStage.FAILED
            result.error = str(e)
            result.completed_at = datetime.now().isoformat()
            update_progress(PipelineStage.FAILED, f"流水线失败: {e}", error=str(e))

            # 保存错误结果
            result_file = job_dir / "result.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

        return result

    def get_job_status(self, job_id: str) -> dict:
        """获取任务状态"""
        job_dir = self.config.output_base_dir / job_id
        result_file = job_dir / "result.json"

        if result_file.exists():
            with open(result_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def list_jobs(self) -> list:
        """列出所有任务"""
        jobs = []
        if self.config.output_base_dir.exists():
            for job_dir in self.config.output_base_dir.iterdir():
                if job_dir.is_dir():
                    result_file = job_dir / "result.json"
                    if result_file.exists():
                        with open(result_file, "r", encoding="utf-8") as f:
                            jobs.append(json.load(f))
        return sorted(jobs, key=lambda x: x.get("created_at", ""), reverse=True)
