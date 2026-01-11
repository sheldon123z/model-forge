"""
Model Forge API Routes - FastAPI 路由定义
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from enum import Enum

from ..core import (
    ModelForgePipeline,
    PipelineConfig,
    PipelineStage,
    IndustryDomain,
    RenderStyle,
    PromptConfig
)

# 创建路由器
router = APIRouter(prefix="/api/v1", tags=["model-forge"])

# 全局流水线实例（延迟初始化）
_pipeline: ModelForgePipeline = None

# 任务状态存储
_running_jobs = {}


def get_pipeline() -> ModelForgePipeline:
    """获取流水线实例"""
    global _pipeline
    if _pipeline is None:
        gemini_key = os.environ.get("GEMINI_API_KEY")
        ark_key = os.environ.get("ARK_API_KEY")

        if not gemini_key:
            raise ValueError("未设置 GEMINI_API_KEY 环境变量，请在 .env 文件中配置")
        if not ark_key:
            raise ValueError("未设置 ARK_API_KEY 环境变量，请在 .env 文件中配置")

        config = PipelineConfig(
            gemini_api_key=gemini_key,
            ark_api_key=ark_key,
            output_base_dir=Path(os.environ.get("OUTPUT_DIR", "./output")),
            mesh_quality=os.environ.get("MESH_QUALITY", "medium"),
            file_format=os.environ.get("FILE_FORMAT", "glb")
        )
        _pipeline = ModelForgePipeline(config)
    return _pipeline


# Enums for API
class DomainEnum(str, Enum):
    power_grid = "power_grid"
    manufacturing = "manufacturing"
    architecture = "architecture"
    automotive = "automotive"
    aerospace = "aerospace"
    medical = "medical"
    robotics = "robotics"
    furniture = "furniture"
    electronics = "electronics"
    general = "general"


class StyleEnum(str, Enum):
    photorealistic = "photorealistic"
    industrial = "industrial"
    product = "product"
    technical = "technical"
    artistic = "artistic"
    minimal = "minimal"


# Request/Response Models
class GenerateRequest(BaseModel):
    """生成请求"""
    description: str = Field(..., description="对象描述（支持中英文）", min_length=5)
    equipment_type: Optional[str] = Field(None, description="设备/对象类型")
    voltage_level: Optional[str] = Field(None, description="电压等级（仅电力设备）")
    domain: Optional[DomainEnum] = Field(None, description="行业领域（可选，自动检测）")
    style: Optional[StyleEnum] = Field(StyleEnum.photorealistic, description="渲染风格")
    mesh_quality: Optional[str] = Field("medium", description="面数质量：high/medium/low")
    custom_prompt: Optional[str] = Field(None, description="自定义提示词（跳过AI生成）")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "description": "一台220kV的油浸式电力变压器，带散热翅片",
                    "equipment_type": "变压器",
                    "voltage_level": "220kV",
                    "domain": "power_grid",
                    "style": "industrial",
                    "mesh_quality": "high"
                },
                {
                    "description": "一台6轴工业机器人手臂",
                    "domain": "robotics",
                    "style": "product",
                    "mesh_quality": "high"
                },
                {
                    "description": "现代简约风格的人体工学办公椅",
                    "domain": "furniture",
                    "style": "minimal",
                    "mesh_quality": "medium"
                }
            ]
        }


class GenerateResponse(BaseModel):
    """生成响应"""
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """任务状态响应"""
    job_id: str
    stage: str
    description: str
    prompt: Optional[str] = None
    detected_domain: Optional[str] = None
    style: Optional[str] = None
    image_path: Optional[str] = None
    model_dir: Optional[str] = None
    model_files: Optional[list] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class PromptGenerateRequest(BaseModel):
    """Prompt生成请求"""
    description: str = Field(..., description="对象描述")
    equipment_type: Optional[str] = None
    voltage_level: Optional[str] = None
    domain: Optional[DomainEnum] = None
    style: Optional[StyleEnum] = StyleEnum.photorealistic


class PromptGenerateResponse(BaseModel):
    """Prompt生成响应"""
    prompt: str
    negative_prompt: str
    analysis: Optional[str] = None
    confidence: Optional[str] = None
    detected_domain: str
    style: str


class PromptOptimizeRequest(BaseModel):
    """Prompt优化请求"""
    prompt: str = Field(..., description="要优化的提示词")
    feedback: Optional[str] = Field(None, description="用户反馈")


class PromptOptimizeResponse(BaseModel):
    """Prompt优化响应"""
    original_prompt: str
    optimized_prompt: str
    feedback_applied: bool


class DomainInfo(BaseModel):
    """领域信息"""
    name: str
    value: str
    keywords: List[str]
    materials: List[str]
    colors: List[str]


# 后台任务
async def run_pipeline_task(job_id: str, request: GenerateRequest):
    """后台运行流水线任务"""
    pipeline = get_pipeline()

    # 临时修改配置
    if request.mesh_quality:
        pipeline.config.mesh_quality = request.mesh_quality

    def progress_callback(progress):
        _running_jobs[job_id] = progress

    # 转换领域和风格
    domain = IndustryDomain(request.domain.value) if request.domain else None
    style = RenderStyle(request.style.value) if request.style else None

    # 在线程池中运行同步代码
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: pipeline.run(
            description=request.description,
            equipment_type=request.equipment_type,
            voltage_level=request.voltage_level,
            domain=domain,
            style=style,
            custom_prompt=request.custom_prompt,
            progress_callback=progress_callback
        )
    )


# API 端点
@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    启动完整的3D模型生成流水线

    流程：需求描述 -> AI生成Prompt -> AI生成图像 -> AI生成3D模型

    支持多行业领域，自动检测或手动指定。
    """
    import uuid
    job_id = str(uuid.uuid4())[:8]

    _running_jobs[job_id] = {
        "job_id": job_id,
        "stage": "init",
        "message": "任务已创建，等待处理...",
        "description": request.description
    }

    background_tasks.add_task(run_pipeline_task, job_id, request)

    return GenerateResponse(
        job_id=job_id,
        status="accepted",
        message="任务已创建，正在后台处理"
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """获取任务状态"""
    # 先检查运行中的任务
    if job_id in _running_jobs:
        progress = _running_jobs[job_id]
        return JobStatusResponse(
            job_id=job_id,
            stage=progress.get("stage", "unknown"),
            description=progress.get("description", ""),
            prompt=progress.get("prompt"),
            detected_domain=progress.get("detected_domain"),
            style=progress.get("style"),
            error=progress.get("error")
        )

    # 检查已完成的任务
    pipeline = get_pipeline()
    result = pipeline.get_job_status(job_id)

    if result:
        return JobStatusResponse(**result)

    raise HTTPException(status_code=404, detail=f"任务 {job_id} 不存在")


@router.get("/jobs")
async def list_jobs():
    """列出所有任务"""
    pipeline = get_pipeline()
    return pipeline.list_jobs()


@router.post("/prompt/generate", response_model=PromptGenerateResponse)
async def generate_prompt(request: PromptGenerateRequest):
    """
    单独生成Prompt（不执行后续流程）

    使用高级Prompt工程技术：
    - Chain-of-Thought 链式思维
    - Few-shot Learning 少样本学习
    - Self-Verification 自我验证
    """
    pipeline = get_pipeline()

    domain = IndustryDomain(request.domain.value) if request.domain else None
    style = RenderStyle(request.style.value) if request.style else None

    result = pipeline.prompt_generator.generate(
        description=request.description,
        equipment_type=request.equipment_type,
        voltage_level=request.voltage_level,
        domain=domain,
        style=style
    )

    return PromptGenerateResponse(
        prompt=result["prompt"],
        negative_prompt=result["negative_prompt"],
        analysis=result.get("analysis"),
        confidence=result.get("confidence"),
        detected_domain=result["detected_domain"],
        style=result["style"]
    )


@router.post("/prompt/optimize", response_model=PromptOptimizeResponse)
async def optimize_prompt(request: PromptOptimizeRequest):
    """优化已有的提示词"""
    pipeline = get_pipeline()
    result = pipeline.prompt_generator.optimize_prompt(
        prompt=request.prompt,
        feedback=request.feedback
    )
    return PromptOptimizeResponse(**result)


@router.get("/domains", response_model=List[DomainInfo])
async def list_domains():
    """列出所有支持的行业领域"""
    from ..core.prompt_generator import PromptGenerator

    domains = []
    for domain, knowledge in PromptGenerator.DOMAIN_KNOWLEDGE.items():
        domains.append(DomainInfo(
            name=domain.name,
            value=domain.value,
            keywords=knowledge["keywords"][:5],
            materials=knowledge["materials"][:5],
            colors=knowledge["colors"][:5]
        ))
    return domains


@router.get("/styles")
async def list_styles():
    """列出所有支持的渲染风格"""
    from ..core.prompt_generator import PromptGenerator

    return [
        {"name": style.name, "value": style.value, "description": desc}
        for style, desc in PromptGenerator.STYLE_TEMPLATES.items()
    ]


@router.get("/jobs/{job_id}/image")
async def get_job_image(job_id: str):
    """获取任务生成的图像"""
    pipeline = get_pipeline()
    job_dir = pipeline.config.output_base_dir / job_id
    image_path = job_dir / "image.png"

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="图像不存在")

    return FileResponse(image_path, media_type="image/png")


@router.get("/jobs/{job_id}/model/{filename}")
async def get_job_model(job_id: str, filename: str):
    """获取任务生成的3D模型文件"""
    pipeline = get_pipeline()
    job_dir = pipeline.config.output_base_dir / job_id / "model"

    # 查找文件
    for file_path in job_dir.rglob(filename):
        if file_path.is_file():
            media_type = "model/gltf-binary" if filename.endswith(".glb") else "application/octet-stream"
            return FileResponse(file_path, media_type=media_type)

    raise HTTPException(status_code=404, detail="模型文件不存在")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "model-forge", "version": "1.1.0"}
