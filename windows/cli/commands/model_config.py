"""AI 夏娃 — 大模型配置命令"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from cli.main import load_config, save_config


PROVIDERS = {
    "1": ("deepseek", "DeepSeek", "https://api.deepseek.com", "deepseek-chat"),
    "2": ("qwen", "通义千问 (阿里云)", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
    "3": ("openai", "OpenAI", "https://api.openai.com/v1", "gpt-4o-mini"),
    "4": ("openrouter", "OpenRouter", "https://openrouter.ai/api/v1", "deepseek/deepseek-chat"),
    "5": ("ollama", "Ollama (本地)", "http://localhost:11434/v1", "qwen2.5:7b"),
}


def configure_model():
    config = load_config()

    print("\n🤖 AI 夏娃 — 大模型配置")
    print("=" * 40)

    current = config.get("model", {})
    if current.get("provider"):
        print(f"\n当前配置: {current['provider']} / {current.get('name', '未设置')}")
        change = input("\n是否修改? (Y/n): ").strip().lower()
        if change == "n":
            return

    print("\n选择模型供应商:")
    for k, (_, name, _, _) in PROVIDERS.items():
        print(f"  {k}) {name}")

    choice = input("\n请选择 [1]: ").strip() or "1"
    provider_info = PROVIDERS.get(choice)
    if not provider_info:
        print("无效选择")
        return

    provider, label, default_url, default_model = provider_info

    print(f"\n配置 {label}:")

    api_key = input(f"  API Key: ").strip()
    base_url = input(f"  API 地址 [{default_url}]: ").strip() or default_url
    model_name = input(f"  模型名称 [{default_model}]: ").strip() or default_model

    config["model"] = {
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
        "name": model_name,
    }

    save_config(config)
    print(f"\n✅ 模型配置完成！")
    print(f"   供应商: {label}")
    print(f"   模型: {model_name}")
    print(f"\n现在运行 ai-eve 即可开始对话")
