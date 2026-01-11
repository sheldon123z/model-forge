# Model Forge

**AI-Powered Universal 3D Model Generation Pipeline**

从文字描述自动生成3D模型的完整流水线：**需求描述 → AI Prompt → 图像 → 3D模型**

## 特性

### 多服务商支持

支持 **11+ 国内外 AI 服务商**，统一接口：

| 服务商 | 特点 | 能力 |
|--------|------|------|
| **DeepSeek** | 国产顶尖开源模型，极低成本 | 文本生成、代码 |
| **豆包 (Doubao)** | 字节跳动，支持3D模型生成 | 文本、图像、**3D模型** |
| **Kimi** | 256K超长上下文，擅长Agent | 文本生成、代码 |
| **MiniMax** | 400万token上下文 | 文本、语音 |
| **智谱 GLM** | 永久免费GLM-4-Flash | 文本、图像理解 |
| **百川** | 192K窗口，角色扮演出色 | 文本生成 |
| **讯飞星火** | 联网搜索、Function Call | 文本、图像理解 |
| **通义千问** | 阿里云，思考模式 | 文本、多模态 |
| **零一万物 Yi** | 200K上下文 | 文本生成 |
| **OpenRouter** | 400+模型聚合 | 全能力 |
| **Gemini** | 2M超长上下文 | 文本、图像、多模态 |

### 豆包 3D 模型生成

深度集成豆包 Seed3D API，完整参数支持：

- **精度级别**: 30k面 / 100k面 / 200k面
- **文件格式**: GLB / OBJ / USD / USDZ
- **价格**: 2.4元/模型

### 联想批量生成

输入一个类别，AI 自动联想生成多种不同样式的物品：

```
输入: "椅子"
输出:
├── 现代简约办公椅 (旋转、网面靠背、五星脚)
├── 经典木质餐椅 (橡木、雕花靠背、四脚)
├── 电竞游戏椅 (人体工学、赛车风格)
├── 户外折叠椅 (铝合金、防水帆布)
├── 北欧风格沙发椅 (布艺、高脚、圆润)
└── ... 更多变体
```

**联想模式**:
- `style` - 不同设计风格
- `spec` - 不同规格参数
- `purpose` - 不同用途场景
- `material` - 不同材质
- `era` - 不同时代风格
- `region` - 不同地区特色
- `comprehensive` - 综合联想

### 批量并行生成

- 多任务并行处理
- 实时进度追踪
- 可配置并行数
- 进度条可视化

### 多行业支持

- **电力系统** - 变压器、断路器、绝缘子、杆塔等
- **制造业** - CNC机床、机械臂、生产线设备
- **建筑** - 建筑模型、室内设计、结构组件
- **家具** - 办公家具、家居用品
- **医疗设备** - 手术机器人、诊断设备
- **交通工具** - 汽车、卡车、飞机
- 更多...

### 高级 Prompt 工程

- **Chain-of-Thought** - 链式思维推理
- **Few-shot Learning** - 领域特定示例学习
- **Self-Verification** - 自动验证优化
- **Domain Detection** - 自动检测行业领域

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/sheldon123z/model-forge.git
cd model-forge

# 安装依赖
pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key
```

### Web 界面

```bash
# 启动服务
model-forge server --port 8088

# 访问 http://localhost:8088
```

Web 界面提供：
- **单个生成**: 输入描述生成单个3D模型
- **批量生成**: 联想生成 + 并行批量处理
- **模型库**: 浏览已生成的所有3D模型
- **设置**: 配置各服务商API Key

### 命令行使用

```bash
# 生成单个3D模型
model-forge generate "220kV油浸式变压器" --quality high

# 启动Web服务
model-forge server --port 8088
```

### Python API

```python
from model_forge import ModelForgePipeline, PipelineConfig

# 基础用法
config = PipelineConfig(
    gemini_api_key="your-gemini-key",
    ark_api_key="your-ark-key",
    mesh_quality="high"
)
pipeline = ModelForgePipeline(config)
result = pipeline.run("一台220kV油浸式变压器")
```

### REST API

#### API v1 - 基础接口

```bash
# 生成3D模型
curl -X POST http://localhost:8088/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"description": "现代简约办公椅", "mesh_quality": "high"}'
```

#### API v2 - 扩展接口

```bash
# 列出所有支持的服务商
curl http://localhost:8088/api/v2/providers

# 获取豆包3D配置选项
curl http://localhost:8088/api/v2/doubao/3d-config

# 联想生成
curl -X POST http://localhost:8088/api/v2/association/generate \
  -H "Content-Type: application/json" \
  -d '{
    "category": "椅子",
    "count": 10,
    "mode": "comprehensive"
  }'

# 创建批量任务
curl -X POST http://localhost:8088/api/v2/batch/create \
  -H "Content-Type: application/json" \
  -d '{
    "prompts": ["办公椅prompt...", "餐椅prompt..."],
    "config": {
      "subdivision_level": "medium",
      "file_format": "glb",
      "max_parallel": 5
    }
  }'

# 从联想结果创建批量任务
curl -X POST http://localhost:8088/api/v2/batch/from-association \
  -H "Content-Type: application/json" \
  -d '{
    "category": "变压器",
    "count": 20,
    "mode": "comprehensive",
    "config": {
      "subdivision_level": "high",
      "file_format": "glb"
    }
  }'

# 查询批量任务状态
curl http://localhost:8088/api/v2/batch/{batch_id}/status

# 浏览模型库
curl http://localhost:8088/api/v2/library/browse

# 获取模型库统计
curl http://localhost:8088/api/v2/library/stats
```

## 配置

### 环境变量

```bash
# AI 服务商 API Keys
DEEPSEEK_API_KEY=your-key
ARK_API_KEY=your-key          # 豆包/火山引擎
KIMI_API_KEY=your-key
MINIMAX_API_KEY=your-key
MINIMAX_GROUP_ID=your-group-id
ZHIPU_API_KEY=your-key
BAICHUAN_API_KEY=your-key
SPARK_API_KEY=your-key
QWEN_API_KEY=your-key
YI_API_KEY=your-key
OPENROUTER_API_KEY=your-key
GEMINI_API_KEY=your-key

# 3D模型生成配置
OUTPUT_DIR=./output
MESH_QUALITY=medium           # low/medium/high (30k/100k/200k面)
FILE_FORMAT=glb               # glb/obj/usd/usdz

# 服务器配置
PORT=8088

# 批量生成配置
MAX_PARALLEL_TASKS=5
DEFAULT_ASSOCIATION_COUNT=20
```

## API 文档

启动服务后访问:
- **Swagger UI**: http://localhost:8088/docs
- **ReDoc**: http://localhost:8088/redoc

### API v1 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/generate` | POST | 启动完整3D生成流水线 |
| `/api/v1/jobs/{id}` | GET | 获取任务状态 |
| `/api/v1/jobs` | GET | 列出所有任务 |
| `/api/v1/prompt/generate` | POST | 单独生成Prompt |
| `/api/v1/domains` | GET | 列出支持的领域 |
| `/api/v1/styles` | GET | 列出支持的风格 |

### API v2 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v2/providers` | GET | 列出所有AI服务商 |
| `/api/v2/providers/{type}` | GET | 获取服务商详情 |
| `/api/v2/providers/configure` | POST | 配置服务商API Key |
| `/api/v2/doubao/3d-config` | GET | 获取豆包3D配置选项 |
| `/api/v2/association/generate` | POST | 联想生成物品列表 |
| `/api/v2/association/categories` | GET | 获取预设类别库 |
| `/api/v2/batch/create` | POST | 创建批量任务 |
| `/api/v2/batch/from-association` | POST | 从联想结果创建批量任务 |
| `/api/v2/batch/{id}/status` | GET | 获取批量任务状态 |
| `/api/v2/batch/{id}/cancel` | POST | 取消批量任务 |
| `/api/v2/library/browse` | GET | 浏览模型库 |
| `/api/v2/library/stats` | GET | 获取模型库统计 |

## 项目结构

```
model-forge/
├── model_forge/
│   ├── __init__.py
│   ├── cli.py                    # CLI 命令
│   ├── server.py                 # FastAPI 服务
│   ├── core/
│   │   ├── prompt_generator.py   # Prompt 生成器
│   │   ├── image_generator.py    # 图像生成
│   │   ├── model_generator.py    # 3D模型生成
│   │   ├── pipeline.py           # 流水线编排
│   │   ├── association_generator.py  # 联想生成器
│   │   └── batch_generator.py    # 批量生成器
│   ├── providers/                # AI 服务商
│   │   ├── base.py               # 基类定义
│   │   ├── manager.py            # 服务商管理器
│   │   ├── deepseek.py
│   │   ├── doubao.py             # 包含3D生成
│   │   ├── kimi.py
│   │   ├── minimax.py
│   │   ├── zhipu.py
│   │   ├── baichuan.py
│   │   ├── spark.py
│   │   ├── qwen.py
│   │   ├── yi.py
│   │   ├── openrouter.py
│   │   └── gemini.py
│   └── api/
│       ├── routes.py             # API v1
│       └── routes_v2.py          # API v2
├── templates/
│   └── index.html                # Web 界面
├── output/                       # 生成的模型
├── .env.example
├── pyproject.toml
├── Makefile
└── README.md
```

## 输出结构

```
output/
├── {job_id}/                     # 单个任务
│   ├── prompt.json
│   ├── image.png
│   ├── model/
│   │   ├── rgb/
│   │   └── pbr/
│   └── result.json
└── batch_{batch_id}/             # 批量任务
    ├── item_001_{name}/
    ├── item_002_{name}/
    └── ...
```

## Makefile 命令

```bash
make help           # 显示帮助
make install        # 安装依赖
make dev            # 开发模式启动 (热重载)
make server         # 生产模式启动
make generate       # 交互式生成
make clean          # 清理输出
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## License

MIT License
