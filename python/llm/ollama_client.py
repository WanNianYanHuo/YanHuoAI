import json
import requests
from config.settings import (
    LLM_BACKEND,
    OLLAMA_MODEL,
    OLLAMA_URL,
    OLLAMA_TIMEOUT,
    ZHIPU_API_KEY,
    ZHIPU_MODEL
)

def _ns_to_s(ns):
    """纳秒转秒，保留 3 位小数。"""
    if ns is None:
        return None
    return round(ns / 1e9, 3)


# ========== Ollama ==========
def _call_ollama(prompt: str, stream_callback=None, on_complete=None, temperature: float = None) -> str:
    """
    Ollama 调用：流式请求。stream_callback(chunk_text) 每段回调；结束时 on_complete(timing_dict) 带回耗时等数据。
    temperature: 可选，≤1.0，如 0.3 用于结构化输出。
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
    }
    if temperature is not None and 0 <= temperature <= 2:
        payload["options"] = {"temperature": temperature}
    resp = None
    try:
        resp = requests.post(
            OLLAMA_URL,
            json=payload,
            stream=True,
            timeout=OLLAMA_TIMEOUT
        )
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"无法连接 Ollama（{OLLAMA_URL}）。请确认：1) 本机已启动 Ollama（ollama serve 或桌面版）；"
            f"2) 若 Ollama 在其它机器，请修改 config/settings.py 中的 OLLAMA_URL。"
        ) from e
    except requests.exceptions.HTTPError as e:
        if resp is not None and getattr(resp, "status_code", None) == 404:
            raise RuntimeError(
                f"模型 '{OLLAMA_MODEL}' 未找到。请先拉取：ollama pull {OLLAMA_MODEL}"
            ) from e
        raise RuntimeError(f"Ollama 请求失败：{e}") from e
    except Exception as e:
        raise RuntimeError(f"Ollama 调用失败：{e}") from e

    parts = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            chunk = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(chunk, dict) and "error" in chunk:
            raise RuntimeError(f"Ollama 返回错误：{chunk['error']}")
        if chunk.get("done"):
            if on_complete:
                timing = {
                    "total_s": _ns_to_s(chunk.get("total_duration")),
                    "load_s": _ns_to_s(chunk.get("load_duration")),
                    "prompt_eval_count": chunk.get("prompt_eval_count"),
                    "prompt_eval_s": _ns_to_s(chunk.get("prompt_eval_duration")),
                    "eval_count": chunk.get("eval_count"),
                    "eval_s": _ns_to_s(chunk.get("eval_duration")),
                    "done_reason": chunk.get("done_reason"),
                }
                on_complete(timing)
            break
        text = chunk.get("response")
        if text:
            parts.append(text)
            if stream_callback:
                stream_callback(text)
    return "".join(parts).strip()


# ========== ZhipuAI ==========
def _call_zhipu(prompt: str, stream_callback=None, on_complete=None, temperature=None) -> str:
    """
    智谱 API 调用。若提供 stream_callback 则走流式（与 Ollama 一致，便于前端逐字显示）；
    否则一次性返回全文。
    """
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
        "Content-Type": "application/json"
    }
    temp = 0.3
    if temperature is not None and 0 <= temperature <= 2:
        temp = temperature
    payload = {
        "model": ZHIPU_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temp,
        "stream": bool(stream_callback),
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120, stream=bool(stream_callback))
        resp.raise_for_status()
    except Exception as e:
        print("Zhipu 调用失败：", e)
        return ""

    if not stream_callback:
        try:
            return (resp.json().get("choices") or [{}])[0].get("message", {}).get("content") or ""
        except Exception:
            return ""

    # 流式：智谱 v4 与 OpenAI 兼容，按行返回 data: {...}，choices[0].delta.content
    parts = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.strip():
            continue
        line = line.strip()
        if line.startswith("data:"):
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            choices = (obj or {}).get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            text = delta.get("content") or ""
            if not text:
                continue
            parts.append(text)
            stream_callback(text)
    if on_complete:
        on_complete({})
    return "".join(parts).strip()


# ========== Unified API ==========
def call_llm(prompt: str, stream_callback=None, on_complete=None, backend=None, temperature=None) -> str:
    """
    统一大模型调用接口。backend 为 None 时使用 config 中的 LLM_BACKEND；可传 "ollama" | "zhipu" 覆盖。
    temperature: 可选，用于 CoT 等需稳定输出时建议 ≤0.3。
    """
    back = (backend or LLM_BACKEND).strip().lower()
    if back == "ollama":
        return _call_ollama(
            prompt,
            stream_callback=stream_callback,
            on_complete=on_complete,
            temperature=temperature,
        )
    elif back == "zhipu":
        return _call_zhipu(
            prompt,
            stream_callback=stream_callback,
            on_complete=on_complete,
            temperature=temperature,
        )
    else:
        return ""
