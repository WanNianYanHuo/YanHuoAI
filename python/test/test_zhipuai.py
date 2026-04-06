import requests

ZHIPU_API_KEY = "423f6cd5e21943c196f6899d1a496665.wsWjaFurFniStfj2"
ZHIPU_MODEL = "glm-4-flash"

def test_zhipu():
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": ZHIPU_MODEL,
        "messages": [
            {"role": "user", "content": "请用一句话说明什么是中医目诊。"}
        ],
        "temperature": 0.3
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)

    print("HTTP 状态码:", resp.status_code)
    resp.raise_for_status()

    data = resp.json()
    print("模型返回内容：")
    print(data["choices"][0]["message"]["content"])


if __name__ == "__main__":
    test_zhipu()
