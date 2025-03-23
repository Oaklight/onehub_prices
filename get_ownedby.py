import requests
import json


def get_channel_id_mapping():
    try:
        # 发送请求获取数据
        response = requests.get("https://oneapi.service.oaklight.cn/api/ownedby")
        response.raise_for_status()
        data = response.json()

        # 保存JSON数据到文件
        with open("ownedby.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    except requests.RequestException as e:
        print(f"请求出错: {e}")
    except (KeyError, ValueError) as e:
        print(f"解析数据出错: {e}")
    return {}

if __name__ == "__main__":
    get_channel_id_mapping()
