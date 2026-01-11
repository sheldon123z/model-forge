"""
批量3D模型生成器 - 支持并行生成多个3D模型

功能：
- 并行生成多个3D模型
- 实时进度追踪
- 自动重试失败任务
- 科学的文件存储和命名
"""

import os
import asyncio
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


@dataclass
class BatchItem:
    """批量生成的单个项目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    prompt: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed
    progress: int = 0
    stage: str = ""  # prompt_generation, image_generation, model_generation
    result: Optional[Dict] = None
    error: Optional[str] = None
    output_dir: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class BatchConfig:
    """批量生成配置"""
    # 并行配置
    max_parallel: int = 3           # 最大并行数
    retry_count: int = 2            # 重试次数
    retry_delay: float = 5.0        # 重试延迟(秒)

    # 3D模型配置
    subdivision_level: str = "medium"  # low/medium/high
    file_format: str = "glb"           # glb/obj/usd/usdz

    # 文件存储配置
    output_base_dir: str = "./output/batch"
    naming_pattern: str = "{category}_{name}_{id}"  # 命名模式
    create_index: bool = True       # 创建索引文件

    # AI配置
    prompt_provider: str = "deepseek"  # 用于生成prompt的服务商
    prompt_model: Optional[str] = None


@dataclass
class BatchProgress:
    """批量生成进度"""
    batch_id: str
    total: int
    completed: int
    failed: int
    running: int
    pending: int
    progress_percent: float
    current_items: List[Dict]
    estimated_remaining: Optional[float] = None


@dataclass
class BatchResult:
    """批量生成结果"""
    batch_id: str
    category: str
    config: BatchConfig
    items: List[BatchItem]
    total: int
    completed: int
    failed: int
    start_time: str
    end_time: Optional[str]
    duration_seconds: Optional[float]
    output_dir: str
    index_file: Optional[str]


class BatchGenerator:
    """批量3D模型生成器"""

    def __init__(self, config: BatchConfig):
        self.config = config
        self.batch_id = str(uuid.uuid4())[:8]
        self._items: List[BatchItem] = []
        self._lock = threading.Lock()
        self._progress_callback: Optional[Callable] = None
        self._pipeline = None

    def set_pipeline(self, pipeline):
        """设置3D生成流水线"""
        self._pipeline = pipeline

    def set_progress_callback(self, callback: Callable[[BatchProgress], None]):
        """设置进度回调"""
        self._progress_callback = callback

    def add_items(self, items: List[Dict[str, Any]]) -> List[BatchItem]:
        """
        添加批量生成项目

        Args:
            items: 项目列表，每个项目包含:
                - name: 名称
                - description: 描述
                - prompt: 可选的自定义prompt

        Returns:
            添加的BatchItem列表
        """
        batch_items = []
        for item in items:
            batch_item = BatchItem(
                name=item.get("name", ""),
                description=item.get("description", ""),
                prompt=item.get("prompt"),
            )
            batch_items.append(batch_item)
            self._items.append(batch_item)
        return batch_items

    def add_from_association(self, association_result) -> List[BatchItem]:
        """从联想结果添加项目"""
        items = []
        for assoc_item in association_result.items:
            items.append({
                "name": assoc_item.name,
                "description": assoc_item.description,
                "prompt": assoc_item.prompt,
            })
        return self.add_items(items)

    def get_progress(self) -> BatchProgress:
        """获取当前进度"""
        with self._lock:
            completed = sum(1 for item in self._items if item.status == "completed")
            failed = sum(1 for item in self._items if item.status == "failed")
            running = sum(1 for item in self._items if item.status == "running")
            pending = sum(1 for item in self._items if item.status == "pending")
            total = len(self._items)

            progress_percent = (completed + failed) / total * 100 if total > 0 else 0

            current_items = [
                {
                    "id": item.id,
                    "name": item.name,
                    "status": item.status,
                    "stage": item.stage,
                    "progress": item.progress,
                }
                for item in self._items if item.status == "running"
            ]

            return BatchProgress(
                batch_id=self.batch_id,
                total=total,
                completed=completed,
                failed=failed,
                running=running,
                pending=pending,
                progress_percent=progress_percent,
                current_items=current_items,
            )

    def _update_item(self, item: BatchItem, **kwargs):
        """更新项目状态"""
        with self._lock:
            for key, value in kwargs.items():
                setattr(item, key, value)

        if self._progress_callback:
            self._progress_callback(self.get_progress())

    def _generate_output_path(self, item: BatchItem, category: str) -> Path:
        """生成输出路径"""
        # 清理名称
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in item.name)

        # 应用命名模式
        dir_name = self.config.naming_pattern.format(
            category=category,
            name=safe_name[:30],
            id=item.id,
            date=datetime.now().strftime("%Y%m%d"),
        )

        return Path(self.config.output_base_dir) / self.batch_id / dir_name

    def _generate_single(self, item: BatchItem, category: str) -> BatchItem:
        """生成单个3D模型"""
        if not self._pipeline:
            raise ValueError("Pipeline not set. Call set_pipeline() first.")

        try:
            self._update_item(
                item,
                status="running",
                started_at=datetime.now().isoformat(),
            )

            output_dir = self._generate_output_path(item, category)
            output_dir.mkdir(parents=True, exist_ok=True)
            item.output_dir = str(output_dir)

            # 进度回调
            def progress_callback(info):
                stage = info.get("stage", "")
                if "prompt" in stage:
                    self._update_item(item, stage="prompt_generation", progress=20)
                elif "image" in stage:
                    self._update_item(item, stage="image_generation", progress=50)
                elif "model" in stage or "processing" in stage:
                    self._update_item(item, stage="model_generation", progress=80)

            # 运行流水线
            result = self._pipeline.run(
                description=item.description,
                custom_prompt=item.prompt,
                output_dir=output_dir,
                progress_callback=progress_callback,
            )

            self._update_item(
                item,
                status="completed",
                progress=100,
                result=result.__dict__ if hasattr(result, "__dict__") else result,
                completed_at=datetime.now().isoformat(),
            )

        except Exception as e:
            self._update_item(
                item,
                status="failed",
                error=str(e),
                completed_at=datetime.now().isoformat(),
            )

        return item

    def run(self, category: str = "batch") -> BatchResult:
        """
        运行批量生成

        Args:
            category: 类别名称

        Returns:
            批量生成结果
        """
        start_time = datetime.now()

        # 创建输出目录
        batch_dir = Path(self.config.output_base_dir) / self.batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)

        # 并行执行
        with ThreadPoolExecutor(max_workers=self.config.max_parallel) as executor:
            futures = {
                executor.submit(self._generate_single, item, category): item
                for item in self._items
            }

            for future in as_completed(futures):
                item = futures[future]
                try:
                    future.result()
                except Exception as e:
                    self._update_item(item, status="failed", error=str(e))

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 创建索引文件
        index_file = None
        if self.config.create_index:
            index_file = self._create_index(batch_dir, category)

        # 统计结果
        completed = sum(1 for item in self._items if item.status == "completed")
        failed = sum(1 for item in self._items if item.status == "failed")

        return BatchResult(
            batch_id=self.batch_id,
            category=category,
            config=self.config,
            items=self._items,
            total=len(self._items),
            completed=completed,
            failed=failed,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_seconds=duration,
            output_dir=str(batch_dir),
            index_file=index_file,
        )

    async def arun(self, category: str = "batch") -> BatchResult:
        """异步运行批量生成"""
        # 使用asyncio在线程池中运行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, category)

    def _create_index(self, batch_dir: Path, category: str) -> str:
        """创建索引文件"""
        index_data = {
            "batch_id": self.batch_id,
            "category": category,
            "created_at": datetime.now().isoformat(),
            "config": {
                "subdivision_level": self.config.subdivision_level,
                "file_format": self.config.file_format,
                "max_parallel": self.config.max_parallel,
            },
            "items": []
        }

        for item in self._items:
            item_info = {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "status": item.status,
                "output_dir": item.output_dir,
            }
            if item.status == "completed" and item.result:
                # 添加模型文件路径
                result = item.result
                if isinstance(result, dict):
                    item_info["model_files"] = result.get("model_files", [])
                    item_info["image_path"] = result.get("image_path")
            index_data["items"].append(item_info)

        index_file = batch_dir / "index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        return str(index_file)


class BatchJobManager:
    """批量任务管理器 - 管理多个批量生成任务"""

    def __init__(self, storage_dir: str = "./output/batch"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: Dict[str, BatchGenerator] = {}

    def create_job(self, config: Optional[BatchConfig] = None) -> BatchGenerator:
        """创建新的批量任务"""
        if config is None:
            config = BatchConfig(output_base_dir=str(self.storage_dir))
        else:
            config.output_base_dir = str(self.storage_dir)

        generator = BatchGenerator(config)
        self._jobs[generator.batch_id] = generator
        return generator

    def get_job(self, batch_id: str) -> Optional[BatchGenerator]:
        """获取批量任务"""
        return self._jobs.get(batch_id)

    def list_jobs(self) -> List[Dict]:
        """列出所有任务"""
        jobs = []
        for batch_id, generator in self._jobs.items():
            progress = generator.get_progress()
            jobs.append({
                "batch_id": batch_id,
                "total": progress.total,
                "completed": progress.completed,
                "failed": progress.failed,
                "progress_percent": progress.progress_percent,
            })
        return jobs

    def list_completed_batches(self) -> List[Dict]:
        """列出已完成的批次"""
        batches = []
        if not self.storage_dir.exists():
            return batches

        for batch_dir in self.storage_dir.iterdir():
            if batch_dir.is_dir():
                index_file = batch_dir / "index.json"
                if index_file.exists():
                    with open(index_file, "r", encoding="utf-8") as f:
                        index_data = json.load(f)
                        batches.append({
                            "batch_id": index_data.get("batch_id"),
                            "category": index_data.get("category"),
                            "created_at": index_data.get("created_at"),
                            "item_count": len(index_data.get("items", [])),
                            "path": str(batch_dir),
                        })

        return sorted(batches, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_batch_models(self, batch_id: str) -> List[Dict]:
        """获取批次中的所有模型"""
        batch_dir = self.storage_dir / batch_id
        index_file = batch_dir / "index.json"

        if not index_file.exists():
            return []

        with open(index_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)

        models = []
        for item in index_data.get("items", []):
            if item.get("status") == "completed":
                model_info = {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "output_dir": item.get("output_dir"),
                    "model_files": item.get("model_files", []),
                    "image_path": item.get("image_path"),
                }
                models.append(model_info)

        return models
