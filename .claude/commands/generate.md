---
description: 从文字描述生成3D模型
argument-hint: <description> [--domain power_grid|robotics|...] [--style photorealistic|industrial|...] [--quality high|medium|low]
---

# Model Forge - 3D 模型生成

从文字描述生成完整的3D模型（GLB格式）。

**流程**: 需求描述 → AI Prompt → 图像生成 → 3D模型(doubao-seed3d)

## 参数

- `$ARGUMENTS` - 必需参数和可选标志:
  - 第一个参数: 对象描述（必需）
  - `--domain` - 行业领域
  - `--style` - 渲染风格
  - `--quality` - 模型精度 (high/medium/low)

## 执行代码

```python
import sys
import os
from pathlib import Path

# 当前项目即为 model-forge
from model_forge import ModelForgePipeline, PipelineConfig
from model_forge.core.prompt_generator import IndustryDomain, RenderStyle
from dotenv import load_dotenv

load_dotenv()

# 检查环境变量
gemini_key = os.environ.get("GEMINI_API_KEY")
ark_key = os.environ.get("ARK_API_KEY")

if not gemini_key or not ark_key:
    print("错误: 请设置 GEMINI_API_KEY 和 ARK_API_KEY 环境变量")
else:
    config = PipelineConfig(
        gemini_api_key=gemini_key,
        ark_api_key=ark_key,
        output_base_dir="./data/3d_models",
        mesh_quality="high"
    )

    pipeline = ModelForgePipeline(config)

    # 解析参数 $ARGUMENTS
    result = pipeline.run(
        description="$ARGUMENTS",
        domain=IndustryDomain.POWER_GRID  # 可根据 --domain 参数调整
    )

    print(f"\n生成完成!")
    print(f"  文件夹: {result.folder_name or result.job_id}")
    print(f"  领域: {result.detected_domain}")
    print(f"  图像: {result.image_path}")
    print(f"  3D模型目录: {result.model_dir}")
```

## 支持的领域

| 领域 | 值 | 示例 |
|------|-----|------|
| 电力系统 | power_grid | 变压器、断路器 |
| 机器人 | robotics | 工业机器人 |
| 制造业 | manufacturing | CNC机床 |
| 建筑 | architecture | 建筑模型 |
| 家具 | furniture | 办公椅 |
| 通用 | general | 自动检测 |

## 示例

```bash
# 电力设备
/generate 220kV油浸式变压器

# 机器人
/generate 6轴工业机器人手臂 --domain robotics

# 家具
/generate 人体工学办公椅 --domain furniture --style minimal
```

---

请根据用户描述 `$ARGUMENTS` 执行生成。如未提供描述，询问用户需要生成什么3D模型。
