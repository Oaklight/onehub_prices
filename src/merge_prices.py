import argparse
import json

import httpclient

from utils import integrate_prices, yaml_to_json

UPSTREAM_URL = "https://raw.githubusercontent.com/MartialBE/one-api/prices/prices.json"


def filter_onehub_only_prices(prices: dict) -> dict:
    """
    Filter prices to only include suppliers with id <= 1000.

    Args:
        prices (dict): Dictionary containing price data.

    Returns:
        dict: Filtered price data.
    """
    return {
        "data": [
            item
            for item in prices["data"]
            if isinstance(item["channel_type"], int) and item["channel_type"] <= 1000
        ]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge pricing data from all sources.")
    parser.add_argument(
        "--no-upstream",
        action="store_true",
        default=True,
        help="Skip fetching upstream MartialBE prices (default: skip)",
    )
    parser.add_argument(
        "--upstream",
        action="store_true",
        help="Fetch and merge upstream MartialBE prices",
    )
    args = parser.parse_args()
    use_upstream = args.upstream  # only fetch when explicitly requested

    # 加载所有手工定价表格
    yaml_dir_path = "manual_prices"
    integrated_manual_prices = yaml_to_json(yaml_dir_path)

    # 加载所有自动定价表格
    # 读取 siliconflow_prices.json 和 openrouter_prices.json 文件
    try:
        with open("siliconflow_prices.json", "r", encoding="utf-8") as file:
            siliconflow_prices = json.load(file)
    except FileNotFoundError:
        print("未找到 siliconflow_prices.json 文件，将跳过 siliconflow 价格。")
        siliconflow_prices = {"data": []}

    try:
        with open("openrouter_prices.json", "r", encoding="utf-8") as file:
            openrouter_prices = json.load(file)
    except FileNotFoundError:
        print("未找到 openrouter_prices.json 文件，将跳过 openrouter 价格。")
        openrouter_prices = {"data": []}

    # 集成手动价格、siliconflow_prices 和 openrouter_prices
    integrated_prices = integrate_prices(integrated_manual_prices, siliconflow_prices)
    integrated_prices = integrate_prices(integrated_prices, openrouter_prices)

    # 获取上游 MartialBE 的价格（仅在 --upstream 时）
    if use_upstream:
        try:
            response = httpclient.get(UPSTREAM_URL)
            response.raise_for_status()
            upstream_prices = {"data": response.json()}
            print(f"已获取上游价格: {len(upstream_prices['data'])} 条")
        except httpclient.HttpClientError as e:
            print(f"获取上游价格出错: {e}")
            upstream_prices = {"data": []}
        # 集成上游价格，手动价格优先
        integrated_prices = integrate_prices(integrated_prices, upstream_prices)
    else:
        print("已跳过上游 MartialBE 价格（默认行为，使用 --upstream 开启）")

    final_prices = integrated_prices

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
