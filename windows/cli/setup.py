"""AI 夏娃 — 配置向导"""
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from cli.main import load_config, save_config, DATA_DIR


def run_setup_wizard():
    print("\n" + "=" * 50)
    print("   🍎 AI 夏娃 — 配置向导")
    print("=" * 50 + "\n")

    config = load_config() or {}

    # ── 1. 人物设定 ──
    print("📝 【第一步】人物设定")
    print("-" * 40)

    name = input(f"  她的名字 [夏娃]: ").strip() or "夏娃"
    eng_name = input(f"  英文名 [Eve]: ").strip() or "Eve"

    print("\n  性格特征（可多选，逗号分隔）:")
    print("    1) 温柔体贴  2) 知性优雅  3) 活泼开朗")
    print("    4) 成熟御姐  5) 俏皮可爱  6) 高冷知性")
    personality_input = input("  请选择 (如 1,3,5) [1,2]: ").strip() or "1,2"
    personality_map = {
        "1": "温柔体贴",
        "2": "知性优雅",
        "3": "活泼开朗",
        "4": "成熟御姐",
        "5": "俏皮可爱",
        "6": "高冷知性",
    }
    selected = []
    for p in personality_input.split(","):
        p = p.strip()
        if p in personality_map:
            selected.append(personality_map[p])
    personality = "、".join(selected) if selected else "温柔、知性"

    greeting = input(f"\n  开场白 ['你好，我是{name}。很高兴认识你。']: ").strip()
    if not greeting:
        greeting = f"你好，我是{name}。很高兴认识你。"

    # ── 2. 视觉风格 ──
    print("\n🎨 【第二步】视觉风格")
    print("-" * 40)
    print("  1) 写实风格  (Realistic)")
    print("  2) 二次元/动漫  (Anime)")
    print("  3) 抽象极简  (Minimalist)")
    style_choice = input("  请选择 [1]: ").strip() or "1"
    style_map = {"1": "realistic", "2": "anime", "3": "minimalist"}
    style = style_map.get(style_choice, "realistic")

    # ── 3. 大模型配置 ──
    print("\n🤖 【第三步】大模型配置")
    print("-" * 40)
    print("  支持的供应商:")
    print("    1) DeepSeek （推荐，性价比高）")
    print("    2) 通义千问 (阿里云)")
    print("    3) OpenAI")
    print("    4) OpenRouter （聚合多模型）")
    print("    5) Ollama （本地模型）")
    print("    6) 跳过，稍后配置")

    provider_choice = input("  请选择 [1]: ").strip() or "1"
    provider_map = {
        "1": ("deepseek", "https://api.deepseek.com"),
        "2": ("qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        "3": ("openai", "https://api.openai.com/v1"),
        "4": ("openrouter", "https://openrouter.ai/api/v1"),
        "5": ("ollama", "http://localhost:11434/v1"),
        "6": ("", ""),
    }

    provider_info = provider_map.get(provider_choice, ("", ""))
    provider = provider_info[0]
    base_url = provider_info[1]

    api_key = ""
    model_name = ""

    if provider:
        api_key = input(f"  API Key (留空稍后配置): ").strip()
        model_name = input(f"  模型名称 (留空使用默认): ").strip()

    # ── 4. 平台接入 ──
    print("\n📱 【第四步】平台接入")
    print("-" * 40)
    platforms = {"telegram": False, "discord": False, "wechat": False, "feishu": False}
    for p_name, p_label in [("telegram", "Telegram"), ("discord", "Discord"),
                             ("wechat", "微信"), ("feishu", "飞书")]:
        ans = input(f"  是否接入 {p_label}? (y/N): ").strip().lower()
        platforms[p_name] = ans == "y"

    # ── 5. 记忆与语音 ──
    print("\n🧠 【第五步】高级功能")
    print("-" * 40)
    memory_ans = input("  启用持久记忆? (Y/n): ").strip().lower()
    memory_enabled = memory_ans != "n"

    voice_ans = input("  启用语音对话? (需要 ffmpeg, y/N): ").strip().lower()
    voice_enabled = voice_ans == "y"

    # ── 保存配置 ──
    config.update({
        "version": "0.1.0",
        "persona": {
            "name": name,
            "english_name": eng_name,
            "style": style,
            "personality": personality,
            "greeting": greeting,
        },
        "model": {
            "provider": provider,
            "api_key": api_key,
            "base_url": base_url,
            "name": model_name,
        },
        "voice": {
            "enabled": voice_enabled,
            "provider": "",
            "voice_id": "",
        },
        "platforms": {k: {"enabled": v} for k, v in platforms.items()},
        "memory": {
            "enabled": memory_enabled,
            "type": "local",
        },
        "data_dir": str(DATA_DIR),
    })

    save_config(config)

    print("\n" + "=" * 50)
    print("   ✅ 配置完成！")
    print("=" * 50)
    print(f"\n  现在运行 ai-eve 即可开始对话")
    print(f"  或运行 ai-eve web 启动 Web 界面\n")


if __name__ == "__main__":
    run_setup_wizard()
