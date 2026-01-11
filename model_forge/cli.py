#!/usr/bin/env python3
"""
Model Forge CLI - 命令行工具

用法：
    model-forge generate "设备描述" [选项]
    model-forge server [选项]
    model-forge list
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from .core import ModelForgePipeline, PipelineConfig, PipelineStage


def check_api_keys(args) -> tuple:
    """检查并获取API密钥"""
    gemini_key = getattr(args, 'gemini_key', None) or os.environ.get("GEMINI_API_KEY")
    ark_key = getattr(args, 'ark_key', None) or os.environ.get("ARK_API_KEY")

    if not gemini_key:
        print("❌ 错误: 未设置 GEMINI_API_KEY")
        print("请通过 --gemini-key 参数或 .env 文件设置")
        sys.exit(1)
    if not ark_key:
        print("❌ 错误: 未设置 ARK_API_KEY")
        print("请通过 --ark-key 参数或 .env 文件设置")
        sys.exit(1)

    return gemini_key, ark_key


def create_pipeline(args) -> ModelForgePipeline:
    """创建流水线实例"""
    gemini_key, ark_key = check_api_keys(args)

    config = PipelineConfig(
        gemini_api_key=gemini_key,
        ark_api_key=ark_key,
        output_base_dir=Path(args.output_dir),
        mesh_quality=args.quality,
        file_format=args.format
    )
    return ModelForgePipeline(config)


def cmd_generate(args):
    """执行生成命令"""
    print("=" * 60)
    print("🔨 Model Forge - 3D模型生成")
    print("=" * 60)
    print(f"描述: {args.description}")
    print(f"设备类型: {args.type or '自动识别'}")
    print(f"电压等级: {args.voltage or '自动识别'}")
    print(f"模型精度: {args.quality}")
    print(f"输出目录: {args.output_dir}")
    print("=" * 60)

    pipeline = create_pipeline(args)

    def progress_callback(progress):
        stage = progress.get("stage", "")
        message = progress.get("message", "")
        if isinstance(stage, PipelineStage):
            stage = stage.value
        print(f"[{stage}] {message}")

    result = pipeline.run(
        description=args.description,
        equipment_type=args.type,
        voltage_level=args.voltage,
        custom_prompt=args.prompt,
        progress_callback=progress_callback
    )

    print("\n" + "=" * 60)
    print("📊 生成结果")
    print("=" * 60)

    if result.stage == PipelineStage.COMPLETED:
        print(f"✅ 状态: 成功")
        print(f"📁 任务ID: {result.job_id}")
        print(f"🖼️  图像: {result.image_path}")
        print(f"📦 模型目录: {result.model_dir}")
        if result.model_files:
            print(f"📄 模型文件:")
            for f in result.model_files:
                size_mb = f['size_bytes'] / 1024 / 1024
                print(f"   - {f['name']} ({size_mb:.1f} MB)")
    else:
        print(f"❌ 状态: 失败")
        print(f"   错误: {result.error}")

    return result


def cmd_server(args):
    """启动Web服务"""
    print(f"🚀 启动 Model Forge 服务...")
    print(f"   地址: http://0.0.0.0:{args.port}")
    print(f"   API文档: http://0.0.0.0:{args.port}/docs")

    from .server import run_server
    run_server(port=args.port, reload=args.reload)


def cmd_list(args):
    """列出历史任务"""
    pipeline = create_pipeline(args)
    jobs = pipeline.list_jobs()

    if not jobs:
        print("暂无历史任务")
        return

    print(f"共 {len(jobs)} 个任务:\n")
    for job in jobs:
        status = "✅" if job.get("stage") == "completed" else "❌"
        desc = job.get('description', '')[:50]
        print(f"{status} [{job['job_id']}] {desc}...")
        print(f"   创建时间: {job.get('created_at', 'N/A')}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Model Forge - 3D模型生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成变压器3D模型
  model-forge generate "220kV油浸式变压器，带散热翅片" --type 变压器 --voltage 220kV

  # 使用高精度生成
  model-forge generate "500kV输电杆塔" --quality high

  # 启动Web服务
  model-forge server --port 8088
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # generate 命令
    gen_parser = subparsers.add_parser("generate", help="生成3D模型")
    gen_parser.add_argument("description", help="设备描述")
    gen_parser.add_argument("--type", "-t", help="设备类型")
    gen_parser.add_argument("--voltage", "-v", help="电压等级")
    gen_parser.add_argument("--quality", "-q", default="medium", choices=["high", "medium", "low"], help="模型精度")
    gen_parser.add_argument("--format", "-f", default="glb", choices=["glb", "obj"], help="输出格式")
    gen_parser.add_argument("--output-dir", "-o", default="./output", help="输出目录")
    gen_parser.add_argument("--prompt", "-p", help="自定义提示词（跳过AI生成）")
    gen_parser.add_argument("--gemini-key", help="Gemini API Key")
    gen_parser.add_argument("--ark-key", help="火山引擎 Ark API Key")

    # server 命令
    server_parser = subparsers.add_parser("server", help="启动Web服务")
    server_parser.add_argument("--port", "-p", type=int, default=8088, help="端口号")
    server_parser.add_argument("--reload", "-r", action="store_true", help="热重载模式")

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出历史任务")
    list_parser.add_argument("--output-dir", "-o", default="./output", help="输出目录")
    list_parser.add_argument("--gemini-key", help="Gemini API Key")
    list_parser.add_argument("--ark-key", help="火山引擎 Ark API Key")
    list_parser.add_argument("--quality", default="medium")
    list_parser.add_argument("--format", default="glb")

    args = parser.parse_args()

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "server":
        cmd_server(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
