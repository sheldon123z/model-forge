"""
Model Forge - AI-Powered Universal 3D Model Generation

从文字描述生成3D模型的完整流水线：需求 → Prompt → 图像 → 3D模型

支持多行业领域：电力系统、制造业、建筑、汽车、航空航天、医疗、机器人、家具、电子等

使用:
    from model_forge import ModelForgePipeline, PipelineConfig

    config = PipelineConfig(
        gemini_api_key="your-gemini-key",
        ark_api_key="your-ark-key"
    )
    pipeline = ModelForgePipeline(config)
    result = pipeline.run("一台220kV油浸式变压器")

高级用法 (指定领域和风格):
    from model_forge import IndustryDomain, RenderStyle, PromptConfig

    prompt_config = PromptConfig(
        domain=IndustryDomain.ROBOTICS,
        style=RenderStyle.PRODUCT,
        use_chain_of_thought=True
    )
"""

__version__ = "1.1.0"
__author__ = "Grid AutoPilot Team"

from .core.pipeline import ModelForgePipeline, PipelineConfig, PipelineResult, PipelineStage
from .core.prompt_generator import (
    PromptGenerator,
    PromptConfig,
    IndustryDomain,
    RenderStyle
)
from .core.image_generator import ImageGenerator
from .core.model_generator import ModelGenerator

__all__ = [
    # Pipeline
    "ModelForgePipeline",
    "PipelineConfig",
    "PipelineResult",
    "PipelineStage",
    # Prompt Generator
    "PromptGenerator",
    "PromptConfig",
    "IndustryDomain",
    "RenderStyle",
    # Other Generators
    "ImageGenerator",
    "ModelGenerator",
]
