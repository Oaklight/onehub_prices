import json
import os

from _vendor.dotenv import load_dotenv

from utils import (
    SCALE_FACTOR_CNY,
    fetch_and_sort_models,
    integrate_prices,
    round_to_five,
    yaml_to_json,
)


def extract_specific_price(model_pricing, specification):
    """
    Retrieves and converts the price for a specific specification from the pricing data.

    Parameters:
    model_pricing (list): List of pricing details as dictionaries.
    specification (str): The specification to filter by (e.g., "completion" or "prompt").

    Returns:
    float: The price as a float, or None if the specification is not found.
    """
    return float(
        next(
            (
                item["price"]
                for item in model_pricing
                if item["specification"] == specification
            ),
            None,
        )
    )


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file

    api_key: str = os.getenv("SILICONFLOW_API_KEY")
    assert api_key is not None, "SILICONFLOW_API_KEY is not set"

    url = "https://busy-bear.siliconflow.cn"  # Note: Removed 'https://' as http.client needs the host part
    endpoint = "/api/v1/playground/comprehensive/all"
    headers = {"Authorization": f"Bearer {api_key}"}

    siliconflow_channel_type: int = 45  # reference https://your-oneapi-url/api/ownedby

    model_json = fetch_and_sort_models(url, endpoint, headers, mode="siliconflow")

    # Filter out disabled/deprecated models
    active_models = [m for m in model_json if m.get("status") != "disable"]
    print(
        f"SiliconFlow: {len(model_json)} total, {len(model_json) - len(active_models)} disabled, {len(active_models)} active"
    )

    processed_prices = []
    for model in active_models:
        model_name = model["modelName"]
        model_pricing = model["pricing"]
        model_price_unit = model["priceUnit"]

        if model_price_unit == "/ M Tokens" and len(model_pricing) == 2:
            completion_price = extract_specific_price(model_pricing, "completion")
            prompt_price = extract_specific_price(model_pricing, "prompt")
            print(
                f"Model Name: {model_name}, Completion Price: {completion_price} {model_price_unit}, Prompt Price: {prompt_price} {model_price_unit}",
                flush=True,
            )
            price_data = {
                "model": model_name,
                "type": "tokens",
                "channel_type": siliconflow_channel_type,
                "input": round_to_five(prompt_price / 1000 / SCALE_FACTOR_CNY),
                "output": round_to_five(completion_price / 1000 / SCALE_FACTOR_CNY),
            }

        else:
            model_price = float(model["price"])

            if model_price_unit in ["/ M Tokens", "/ M UTF-8 bytes", "/ M px / Steps"]:
                price_data = {
                    "model": model_name,
                    "type": "tokens",
                    "channel_type": siliconflow_channel_type,
                    "input": round_to_five(model_price / 1000 / SCALE_FACTOR_CNY),
                    "output": round_to_five(model_price / 1000 / SCALE_FACTOR_CNY),
                }
                print(
                    f"Model Name: {model_name}, Completion Price: {model_price} {model_price_unit}, Prompt Price: {model_price} {model_price_unit}"
                )
            elif model_price_unit in ["/ Video", "/ Image", ""]:
                price_data = {
                    "model": model_name,
                    "type": "times",
                    "channel_type": siliconflow_channel_type,
                    "input": round_to_five(model_price),
                    "output": round_to_five(model_price),
                }
                print(
                    f"Model Name: {model_name}, Pricing: {model_price} {model_price_unit}"
                )
            else:
                raise ValueError(f"Unknown price unit: {model_price_unit}")

        processed_prices.append(price_data)
        print("-" * 40)

    # Load and convert manual_prices/Siliconflow.yaml
    manual_prices = yaml_to_json("manual_prices", "Siliconflow.yaml")

    # Integrate manual prices and siliconflow_prices
    integrated_prices = integrate_prices(manual_prices, {"data": processed_prices})

    # 保存集成后的价格数据
    with open("siliconflow_prices.json", "w", encoding="utf-8") as f:
        json.dump(integrated_prices, f, ensure_ascii=False, indent=2)
