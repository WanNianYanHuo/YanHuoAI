# -*- coding: utf-8 -*-
"""
从本地 Ollama 端口拉取模型（默认 deepseek-v3.1:671b-cloud）
需先启动 Ollama 服务，默认地址 http://127.0.0.1:11434
原位置: test/pull_ollama_qwen.py，已整合至 python/scripts
"""
import json
import sys

DEFAULT_BASE = "http://127.0.0.1:11434"
MODEL_NAME = "deepseek-v3.1:671b-cloud"


def pull_model(base_url=DEFAULT_BASE, model=MODEL_NAME, stream=True):
    url = f"{base_url.rstrip('/')}/api/pull"
    try:
        import requests
    except ImportError:
        print("请先安装: pip install requests", flush=True)
        return False
    payload = {"model": model, "stream": stream}
    print(f"正在从 {base_url} 拉取模型: {model}", flush=True)
    print("-" * 50, flush=True)
    try:
        # 连接超时 10 秒，读超时 2 小时（大模型下载时间长）
        r = requests.post(url, json=payload, stream=stream, timeout=(10, 7200))
        r.raise_for_status()
        if stream:
            for line in r.iter_lines(decode_unicode=True):
                if line:
                    try:
                        d = json.loads(line)
                        status = d.get("status", "")
                        completed = d.get("completed")
                        total = d.get("total")
                        if total is not None and completed is not None:
                            pct = (completed / total * 100) if total else 0
                            print(f"  {status}  {completed}/{total} ({pct:.1f}%)", flush=True)
                        else:
                            print(f"  {status}", flush=True)
                        if status == "success":
                            break
                    except json.JSONDecodeError:
                        print(line, flush=True)
        else:
            print(json.dumps(r.json(), indent=2, ensure_ascii=False), flush=True)
        print("-" * 50, flush=True)
        print("拉取完成。可用: ollama run " + model.split(":")[0], flush=True)
        return True
    except requests.exceptions.ConnectionError:
        print("无法连接 Ollama，请确认已启动: ollama serve 或 Ollama 桌面版", flush=True)
        return False
    except Exception as e:
        print(f"拉取失败: {e}", flush=True)
        return False


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE
    model = sys.argv[2] if len(sys.argv) > 2 else MODEL_NAME
    ok = pull_model(base, model)
    input("\n按回车键退出...")
    sys.exit(0 if ok else 1)
