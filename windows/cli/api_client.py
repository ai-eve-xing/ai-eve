"""AI 夏娃 — API 客户端（模型调用层）"""
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# Token 审计日志路径
TOKEN_LOG_DIR = Path.home() / ".ai-eve" / "data" / "logs"
TOKEN_LOG_PATH = TOKEN_LOG_DIR / "token_usage.jsonl"


def _log_token_usage(model: str, prompt_tokens: int, completion_tokens: int, total_tokens: int):
    """记录 token 用量到审计日志"""
    TOKEN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }
    with open(TOKEN_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def call_openai_compatible(base_url, api_key, model, messages):
    """调用 OpenAI 兼容接口"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    data = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 1024,
    }).encode("utf-8")

    # 修正 URL
    url = base_url.rstrip("/")
    if not url.endswith("/v1"):
        url += "/v1"
    url += "/chat/completions"

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        # 记录 token 用量（如果 API 返回了 usage 字段）
        usage = result.get("usage")
        if usage:
            _log_token_usage(
                model=model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )

        return result["choices"][0]["message"]["content"]

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return f"请求失败 (HTTP {e.code}): {error_body[:200]}"
    except urllib.error.URLError as e:
        return f"网络错误: {e.reason}"
    except json.JSONDecodeError:
        return "响应解析失败"
