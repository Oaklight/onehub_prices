#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建新provider的脚本
用法: python scripts/new_provider.py "Provider Name" [--series 1000|2000]
"""

import argparse
import json
import re
import sys
from pathlib import Path


def sanitize_filename(name):
    """将provider名称转换为合法的文件名"""
    # 移除或替换不合法的字符
    sanitized = re.sub(r'[<>:"/\\|?*]', "", name)
    # 替换多个空格为单个空格
    sanitized = re.sub(r"\s+", " ", sanitized)
    return sanitized.strip()


def get_next_id(ownedby_file, series):
    """获取下一个可用的ID"""
    with open(ownedby_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if series == 1000:
        # 1000系列：1000-1999
        ids = [int(k) for k in data["data"].keys() if 1000 <= int(k) < 2000]
        return max(ids) + 1 if ids else 1000
    elif series == 2000:
        # 2000系列：2000-2999
        ids = [int(k) for k in data["data"].keys() if 2000 <= int(k) < 3000]
        return max(ids) + 1 if ids else 2000
    else:
        raise ValueError(f"不支持的系列: {series}")


def create_yaml_template(provider_name):
    """创建YAML模板"""
    template = f"""models:
  {provider_name}:
    # 模型价格：请填写官方价格页面链接
    
    # 示例模型配置
    example-model:
      input: 0.1 usd / M
      output: 0.2 usd / M
      # aliases:
      #   - example-model-alias
      # extra_ratios:
      #   - cached_tokens: 0.05 usd / M
    
    # 请根据实际情况添加更多模型配置
"""
    return template


def update_ownedby_manual(ownedby_file, provider_name, new_id):
    """更新ownedby_manual.json文件"""
    with open(ownedby_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 添加新的provider条目
    data["data"][str(new_id)] = {
        "id": new_id,
        "name": provider_name,
        "icon": "",  # 用户需要手动填写图标URL
    }

    # 按ID排序data字典，但保持每个entry内部结构不变
    sorted_data = {}
    for key in sorted(data["data"].keys(), key=lambda x: int(x)):
        sorted_data[key] = data["data"][key]

    data["data"] = sorted_data

    # 写回文件，保持格式，确保最后一行是空行
    with open(ownedby_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")  # 确保文件以空行结尾


def main():
    parser = argparse.ArgumentParser(description="创建新的provider")
    parser.add_argument("name", help="Provider名称")
    parser.add_argument(
        "--series",
        type=int,
        choices=[1000, 2000],
        help="ID序列选择: 1000=公开provider, 2000=私人/小众provider",
    )

    args = parser.parse_args()

    provider_name = args.name.strip()

    if not provider_name:
        print("错误: Provider名称不能为空")
        sys.exit(1)

    # 如果没有指定系列，询问用户
    if args.series is None:
        print("请选择ID序列:")
        print("  1000 - 公开provider (商业AI服务商)")
        print("  2000 - 私人/小众provider (自建或小众服务)")
        while True:
            try:
                choice = input("请输入选择 (1000/2000): ").strip()
                if choice == "1000":
                    series = 1000
                    break
                elif choice == "2000":
                    series = 2000
                    break
                else:
                    print("请输入 1000 或 2000")
            except KeyboardInterrupt:
                print("\n操作已取消")
                sys.exit(1)
    else:
        series = args.series

    # 项目根目录
    project_root = Path(__file__).parent.parent

    # 文件路径
    ownedby_file = project_root / "ownedby_manual.json"
    manual_prices_dir = project_root / "manual_prices"

    # 确保目录存在
    manual_prices_dir.mkdir(exist_ok=True)

    # 生成文件名
    yaml_filename = sanitize_filename(provider_name) + ".yaml"
    yaml_file = manual_prices_dir / yaml_filename

    # 检查文件是否已存在
    if yaml_file.exists():
        print(f"错误: 文件 {yaml_file} 已存在")
        sys.exit(1)

    try:
        # 获取下一个ID
        new_id = get_next_id(ownedby_file, series)

        # 创建YAML文件
        yaml_content = create_yaml_template(provider_name)
        with open(yaml_file, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        # 更新ownedby_manual.json
        update_ownedby_manual(ownedby_file, provider_name, new_id)

        series_desc = "公开provider" if series == 1000 else "私人/小众provider"
        print("✅ 成功创建新provider:")
        print(f"   名称: {provider_name}")
        print(f"   ID: {new_id} ({series_desc})")
        print(f"   YAML文件: {yaml_file}")
        print(f"   已更新: {ownedby_file}")
        print()
        print("📝 下一步:")
        print(f"   1. 编辑 {yaml_file} 添加实际的模型配置")
        print(f"   2. 在 {ownedby_file} 中为ID {new_id} 添加图标URL")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
