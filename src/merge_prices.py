import json
import os
import sys

import requests

_current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.extend([_current_dir])

from utils import yaml_to_json, integrate_prices


if __name__ == "__main__":
    # 加载所有手工定价表格
    yaml_dir_path = "manual_prices"
    integrated_manual_prices = yaml_to_json(yaml_dir_path)
    # 读取 siliconflow_prices.json 文件
    try:
        with open("siliconflow_prices.json", "r", encoding="utf-8") as file:
            siliconflow_prices = json.load(file)
    except FileNotFoundError:
        print("未找到 siliconflow_prices.json 文件，将使用手动价格作为最终结果。")
        siliconflow_prices = {"data": []}

    # 集成手动价格和 siliconflow_prices
    integrated_prices = integrate_prices(integrated_manual_prices, siliconflow_prices)

    # 获取 provider 的价格
    try:
        response = requests.get(
            "https://raw.githubusercontent.com/MartialBE/one-api/prices/prices.json"
        )
        response.raise_for_status()
        provider_prices = {"data": response.json()}
    except requests.RequestException as e:
        print(f"获取 provider 价格出错: {e}")
        provider_prices = {"data": []}

    # 集成 provider 的价格，确保手动价格优先
    final_prices = integrate_prices(integrated_prices, provider_prices)

    def filter_onehub_only_prices(prices):
        """Filter prices to only include suppliers with id <= 1000"""
        return {
            "data": [
                item
                for item in prices["data"]
                if isinstance(item["channel_type"], int)
                and item["channel_type"] <= 1000
            ]
        }

    # 将集成后的价格数据保存到 oneapi_prices.json 文件
    with open("oneapi_prices.json", "w", encoding="utf-8") as file:
        json.dump(final_prices, file, indent=2, ensure_ascii=False)

    # 生成 onehub_only_prices.json 文件
    onehub_only_prices = filter_onehub_only_prices(final_prices)
    with open("onehub_only_prices.json", "w", encoding="utf-8") as file:
        json.dump(onehub_only_prices, file, indent=2, ensure_ascii=False)

    print(
        "已将集成后的价格数据保存到 oneapi_prices.json 和 onehub_only_prices.json 文件。"
    )
