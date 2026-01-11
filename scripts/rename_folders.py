#!/usr/bin/env python3
"""
重命名脚本 - 将 hash 命名的 3D 模型文件夹重命名为语义化名称

用法:
    python scripts/rename_folders.py --data-dir ./data/3d_models [--dry-run]
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# 尝试导入 LLM 相关库
try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


def is_hash_folder(name: str) -> bool:
    """检查文件夹名是否是 hash 格式（8位十六进制）"""
    return bool(re.match(r'^[0-9a-f]{8}$', name.lower()))


def generate_folder_name_with_llm(description: str, api_key: str) -> Optional[str]:
    """使用 LLM 从描述生成语义化文件夹名"""
    if not HAS_GENAI:
        return None

    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""根据以下设备描述，生成一个简洁的英文文件夹名。

要求:
- 使用小写英文
- 使用下划线分隔
- 格式: {{设备类型}}_{{规格或电压等级}}
- 不要有空格或特殊字符
- 长度控制在30字符以内

设备描述: {description}

只输出文件夹名，不要其他内容:"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        folder_name = response.text.strip().lower()
        folder_name = re.sub(r'[^a-z0-9_]', '_', folder_name)
        folder_name = re.sub(r'_+', '_', folder_name).strip('_')

        return folder_name[:30] if folder_name else None
    except Exception as e:
        print(f"  LLM 生成失败: {e}")
        return None


def generate_folder_name_from_description(description: str) -> str:
    """从描述中提取关键信息生成文件夹名（不使用 LLM）"""
    equipment_map = {
        '变压器': 'transformer',
        '断路器': 'circuit_breaker',
        '隔离开关': 'disconnector',
        '电流互感器': 'current_transformer',
        '电压互感器': 'voltage_transformer',
        '互感器': 'transformer',
        '电容器': 'capacitor',
        '电抗器': 'reactor',
        '避雷器': 'arrester',
        '绝缘子': 'insulator',
        '母线': 'busbar',
        '接地': 'grounding',
        '控制柜': 'control_cabinet',
        'GIS': 'gis',
        '开关设备': 'switchgear',
        '电缆终端': 'cable_termination',
        '构架': 'structure',
        '机器人': 'robot',
        '椅子': 'chair',
        '桌子': 'table',
    }

    voltage_pattern = r'(\d+)\s*kV|(\d+)\s*千伏'
    voltage_match = re.search(voltage_pattern, description, re.IGNORECASE)
    voltage = f"_{voltage_match.group(1) or voltage_match.group(2)}kv" if voltage_match else ""

    equipment_type = None
    for cn_name, en_name in equipment_map.items():
        if cn_name in description:
            equipment_type = en_name
            break

    if not equipment_type:
        words = re.findall(r'[a-zA-Z]+', description.lower())
        equipment_type = '_'.join(words[:2]) if words else 'model'

    folder_name = f"{equipment_type}{voltage}"
    return folder_name


def create_metadata(folder_path: Path, folder_name: str, description: str):
    """创建 metadata.json 文件"""
    metadata = {
        "display_name": description[:50],
        "folder_name": folder_name,
        "description": description,
        "equipment_type": None,
        "voltage_level": None,
        "domain": "power_grid",
        "created_at": datetime.now().isoformat(),
        "migrated_at": datetime.now().isoformat()
    }

    prompt_file = folder_path / "prompt.json"
    if prompt_file.exists():
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_data = json.load(f)
                metadata["domain"] = prompt_data.get("detected_domain", "power_grid")
                metadata["style"] = prompt_data.get("style", "photorealistic")
        except Exception:
            pass

    metadata_file = folder_path / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return metadata_file


def rename_hash_folders(data_dir: Path, dry_run: bool = False, use_llm: bool = False, api_key: str = None):
    """重命名所有 hash 命名的文件夹"""
    if not data_dir.exists():
        print(f"目录不存在: {data_dir}")
        return

    folders_to_process = []
    for folder in data_dir.iterdir():
        if folder.is_dir() and is_hash_folder(folder.name):
            prompt_file = folder / "prompt.json"
            if prompt_file.exists():
                folders_to_process.append(folder)
            else:
                print(f"跳过 {folder.name}: 没有 prompt.json")

    print(f"\n找到 {len(folders_to_process)} 个需要重命名的文件夹\n")

    renamed_count = 0
    for folder in folders_to_process:
        prompt_file = folder / "prompt.json"
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_data = json.load(f)
                description = prompt_data.get('description', '')
        except Exception as e:
            print(f"读取 {folder.name}/prompt.json 失败: {e}")
            continue

        if not description:
            print(f"跳过 {folder.name}: description 为空")
            continue

        if use_llm and api_key:
            new_name = generate_folder_name_with_llm(description, api_key)
            if not new_name:
                new_name = generate_folder_name_from_description(description)
        else:
            new_name = generate_folder_name_from_description(description)

        target_path = data_dir / new_name
        if target_path.exists():
            suffix = folder.name[:4]
            new_name = f"{new_name}_{suffix}"
            target_path = data_dir / new_name

        print(f"{folder.name} -> {new_name}")
        print(f"  描述: {description[:60]}...")

        if not dry_run:
            try:
                create_metadata(folder, new_name, description)
                folder.rename(target_path)
                renamed_count += 1
                print(f"  ✓ 重命名成功")
            except Exception as e:
                print(f"  ✗ 重命名失败: {e}")
        else:
            print(f"  [dry-run] 将重命名")

        print()

    print(f"\n完成! 已重命名 {renamed_count}/{len(folders_to_process)} 个文件夹")


def main():
    parser = argparse.ArgumentParser(description='重命名 hash 命名的 3D 模型文件夹')
    parser.add_argument('--data-dir', type=str, default='./data/3d_models',
                        help='3D 模型数据目录')
    parser.add_argument('--dry-run', action='store_true',
                        help='预览模式，不实际执行重命名')
    parser.add_argument('--use-llm', action='store_true',
                        help='使用 LLM 生成文件夹名称')
    parser.add_argument('--api-key', type=str,
                        help='Gemini API Key')

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    api_key = args.api_key or os.environ.get('GEMINI_API_KEY')

    if args.use_llm and not api_key:
        print("警告: --use-llm 需要提供 API Key")
        args.use_llm = False

    print("=" * 60)
    print("Model Forge - 文件夹重命名工具")
    print("=" * 60)
    print(f"数据目录: {data_dir}")
    print(f"预览模式: {args.dry_run}")
    print(f"使用 LLM: {args.use_llm}")

    rename_hash_folders(data_dir, args.dry_run, args.use_llm, api_key)


if __name__ == '__main__':
    main()
