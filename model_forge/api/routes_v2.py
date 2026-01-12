"""
Model Forge API V2 Routes - 扩展API路由

新增功能：
- 多服务商管理
- 联想批量生成
- 批量并行生成
- 3D模型库管理
- 增强的豆包3D参数配置
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from enum import Enum

from ..providers import (
    ProviderType,
    ProviderCapability,
    ProviderManager,
    DoubaoProvider,
)
from ..core import (
    AssociationGenerator,
    AssociationMode,
    CategorySuggester,
    BatchGenerator,
    BatchConfig,
    BatchJobManager,
    ModelForgePipeline,
    PipelineConfig,
)

# 创建路由器
router = APIRouter(prefix="/api/v2", tags=["model-forge-v2"])

# 全局管理器
_provider_manager: Optional[ProviderManager] = None
_batch_manager: Optional[BatchJobManager] = None


def get_provider_manager() -> ProviderManager:
    """获取服务商管理器"""
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = ProviderManager()
        _init_providers()
    return _provider_manager


def get_batch_manager() -> BatchJobManager:
    """获取批量任务管理器"""
    global _batch_manager
    if _batch_manager is None:
        output_dir = os.environ.get("OUTPUT_DIR", "./output")
        _batch_manager = BatchJobManager(storage_dir=f"{output_dir}/batch")
    return _batch_manager


def _init_providers():
    """从环境变量初始化服务商"""
    env_mappings = {
        ProviderType.DEEPSEEK: "DEEPSEEK_API_KEY",
        ProviderType.DOUBAO: "ARK_API_KEY",
        ProviderType.KIMI: "KIMI_API_KEY",
        ProviderType.MINIMAX: "MINIMAX_API_KEY",
        ProviderType.ZHIPU: "ZHIPU_API_KEY",
        ProviderType.BAICHUAN: "BAICHUAN_API_KEY",
        ProviderType.SPARK: "SPARK_API_KEY",
        ProviderType.QWEN: "QWEN_API_KEY",
        ProviderType.YI: "YI_API_KEY",
        ProviderType.OPENROUTER: "OPENROUTER_API_KEY",
        ProviderType.GEMINI: "GEMINI_API_KEY",
    }

    for provider_type, env_key in env_mappings.items():
        api_key = os.environ.get(env_key)
        if api_key:
            _provider_manager.configure(provider_type, api_key)


# ==================== 服务商管理API ====================

class ProviderInfoResponse(BaseModel):
    """服务商信息响应"""
    provider_type: str
    display_name: str
    website: str
    capabilities: List[str]
    description: str
    api_doc_url: str
    is_configured: bool
    models: List[Dict[str, Any]]


class ProviderConfigRequest(BaseModel):
    """服务商配置请求"""
    provider_type: str
    api_key: str
    base_url: Optional[str] = None
    model: Optional[str] = None


@router.get("/providers")
async def list_providers() -> List[ProviderInfoResponse]:
    """列出所有支持的AI服务商"""
    manager = get_provider_manager()
    providers = ProviderManager.list_providers()

    result = []
    for p in providers:
        result.append(ProviderInfoResponse(
            provider_type=p.provider_type.value,
            display_name=p.display_name,
            website=p.website,
            capabilities=[c.value for c in p.capabilities],
            description=p.description,
            api_doc_url=p.api_doc_url,
            is_configured=p.provider_type in manager._configs,
            models=[
                {
                    "name": m.name,
                    "display_name": m.display_name,
                    "description": m.description,
                    "max_tokens": m.max_tokens,
                    "context_length": m.context_length,
                    "price_input": m.price_input,
                    "price_output": m.price_output,
                    "supports_vision": m.supports_vision,
                }
                for m in p.models
            ]
        ))

    return result


@router.get("/providers/{provider_type}")
async def get_provider(provider_type: str) -> ProviderInfoResponse:
    """获取单个服务商详情"""
    try:
        pt = ProviderType(provider_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"未知的服务商: {provider_type}")

    info = ProviderManager.get_provider_info(pt)
    if not info:
        raise HTTPException(status_code=404, detail=f"服务商信息不存在: {provider_type}")

    manager = get_provider_manager()
    return ProviderInfoResponse(
        provider_type=info.provider_type.value,
        display_name=info.display_name,
        website=info.website,
        capabilities=[c.value for c in info.capabilities],
        description=info.description,
        api_doc_url=info.api_doc_url,
        is_configured=info.provider_type in manager._configs,
        models=[
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "max_tokens": m.max_tokens,
                "context_length": m.context_length,
                "price_input": m.price_input,
                "price_output": m.price_output,
                "supports_vision": m.supports_vision,
            }
            for m in info.models
        ]
    )


@router.post("/providers/configure")
async def configure_provider(request: ProviderConfigRequest):
    """配置服务商API密钥"""
    try:
        pt = ProviderType(request.provider_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"未知的服务商: {request.provider_type}")

    manager = get_provider_manager()
    manager.configure(
        pt,
        request.api_key,
        base_url=request.base_url,
        model=request.model
    )

    return {"status": "success", "message": f"服务商 {request.provider_type} 配置成功"}


@router.get("/providers/by-capability/{capability}")
async def list_providers_by_capability(capability: str) -> List[ProviderInfoResponse]:
    """按能力筛选服务商"""
    try:
        cap = ProviderCapability(capability)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"未知的能力: {capability}")

    providers = ProviderManager.list_providers_by_capability(cap)
    manager = get_provider_manager()

    return [
        ProviderInfoResponse(
            provider_type=p.provider_type.value,
            display_name=p.display_name,
            website=p.website,
            capabilities=[c.value for c in p.capabilities],
            description=p.description,
            api_doc_url=p.api_doc_url,
            is_configured=p.provider_type in manager._configs,
            models=[{"name": m.name, "display_name": m.display_name} for m in p.models]
        )
        for p in providers
    ]


# ==================== 豆包3D模型配置API ====================

@router.get("/doubao/3d-config")
async def get_doubao_3d_config():
    """获取豆包3D模型生成的完整配置选项"""
    config = DoubaoProvider.get_3d_config()
    return {
        "model_name": config["model_name"],
        "subdivision_levels": config["subdivision_levels"],
        "file_formats": config["file_formats"],
        "price_per_model": config["price_per_model"],
        "estimated_time": config["estimated_time"],
        "description": "豆包Seed3D是基于Diffusion Transformer架构的3D生成模型，"
                      "能够在几分钟内输出包含多边形面片与PBR材质的高精度资产。"
                      "生成结果具备边缘锐利清晰、薄面结构稳定不变形的特征。",
        "features": [
            "支持30k/100k/200k三种面数精度",
            "支持GLB/OBJ/USD/USDZ多种格式",
            "输出包含RGB和PBR两种纹理版本",
            "6K分辨率下几何细节清晰可见",
        ]
    }


# ==================== 联想生成API ====================

class AssociationRequest(BaseModel):
    """联想生成请求"""
    category: str = Field(..., description="物品类别，如'椅子'、'变压器'")
    count: int = Field(20, description="生成数量", ge=5, le=100)
    mode: str = Field("comprehensive", description="联想模式: style/spec/purpose/material/era/region/comprehensive")
    custom_requirements: Optional[str] = Field(None, description="自定义要求")
    provider: str = Field("deepseek", description="使用的AI服务商")
    model: Optional[str] = Field(None, description="使用的模型")


class AssociationResponse(BaseModel):
    """联想生成响应"""
    category: str
    mode: str
    total_count: int
    items: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@router.post("/association/generate", response_model=AssociationResponse)
async def generate_association(request: AssociationRequest):
    """
    联想生成 - 为指定类别生成多种不同样式的物品

    示例：
    - 输入"椅子"，生成办公椅、餐椅、电竞椅、折叠椅等20+种不同椅子
    - 输入"变压器"，生成不同电压等级、功率、用途的变压器
    """
    manager = get_provider_manager()

    try:
        provider_type = ProviderType(request.provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"未知的服务商: {request.provider}")

    if provider_type not in manager._configs:
        raise HTTPException(status_code=400, detail=f"服务商 {request.provider} 未配置API密钥")

    try:
        mode = AssociationMode(request.mode)
    except ValueError:
        mode = AssociationMode.COMPREHENSIVE

    generator = AssociationGenerator(
        provider_type=provider_type,
        model=request.model
    )

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: generator.generate(
            category=request.category,
            count=request.count,
            mode=mode,
            custom_requirements=request.custom_requirements
        )
    )

    return AssociationResponse(
        category=result.category,
        mode=result.mode.value,
        total_count=result.total_count,
        items=[
            {
                "name": item.name,
                "description": item.description,
                "prompt": item.prompt,
                "subcategory": item.subcategory,
                "specifications": item.specifications,
                "tags": item.tags,
            }
            for item in result.items
        ],
        metadata=result.metadata
    )


@router.get("/association/categories")
async def list_categories(industry: Optional[str] = None):
    """获取预定义的类别库"""
    return CategorySuggester.get_categories(industry)


@router.get("/association/search")
async def search_categories(keyword: str):
    """搜索相关类别"""
    results = CategorySuggester.search_category(keyword)
    return {"keyword": keyword, "results": results}


# ==================== 批量生成API ====================

class BatchCreateRequest(BaseModel):
    """批量任务创建请求"""
    items: List[Dict[str, Any]] = Field(..., description="生成项目列表")
    category: str = Field("batch", description="类别名称")
    max_parallel: int = Field(3, description="最大并行数", ge=1, le=10)
    subdivision_level: str = Field("medium", description="3D精度: low/medium/high")
    file_format: str = Field("glb", description="输出格式: glb/obj/usd/usdz")


class BatchFromAssociationRequest(BaseModel):
    """从联想结果创建批量任务"""
    association_request: AssociationRequest
    max_parallel: int = Field(3, ge=1, le=10)
    subdivision_level: str = Field("medium")
    file_format: str = Field("glb")


class BatchStatusResponse(BaseModel):
    """批量任务状态响应"""
    batch_id: str
    total: int
    completed: int
    failed: int
    running: int
    pending: int
    progress_percent: float
    current_items: List[Dict]


@router.post("/batch/create")
async def create_batch(request: BatchCreateRequest, background_tasks: BackgroundTasks):
    """创建批量生成任务"""
    manager = get_batch_manager()

    config = BatchConfig(
        max_parallel=request.max_parallel,
        subdivision_level=request.subdivision_level,
        file_format=request.file_format,
    )

    job = manager.create_job(config)
    job.add_items(request.items)

    # 设置流水线
    gemini_key = os.environ.get("GEMINI_API_KEY")
    ark_key = os.environ.get("ARK_API_KEY")
    if gemini_key and ark_key:
        pipeline_config = PipelineConfig(
            gemini_api_key=gemini_key,
            ark_api_key=ark_key,
            mesh_quality=request.subdivision_level,
            file_format=request.file_format,
        )
        pipeline = ModelForgePipeline(pipeline_config)
        job.set_pipeline(pipeline)

    # 后台运行
    background_tasks.add_task(job.run, request.category)

    return {
        "batch_id": job.batch_id,
        "total": len(request.items),
        "status": "started",
        "message": "批量任务已创建并开始执行"
    }


@router.post("/batch/from-association")
async def create_batch_from_association(
    request: BatchFromAssociationRequest,
    background_tasks: BackgroundTasks
):
    """
    从联想生成结果创建批量任务

    一站式流程：
    1. 先调用联想生成获取物品列表
    2. 自动创建批量任务
    3. 并行生成3D模型
    """
    # 先执行联想生成
    manager = get_provider_manager()
    assoc_req = request.association_request

    try:
        provider_type = ProviderType(assoc_req.provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"未知的服务商: {assoc_req.provider}")

    if provider_type not in manager._configs:
        raise HTTPException(status_code=400, detail=f"服务商 {assoc_req.provider} 未配置")

    try:
        mode = AssociationMode(assoc_req.mode)
    except ValueError:
        mode = AssociationMode.COMPREHENSIVE

    generator = AssociationGenerator(provider_type=provider_type, model=assoc_req.model)

    loop = asyncio.get_event_loop()
    assoc_result = await loop.run_in_executor(
        None,
        lambda: generator.generate(
            category=assoc_req.category,
            count=assoc_req.count,
            mode=mode,
            custom_requirements=assoc_req.custom_requirements
        )
    )

    # 创建批量任务
    batch_manager = get_batch_manager()
    config = BatchConfig(
        max_parallel=request.max_parallel,
        subdivision_level=request.subdivision_level,
        file_format=request.file_format,
    )

    job = batch_manager.create_job(config)
    job.add_from_association(assoc_result)

    # 设置流水线
    gemini_key = os.environ.get("GEMINI_API_KEY")
    ark_key = os.environ.get("ARK_API_KEY")
    if gemini_key and ark_key:
        pipeline_config = PipelineConfig(
            gemini_api_key=gemini_key,
            ark_api_key=ark_key,
            mesh_quality=request.subdivision_level,
            file_format=request.file_format,
        )
        pipeline = ModelForgePipeline(pipeline_config)
        job.set_pipeline(pipeline)

    # 后台运行
    background_tasks.add_task(job.run, assoc_req.category)

    return {
        "batch_id": job.batch_id,
        "category": assoc_req.category,
        "total": assoc_result.total_count,
        "items_preview": [
            {"name": item.name, "description": item.description[:100]}
            for item in assoc_result.items[:5]
        ],
        "status": "started",
        "message": f"已联想生成 {assoc_result.total_count} 个物品，批量任务已开始"
    }


@router.get("/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """获取批量任务状态"""
    manager = get_batch_manager()
    job = manager.get_job(batch_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"批量任务 {batch_id} 不存在")

    progress = job.get_progress()
    return BatchStatusResponse(
        batch_id=progress.batch_id,
        total=progress.total,
        completed=progress.completed,
        failed=progress.failed,
        running=progress.running,
        pending=progress.pending,
        progress_percent=progress.progress_percent,
        current_items=progress.current_items
    )


@router.get("/batch")
async def list_batch_jobs():
    """列出所有批量任务"""
    manager = get_batch_manager()
    return {
        "running": manager.list_jobs(),
        "completed": manager.list_completed_batches()
    }


@router.get("/batch/{batch_id}/models")
async def get_batch_models(batch_id: str):
    """获取批量任务中的所有模型"""
    manager = get_batch_manager()
    models = manager.get_batch_models(batch_id)
    return {"batch_id": batch_id, "models": models}


# ==================== 模型库API ====================

@router.get("/library/browse")
async def browse_model_library(
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    浏览3D模型库

    支持分页和按类别筛选
    """
    output_dir = Path(os.environ.get("OUTPUT_DIR", "./output"))
    models = []

    # 扫描单个生成的模型
    for job_dir in output_dir.iterdir():
        if job_dir.is_dir() and job_dir.name != "batch":
            result_file = job_dir / "result.json"
            if result_file.exists():
                import json
                with open(result_file, "r", encoding="utf-8") as f:
                    result = json.load(f)
                    models.append({
                        "id": job_dir.name,
                        "type": "single",
                        "description": result.get("description", ""),
                        "created_at": result.get("created_at"),
                        "model_files": result.get("model_files", []),
                        "image_path": f"/api/v1/jobs/{job_dir.name}/image" if (job_dir / "image.png").exists() else None
                    })

    # 扫描批量生成的模型
    batch_dir = output_dir / "batch"
    if batch_dir.exists():
        manager = get_batch_manager()
        for batch in manager.list_completed_batches():
            batch_models = manager.get_batch_models(batch["batch_id"])
            for m in batch_models:
                if category is None or category.lower() in batch.get("category", "").lower():
                    models.append({
                        "id": m["id"],
                        "type": "batch",
                        "batch_id": batch["batch_id"],
                        "name": m["name"],
                        "description": m["description"],
                        "created_at": batch.get("created_at"),
                        "model_files": m.get("model_files", []),
                    })

    # 分页
    total = len(models)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "models": models[start:end]
    }


@router.get("/library/stats")
async def get_library_stats():
    """获取模型库统计信息"""
    output_dir = Path(os.environ.get("OUTPUT_DIR", "./output"))

    single_count = 0
    batch_count = 0
    total_size = 0

    # 统计单个模型
    for job_dir in output_dir.iterdir():
        if job_dir.is_dir() and job_dir.name != "batch":
            if (job_dir / "result.json").exists():
                single_count += 1
                for f in job_dir.rglob("*"):
                    if f.is_file():
                        total_size += f.stat().st_size

    # 统计批量模型
    batch_dir = output_dir / "batch"
    if batch_dir.exists():
        manager = get_batch_manager()
        for batch in manager.list_completed_batches():
            batch_models = manager.get_batch_models(batch["batch_id"])
            batch_count += len(batch_models)

    return {
        "single_models": single_count,
        "batch_models": batch_count,
        "total_models": single_count + batch_count,
        "total_size_mb": round(total_size / 1024 / 1024, 2),
    }
