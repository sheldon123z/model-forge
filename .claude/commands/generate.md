---
description: 从文字描述生成3D模型
argument-hint: <description> [--domain domain] [--style style] [--quality quality]
---

# Model Forge - 3D 模型生成

从文字描述生成高质量3D模型。

## 参数

- `$ARGUMENTS` - 对象描述和可选参数

## 支持的领域 (--domain)

| 值 | 说明 |
|---|------|
| power_grid | 电力系统 (变压器、断路器、绝缘子) |
| manufacturing | 制造业 (CNC机床、机械臂) |
| architecture | 建筑 (建筑模型、室内设计) |
| automotive | 汽车 (车辆、发动机) |
| aerospace | 航空航天 (飞机、卫星) |
| medical | 医疗设备 (手术机器人) |
| robotics | 机器人 (工业机器人) |
| furniture | 家具 (办公椅、桌子) |
| electronics | 电子产品 (消费电子) |
| general | 通用 (自动检测) |

## 支持的风格 (--style)

| 值 | 说明 |
|---|------|
| photorealistic | 照片级真实 |
| industrial | 工业摄影风格 |
| product | 产品展示风格 |
| technical | 技术图纸风格 |
| artistic | 艺术风格 |
| minimal | 简约风格 |

## 模型精度 (--quality)

| 值 | 说明 |
|---|------|
| high | 高精度 (~50k面) |
| medium | 中等精度 (~30k面) |
| low | 低精度 (~10k面) |

## 执行

请按以下步骤执行：

1. 检查 `.env` 文件是否存在并配置了 API Key
2. 解析用户参数
3. 执行生成命令

```bash
# 确保在 model-forge 目录
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

# 检查环境
if [ ! -f .env ]; then
    echo "请先配置 .env 文件: cp .env.example .env"
    exit 1
fi

# 执行生成
model-forge generate $ARGUMENTS
```

## 示例

```bash
# 电力设备
/generate 220kV油浸式变压器 --domain power_grid --quality high

# 机器人
/generate 一台6轴工业机器人手臂 --style product

# 家具
/generate 现代简约办公椅 --domain furniture --style minimal

# 自动检测领域
/generate 一辆红色跑车
```

---

如果用户未提供描述，使用 AskUserQuestion 询问：
1. 要生成的3D对象描述
2. 行业领域（可选，默认自动检测）
3. 渲染风格（可选，默认 photorealistic）
4. 模型精度（可选，默认 medium）

执行完成后报告：
- 检测到的领域
- 生成的图像路径
- 3D模型文件路径
