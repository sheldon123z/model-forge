# Model Forge

🔨 **AI-Powered Universal 3D Model Generation Pipeline**

从文字描述自动生成3D模型的完整流水线：**需求描述 → AI Prompt → 图像 → 3D模型**

## ✨ 特性

### 🌐 多行业支持
- **电力系统** - 变压器、断路器、绝缘子、杆塔等
- **制造业** - CNC机床、机械臂、生产线设备
- **建筑** - 建筑模型、室内设计、结构组件
- **汽车** - 车辆、发动机、底盘组件
- **航空航天** - 飞机、卫星、无人机
- **医疗设备** - 手术机器人、诊断设备、植入物
- **机器人** - 工业机器人、服务机器人
- **家具** - 办公家具、家居用品
- **电子产品** - 消费电子、电路板、设备外壳

### 🧠 高级 Prompt 工程
- **Chain-of-Thought** - 链式思维推理，生成结构化详细描述
- **Few-shot Learning** - 领域特定示例学习
- **Self-Verification** - 自动验证和优化生成的提示词
- **Domain Detection** - 自动检测行业领域
- **Style Adaptation** - 多种渲染风格支持

### 🎨 渲染风格
- `photorealistic` - 照片级真实渲染
- `industrial` - 工业摄影风格
- `product` - 产品展示风格
- `technical` - 技术图纸风格
- `artistic` - 艺术风格
- `minimal` - 简约风格

### 🛠️ 完整工具链
- 🤖 AI 提示词生成 (Gemini 2.5 Flash)
- 🎨 AI 图像生成 (Gemini 2.0 Flash)
- 📦 AI 3D模型生成 (火山引擎 doubao-seed3d)
- 🌐 Web 界面
- ⚡ CLI 工具
- 🔌 REST API

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-org/model-forge.git
cd model-forge

# 安装依赖
pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key
```

### 命令行使用

```bash
# 生成电力设备3D模型
model-forge generate "220kV油浸式变压器，带散热翅片" \
  --type 变压器 \
  --voltage 220kV \
  --quality high

# 生成机器人3D模型 (自动检测领域)
model-forge generate "一台6轴工业机器人手臂" --quality high

# 生成家具3D模型
model-forge generate "现代简约风格的人体工学办公椅" \
  --domain furniture \
  --style minimal

# 启动Web服务
model-forge server --port 8088
```

### Python API

```python
from model_forge import ModelForgePipeline, PipelineConfig
from model_forge import IndustryDomain, RenderStyle

# 基础用法 (自动检测领域)
config = PipelineConfig(
    gemini_api_key="your-gemini-key",
    ark_api_key="your-ark-key",
    mesh_quality="high"
)
pipeline = ModelForgePipeline(config)
result = pipeline.run("一台220kV油浸式变压器")

# 高级用法 (指定领域和风格)
result = pipeline.run(
    description="一台6轴工业机器人手臂",
    domain=IndustryDomain.ROBOTICS,
    style=RenderStyle.PRODUCT
)

print(f"领域: {result.detected_domain}")
print(f"置信度: {result.confidence}")
print(f"3D模型: {result.model_dir}")
```

### REST API

```bash
# 启动服务
model-forge server

# 生成3D模型 (自动检测领域)
curl -X POST http://localhost:8088/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "一台6轴工业机器人手臂",
    "style": "product",
    "mesh_quality": "high"
  }'

# 指定领域
curl -X POST http://localhost:8088/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "现代简约办公椅",
    "domain": "furniture",
    "style": "minimal"
  }'

# 单独生成Prompt (不生成模型)
curl -X POST http://localhost:8088/api/v1/prompt/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "一台工业焊接机器人"
  }'

# 查看支持的领域
curl http://localhost:8088/api/v1/domains

# 查看支持的风格
curl http://localhost:8088/api/v1/styles
```

## 📋 Makefile 命令

```bash
make help           # 显示帮助
make install        # 安装依赖
make dev            # 开发模式启动 (热重载)
make server         # 生产模式启动
make generate       # 交互式生成
make generate-demo  # 生成演示模型
make check-env      # 检查环境配置
make clean          # 清理输出
```

## 🔧 配置

### 环境变量

```bash
# 必需
GEMINI_API_KEY=your-gemini-api-key
ARK_API_KEY=your-ark-api-key

# 可选
OUTPUT_DIR=./output
MESH_QUALITY=medium  # high/medium/low
FILE_FORMAT=glb      # glb/obj
PORT=8088
```

### Prompt 工程配置

```python
from model_forge import PipelineConfig

config = PipelineConfig(
    gemini_api_key="...",
    ark_api_key="...",
    # Prompt 工程选项
    use_few_shot=True,           # Few-shot 示例学习
    use_chain_of_thought=True,   # 链式思维推理
    use_self_verification=True,  # 自动验证优化
    optimize_iterations=1,       # 优化迭代次数
)
```

## 📁 输出结构

```
output/{job_id}/
├── prompt.json      # 生成的提示词和分析
│   ├── description
│   ├── prompt
│   ├── negative_prompt
│   ├── analysis      # Chain-of-thought 分析
│   ├── confidence    # 置信度
│   ├── detected_domain
│   └── style
├── image.png        # 生成的图像
├── model/           # 3D模型
│   ├── rgb/         # RGB纹理版本
│   └── pbr/         # PBR物理渲染版本
└── result.json      # 完整结果
```

## 🏗️ 项目结构

```
model-forge/
├── model_forge/           # Python 包
│   ├── __init__.py       # 包入口
│   ├── cli.py            # CLI 命令
│   ├── server.py         # FastAPI 服务
│   ├── core/             # 核心模块
│   │   ├── prompt_generator.py  # 高级 Prompt 生成器
│   │   ├── image_generator.py   # 图像生成
│   │   ├── model_generator.py   # 3D模型生成
│   │   └── pipeline.py          # 流水线编排
│   └── api/
│       └── routes.py     # REST API
├── templates/
│   └── index.html        # Web 界面
├── pyproject.toml        # 项目配置
├── Makefile              # 快捷命令
└── README.md
```

## 📖 API 文档

启动服务后访问:
- **Swagger UI**: http://localhost:8088/docs
- **ReDoc**: http://localhost:8088/redoc

### 主要端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/generate` | POST | 启动完整3D生成流水线 |
| `/api/v1/jobs/{id}` | GET | 获取任务状态 |
| `/api/v1/jobs` | GET | 列出所有任务 |
| `/api/v1/prompt/generate` | POST | 单独生成Prompt |
| `/api/v1/prompt/optimize` | POST | 优化已有Prompt |
| `/api/v1/domains` | GET | 列出支持的领域 |
| `/api/v1/styles` | GET | 列出支持的风格 |
| `/api/v1/jobs/{id}/image` | GET | 获取生成的图像 |
| `/api/v1/jobs/{id}/model/{file}` | GET | 获取3D模型文件 |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License
