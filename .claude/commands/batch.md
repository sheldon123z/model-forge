---
description: 批量并行生成多个3D模型
argument-hint: [--workers N] [--dry-run]
---

# Model Forge - 批量生成

并行批量生成多个3D模型，支持自定义并行数。

## 参数

- `--workers N` - 并行工作线程数（默认3，建议2-4）
- `--dry-run` - 仅预览将要生成的模型，不实际执行

## 使用方式

执行批量生成脚本：

```bash
python scripts/batch_generate.py $ARGUMENTS
```

或使用 Python API：

```python
from model_forge import ModelForgePipeline, PipelineConfig
from model_forge.core.prompt_generator import IndustryDomain
from concurrent.futures import ThreadPoolExecutor
import os

# 定义要生成的模型列表
models = [
    {"description": "220kV变压器", "domain": IndustryDomain.POWER_GRID},
    {"description": "SF6断路器", "domain": IndustryDomain.POWER_GRID},
    {"description": "6轴机器人", "domain": IndustryDomain.ROBOTICS},
]

config = PipelineConfig(
    gemini_api_key=os.environ.get("GEMINI_API_KEY"),
    ark_api_key=os.environ.get("ARK_API_KEY"),
    output_base_dir="./data/3d_models",
    mesh_quality="medium"
)

def generate_one(spec):
    pipeline = ModelForgePipeline(config)
    return pipeline.run(**spec)

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(generate_one, models))
```

## 预定义模型列表

编辑 `scripts/batch_generate.py` 中的 `MODELS_TO_GENERATE` 列表添加要生成的模型。

---

如用户提供模型列表，解析后并行执行生成。
