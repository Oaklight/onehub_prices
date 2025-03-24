import os
import requests
import json

import yaml


def get_channel_id_mapping(save_to_file=False):
    try:
        # 发送请求获取数据
        response = requests.get("https://oneapi.service.oaklight.cn/api/ownedby")
        response.raise_for_status()
        data = response.json()

        if save_to_file:
            # 保存JSON数据到文件
            with open("ownedby.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            mapping = {}
            for key, value in data["data"].items():
                mapping[value["name"]] = int(key)
            return mapping

    except requests.RequestException as e:
        print(f"请求出错: {e}")
    except (KeyError, ValueError) as e:
        print(f"解析数据出错: {e}")
    return {}


def load_yaml_from_directory(directory_path, file_name=None):
    """从目录中加载并合并 YAML 文件，同时处理重复项，并确保 'oaklight-load-balancer.yaml' 最后应用。
    如果传入 file_name 参数，则只处理该文件。
    """
    yaml_data = {"models": {}}
    special_file = "oaklight-load-balancer.yaml"

    # 如果提供了 file_name，则只处理这个文件
    if file_name:
        file_path = os.path.join(directory_path, file_name)
        with open(file_path, "r", encoding="utf-8") as file:
            file_data = yaml.safe_load(file)
        if "models" in file_data:
            yaml_data["models"] = file_data["models"]
        return yaml_data

    # 原有逻辑，只处理目录中的所有 YAML 文件
    files_to_process = []

    # 收集除特殊文件之外的所有 yaml 文件
    for filename in os.listdir(directory_path):
        if filename.endswith(".yaml") and filename != special_file:
            files_to_process.append(filename)

    # 排序以确保覆盖顺序一致
    files_to_process.sort()

    # 如果存在特殊文件，则把它放在最后处理
    if special_file in os.listdir(directory_path):
        files_to_process.append(special_file)

    # 处理收集到的每个文件
    for filename in files_to_process:
        file_path = os.path.join(directory_path, filename)
        with open(file_path, "r", encoding="utf-8") as file:
            file_data = yaml.safe_load(file)
            if "models" in file_data:
                for channel, models in file_data["models"].items():
                    if channel in yaml_data["models"]:
                        # 更新已存在的模型，覆盖重复项
                        for model_name, model_info in models.items():
                            yaml_data["models"][channel][model_name] = model_info
                    else:
                        yaml_data["models"][channel] = models

    return yaml_data


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


def yaml_to_json(directory_path, file_name=None):
    """将目录中的 YAML 数据转换为 JSON 格式，同时处理别名和价格转换。
    如果指定 file_name，则只处理该 YAML 文件。
    """

    def create_model_entry(
        model_name, model_type, channel_type, input_price, output_price
    ):
        """创建模型条目字典。"""
        return {
            "model": model_name,
            "type": model_type,
            "channel_type": channel_type,
            "input": input_price,
            "output": output_price,
        }

    # 根据 file_name 参数加载 YAML 数据
    yaml_data = load_yaml_from_directory(directory_path, file_name)

    # 获取渠道 ID 映射关系
    channel_id_mapping = get_channel_id_mapping()

    json_data = {"data": []}

    # 遍历每个渠道及其模型
    for channel_type, models in yaml_data["models"].items():
        new_channel_type = channel_id_mapping.get(channel_type, channel_type)
        if new_channel_type is None:
            print(f"未找到 {channel_type} 对应的渠道 ID，将保留原始值。")

        # 遍历每个模型及其信息
        for model_name, model_info in models.items():
            # 转换价格
            input_price = convert_price(str(model_info["input"]))
            output_price = convert_price(str(model_info["output"]))

            # 获取模型类型（如果未指定，则默认为 "tokens"）
            model_type = model_info.get("type", "tokens")

            # 添加主模型条目
            json_data["data"].append(
                create_model_entry(
                    model_name, model_type, new_channel_type, input_price, output_price
                )
            )

            # 如果存在别名，则为每个别名添加条目
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
