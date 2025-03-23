import json
import os

import requests
import yaml


def convert_price(price_str):
    # 初始化价格和缩放因子
    price = 0
    scale_factor = 1

    # 检查价格字符串中是否包含 "usd"
    if "usd" in price_str:
        scale_factor = 0.002
        price = float(
            price_str.replace("usd", "")
            .replace("/", "")
            .replace("M", "")
            .replace("K", "")
            .strip()
        )
        # 如果价格字符串中包含 "M"，将价格除以1000000
        if "M" in price_str:
            price = price / 1000
        # 如果价格字符串中包含 "K"，将价格除以1000
        elif "K" in price_str:
            price = price
    # 检查价格字符串中是否包含 "rmb"
    elif "rmb" in price_str:
        scale_factor = 0.014
        price = float(
            price_str.replace("rmb", "")
            .replace("/", "")
            .replace("M", "")
            .replace("K", "")
            .strip()
        )
        # 如果价格字符串中包含 "M"，将价格除以1000000
        if "M" in price_str:
            price = price / 1000
        # 如果价格字符串中包含 "K"，将价格除以1000
        elif "K" in price_str:
            price = price
    else:
        price = float(price_str)
    # 返回根据缩放因子调整后的价格
    return price / scale_factor


def get_channel_id_mapping():
    try:
        # 发送请求获取数据
        response = requests.get("https://oneapi.service.oaklight.cn/api/ownedby")
        response.raise_for_status()
        data = response.json()
        mapping = {}
        for key, value in data["data"].items():
            mapping[value["name"]] = int(key)
        return mapping
    except requests.RequestException as e:
        print(f"请求出错: {e}")
    except (KeyError, ValueError) as e:
        print(f"解析数据出错: {e}")
    return {}


def load_yaml_from_directory(directory_path):
    """Load and merge YAML files from a directory, handling duplicates.
    Ensures 'oaklight-load-balancer.yaml' is applied last."""
    yaml_data = {"models": {}}
    special_file = "oaklight-load-balancer.yaml"
    files_to_process = []

    # Collect all YAML files except the special one
    for filename in os.listdir(directory_path):
        if filename.endswith(".yaml") and filename != special_file:
            files_to_process.append(filename)

    # Sort files to ensure consistent overwriting
    files_to_process.sort()

    # Process the special file last
    if special_file in os.listdir(directory_path):
        files_to_process.append(special_file)

    # Process each file
    for filename in files_to_process:
        file_path = os.path.join(directory_path, filename)
        with open(file_path, "r", encoding="utf-8") as file:
            file_data = yaml.safe_load(file)
            if "models" in file_data:
                for channel, models in file_data["models"].items():
                    if channel in yaml_data["models"]:
                        # Update existing models, overwriting duplicates
                        for model_name, model_info in models.items():
                            yaml_data["models"][channel][model_name] = model_info
                    else:
                        yaml_data["models"][channel] = models

    return yaml_data


def yaml_to_json(directory_path):
    """Convert YAML data from directory to JSON format, handling aliases and price conversions."""

    def create_model_entry(
        model_name, model_type, channel_type, input_price, output_price
    ):
        """Create a model entry dictionary."""
        return {
            "model": model_name,
            "type": model_type,
            "channel_type": channel_type,
            "input": input_price,
            "output": output_price,
        }

    # Load YAML data from directory
    yaml_data = load_yaml_from_directory(directory_path)

    # Get channel ID mapping
    channel_id_mapping = get_channel_id_mapping()

    json_data = {"data": []}

    # Iterate over each channel and its models
    for channel_type, models in yaml_data["models"].items():
        new_channel_type = channel_id_mapping.get(channel_type, channel_type)
        if new_channel_type is None:
            print(f"未找到 {channel_type} 对应的渠道 ID，将保留原始值。")

        # Iterate over each model and its info
        for model_name, model_info in models.items():
            # Convert prices
            input_price = convert_price(str(model_info["input"]))
            output_price = convert_price(str(model_info["output"]))

            # Get the model type (default to "tokens" if not specified)
            model_type = model_info.get("type", "tokens")

            # Add the main model entry
            json_data["data"].append(
                create_model_entry(
                    model_name, model_type, new_channel_type, input_price, output_price
                )
            )

            # Add entries for each alias (if aliases exist)
            if "aliases" in model_info:
                aliases = model_info["aliases"].split(", ")
                for alias in aliases:
                    json_data["data"].append(
                        create_model_entry(
                            alias.strip(),
                            model_type,
                            new_channel_type,
                            input_price,
                            output_price,
                        )
                    )

    return json_data


# Function to sort the prices list based on channel_type (primary) and model (secondary)
def sort_prices(prices):
    print(prices)
    prices["data"] = sorted(
        prices["data"], key=lambda x: (x["channel_type"], x["model"])
    )
    return prices


# Updated integrate_prices function to include sorting
def integrate_prices(primary_prices, secondary_prices):
    # 创建一个字典，用于快速查找 primary_prices 中的条目，键为 (model, channel_type) 元组
    primary_dict = {
        (item["model"], item["channel_type"]): item for item in primary_prices["data"]
    }

    # 遍历 secondary_prices 中的每个条目
    for secondary_item in secondary_prices["data"]:
        key = (secondary_item["model"], secondary_item["channel_type"])
        if key not in primary_dict:
            # 如果 primary_prices 中没有该条目，则添加 secondary_prices 的条目
            primary_prices["data"].append(secondary_item)

    # 对合并后的价格进行排序
    return sort_prices(primary_prices)


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
