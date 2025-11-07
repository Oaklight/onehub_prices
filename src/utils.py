import json
import os
from typing import Dict, List, Literal, Tuple

import requests
import yaml

SCALE_FACTOR_CNY = 0.014
SCALE_FACTOR_USD = 0.002


def round_to_five(num: float) -> float:
    """Round number to 5 decimal places for better precision display."""
    return round(num * 100000) / 100000


def fetch_and_sort_models(
    url: str,
    endpoint: str,
    headers: dict[str, str],
    mode: Literal["siliconflow", "openrouter"],
) -> dict:
    """
    Fetches models from the given URL and sorts them by modelName.

    Parameters:
    url (str): The base URL for the HTTPS connection.
    endpoint (str): The endpoint to send the GET request to.
    headers (dict): Dictionary containing any necessary headers.
    mode (Literal): The mode, either "siliconflow" or "openrouter".

    Returns:
    list: A sorted list of models based on modelName.

    Raises:
    requests.ConnectionError: If the connection fails.
    json.JSONDecodeError: If the response body cannot be decoded into JSON.
    requests.exceptions.RequestException: For other HTTP errors.
    """
    try:
        response = requests.get(f"{url}{endpoint}", headers=headers)
        response.raise_for_status()  # Raise exception for HTTP error responses
        body = response.text

        if mode == "siliconflow":
            model_json = json.loads(body)["data"]["models"]
            model_json = sorted(model_json, key=lambda x: x["modelName"])
        else:
            model_json = json.loads(body)["data"]

        return model_json

    except requests.ConnectionError as e:
        raise requests.ConnectionError(f"Failed to connect to {url}: {e}")

    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Failed to decode JSON response: {e}", doc=e.doc, pos=e.pos
        )

    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"An HTTP error occurred: {e}")


def get_channel_id_mapping(save_to_file: bool = False) -> Dict:
    """
    Fetches channel ID mapping data from an external API, optionally saves it to a file,
    and returns a processed mapping.

    Parameters:
    save_to_file (bool): Whether to save the sorted data to a JSON file.

    Returns:
    dict: A mapping of channel names to IDs.

    Raises:
    requests.RequestException: For API request errors.
    KeyError, ValueError: For errors while processing the data.
    """
    try:
        # Fetch data from the API
        response = requests.get("https://oneapi.service.oaklight.cn/api/ownedby")
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        if save_to_file:
            # Sort data by key and prepare for saving
            sorted_data = {
                str(k): v
                for k, v in sorted(data["data"].items(), key=lambda item: int(item[0]))
            }
            result = {"data": sorted_data}

            # Save the processed JSON data to a file
            with open("ownedby.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        else:
            # Create a mapping from the retrieved data
            mapping = {}
            for key, value in data.get("data", {}).items():
                mapping[value["name"]] = int(key)
            return mapping

    except requests.ConnectionError as e:
        raise requests.ConnectionError(f"Connection error occurred: {e}")
    except requests.RequestException as e:
        raise requests.RequestException(f"HTTP request error: {e}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"JSON parsing error: {e}", doc=e.doc, pos=e.pos)
    except (KeyError, ValueError) as e:
        raise RuntimeError(f"Data processing error: {e}") from e


def load_yaml_from_directory(directory_path: str, file_name: str = None) -> dict:
    """
    Load and merge YAML files from a directory, handling duplicates and ensuring
    'oaklight-load-balancer.yaml' is applied last. If `file_name` is provided,
    only process that file.

    Args:
        directory_path (str): Path to the directory containing YAML files.
        file_name (str, optional): Specific file name to process.

    Returns:
        dict: Merged YAML data.
    Raises:
        FileNotFoundError: If the specified file_name does not exist.
    """
    yaml_data = {"models": {}}
    special_file = "oaklight-load-balancer.yaml"

    # 如果提供了 file_name，则只处理这个文件
    if file_name:
        file_path = os.path.join(directory_path, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"The specified file '{file_name}' does not exist in the directory: {directory_path}"
            )
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
        print(f"Processing file: {filename}")  # Debug print
        file_path = os.path.join(directory_path, filename)
        with open(file_path, "r", encoding="utf-8") as file:
            file_data = yaml.safe_load(file)
            if "models" in file_data:
                for channel, models in file_data["models"].items():
                    # 如果模型列表为空，跳过更新
                    if not models:
                        print(f"Skipping empty model list for channel: {channel}")
                        continue
                    if channel in yaml_data["models"]:
                        # 更新已存在的模型，覆盖重复项
                        for model_name, model_info in models.items():
                            yaml_data["models"][channel][model_name] = model_info
                    else:
                        yaml_data["models"][channel] = models

    # print(yaml_data["models"]["OpenRouter"])
    return yaml_data


def split_price_string(price_str: str) -> Tuple[float, str]:
    """
    Split a price string into numeric part and text part.

    Examples:
    - "10 usd" → (10.0, "usd")
    - "5.5 rmb / M" → (5.5, "rmb / M")
    - "100 /image" → (100.0, "/image")

    :param price_str: The input price string
    :return: Tuple of (numeric_value, text_part)
    """
    import re

    match = re.match(r"^([\d.]+)\s*(.*)$", price_str.strip())
    if not match:
        raise ValueError(f"Invalid price format: {price_str}")
    return (float(match.group(1)), match.group(2))


def convert_price(price_str: str) -> Tuple[float, str]:
    """
    Converts a price string into a normalized numerical value and its price type.

    Supported Formats:
    - "<value> usd"
    - "<value> usd / M"
    - "<value> usd / K"
    - "<value> rmb"
    - "<value> rmb / M"
    - "<value> rmb / K"

    Conversion Details:
    - Currency:
      - USD: Normalized directly using SCALE_FACTOR_USD.
      - RMB: Converted to normalized USD units using SCALE_FACTOR_CNY.
    - Units:
      - "/M": Values are divided by 1,000,000 to normalize.
      - "/K": Values are divided by 1,000 to normalize.

    Pricing Types:
    - "tokens": Represented by unit-based formats like '/M' or '/K'.
    - "times": Used where no unit-based suffix is present.

    Examples:
    - "100 usd" -> (100.0, "times")
    - "200 rmb / M" -> (normalized_float_value, "tokens")

    Parameters:
        price_str (str): The price string to parse and convert.

    Returns:
        Tuple[float, str]: A tuple containing the rounded normalized price value
                           (to three decimal places) and its price type.

    Raises:
        ValueError: If the input string format is invalid.
    """
    # Split into numeric value and text part
    try:
        numeric_value, text_part = split_price_string(price_str)
    except ValueError:
        raise ValueError(f"Invalid price format: {price_str}")

    text_part = text_part.lower()

    # Determine currency scale factor
    if "rmb" in text_part:
        scale_factor = SCALE_FACTOR_CNY
    else:  # Default to USD
        scale_factor = SCALE_FACTOR_USD

    # Determine division factor and price type
    if "/m" in text_part or "/ m" in text_part:
        division_factor = 1_000
        price_type = "tokens"
    elif "/k" in text_part or "/ k" in text_part:
        division_factor = 1
        price_type = "tokens"
    elif text_part:  # text_part exists and doesn't contain /m or /k
        division_factor = 1
        price_type = "times"
    else:  # text_part is empty, by default we take it as tokens type
        division_factor = 1
        price_type = "tokens"

    # Normalize the price and round to three decimal places
    normalized_price = numeric_value / (division_factor * scale_factor)
    return normalized_price, price_type


def process_extra_ratios(
    extra_ratios: list, input_price: float, output_price: float
) -> dict:
    """
    处理extra_ratios字段，转换为指定格式的字典

    Args:
        extra_ratios: YAML中的extra_ratios列表
        input_price: 模型的input/output价格(用于计算比率)
        output_price: 模型的input/output价格(用于计算比率)

    Returns:
        转换后的extra_ratios字典
    """
    if input_price == 0:
        input_price = 1  # 避免除以零错误
    if output_price == 0:
        output_price = 1  # 避免除以零错误

    result = {}
    for item in extra_ratios:
        for key, value in item.items():
            # 判断是否有单位
            if isinstance(value, str) and (
                "usd" in value.lower() or "rmb" in value.lower()
            ):
                # 带单位的情况，先convert_price再计算比率
                normalized_price, _ = convert_price(value)
                if "output" in key:
                    ratio = normalized_price / output_price
                else:
                    ratio = normalized_price / input_price

            else:
                # 不带单位的情况，直接使用
                ratio = float(value)
            result[key] = round_to_five(ratio)
    return result


def create_model_entry(
    model_name, model_type, channel_type, input_price, output_price, extra_ratios=None
):
    """创建模型条目字典。"""
    entry = {
        "model": model_name,
        "type": model_type,
        "channel_type": channel_type,
        "input": round_to_five(input_price),
        "output": round_to_five(output_price),
    }
    if extra_ratios:
        entry["extra_ratios"] = process_extra_ratios(
            extra_ratios, input_price, output_price
        )
    return entry


def yaml_to_json(directory_path: str, file_name: str = None) -> dict:
    """
    Convert YAML data in a directory to JSON format, handling aliases and price conversion.
    If `file_name` is specified, only process that YAML file.

    Args:
        directory_path (str): Path to the directory containing YAML files.
        file_name (str, optional): Specific file name to process.

    Returns:
        dict: Converted JSON data.
    """

    # 根据 file_name 参数加载 YAML 数据
    yaml_data = load_yaml_from_directory(directory_path, file_name)

    # 获取渠道 ID 映射关系
    channel_id_mapping = get_channel_id_mapping()

    json_data = {"data": []}

    # 遍历每个渠道及其模型
    for channel_type, models in yaml_data["models"].items():
        new_channel_type = channel_id_mapping.get(channel_type, channel_type)
        if new_channel_type is None:
            print(f"[manual pricing] 未找到 {channel_type} 对应的渠道 ID，将保留原始值。")

        if models is None or len(models) == 0:
            print(f"[manual pricing] 渠道 {channel_type} 没有模型，跳过。")
            continue
        # 遍历每个模型及其信息
        for model_name, model_info in models.items():
            # 转换价格（处理可能缺失的input/output字段）
            input_price, input_price_type = (
                convert_price(str(model_info["input"]))
                if "input" in model_info
                else (0, "times")
            )
            output_price, output_price_type = (
                convert_price(str(model_info["output"]))
                if "output" in model_info
                else (0, "times")
            )

            if (input_price != 0 and input_price_type == "times") or (
                output_price != 0 and output_price_type == "times"
            ):
                model_type_default = "times"
            else:
                model_type_default = "tokens"

            # 如果模型提供了type，则使用模型信息。否则使用默认值。
            model_type = model_info.get("type", model_type_default)

            # 添加主模型条目
            json_data["data"].append(
                create_model_entry(
                    model_name,
                    model_type,
                    new_channel_type,
                    input_price,
                    output_price,
                    model_info.get("extra_ratios", None),
                )
            )

            # 如果存在别名，则为每个别名添加条目
            if "aliases" in model_info:
                aliases = model_info["aliases"]
                # 兼容旧格式（逗号分隔字符串）和新格式（列表）
                if isinstance(aliases, str):
                    aliases = [alias.strip() for alias in aliases.split(",")]
                for alias in aliases:
                    json_data["data"].append(
                        create_model_entry(
                            alias.strip(),
                            model_type,
                            new_channel_type,
                            input_price,
                            output_price,
                            # 确保别名也包含额外的比率信息
                            model_info.get("extra_ratios", None),
                        )
                    )

    return json_data


# Function to sort the prices list based on channel_type (primary) and model (secondary)
def sort_prices(prices: dict) -> dict:
    prices["data"] = sorted(
        prices["data"], key=lambda x: (x["channel_type"], x["model"])
    )
    return prices


# Updated integrate_prices function to include sorting
def integrate_prices(primary_prices: dict, secondary_prices: dict) -> dict:
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
