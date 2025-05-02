import http.client
import json
import os

import dotenv

from utils import integrate_prices, yaml_to_json

dotenv.load_dotenv()  # Load environment variables from .env file

api_key: str = os.getenv("SILICONFLOW_API_KEY")
assert api_key is not None, "SILICONFLOW_API_KEY is not set"

url = "busy-bear.siliconflow.cn"  # Note: Removed 'https://' as http.client needs the host part
endpoint = "/api/v1/playground/comprehensive/all"
headers = {"Authorization": f"Bearer {api_key}"}

siliconflow_channel_type: int = 45  # reference https://your-oneapi-url/api/ownedby

conn = http.client.HTTPSConnection(url)
conn.request("GET", endpoint, headers=headers)

response = conn.getresponse()
print(response.status)

body = response.read().decode("utf-8")
model_json = json.loads(body)["data"]["models"]

# Sort models by modelName to maintain consistent ordering
model_json = sorted(model_json, key=lambda x: x["modelName"])

with open("siliconflow_models.json", "w", encoding="utf-8") as f:
    json.dump(model_json, f, ensure_ascii=False, indent=4)

siliconflow_price_json = []
for model in model_json:
    model_name = model["modelName"]
    model_price = float(model["price"])
    model_price_unit = model["priceUnit"]
    print(f"Model Name: {model_name}, Price: {model_price} {model_price_unit}")
    scale_factor = 0.014
    if model_price_unit in ["/ M Tokens", "/ M UTF-8 bytes", "/ M px / Steps"]:
        price_data = {
            "model": model_name,
            "type": "tokens",
            "channel_type": siliconflow_channel_type,
            "input": model_price / 1000 / scale_factor,
            "output": model_price / 1000 / scale_factor,
        }
    elif model_price_unit in ["/ Video", "/ Image", ""]:
        print(f"special price unit: {model_price_unit}")

        price_data = {
            "model": model_name,
            "type": "times",
            "channel_type": siliconflow_channel_type,
            "input": model_price,
            "output": model_price,
        }
    siliconflow_price_json.append(price_data)
    print("-" * 40)

# 加载并转换 manual_prices/Siliconflow.yaml
manual_prices = yaml_to_json("manual_prices", "Siliconflow.yaml")

# 集成手动价格和 siliconflow_prices
integrated_prices = integrate_prices(manual_prices, {"data": siliconflow_price_json})

# 保存集成后的价格数据
with open("siliconflow_prices.json", "w", encoding="utf-8") as f:
    json.dump(integrated_prices, f, ensure_ascii=False, indent=2)
