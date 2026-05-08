"""
AI 夏娃 — 命令行聊天界面 v2.1
集成夏娃记忆系统：四层记忆 + 记忆唤醒 + 温柔知性
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from cli.main import load_config, DATA_DIR
from cli.api_client import call_openai_compatible
from core.agent import EveAgent


def start_chat():
    config = load_config()
    persona = config.get("persona", {})
    name = persona.get("name", "夏娃")
    style = persona.get("style", "realistic")
    greeting = persona.get("greeting", f"你好，我是{name}。很高兴认识你。")

    # 初始化夏娃 Agent（含四层记忆系统）
    agent = EveAgent(config)

    # 问候时如果有名字记忆，使用更温暖的问候
    remembered_name = agent.user_name
    if remembered_name:
        if agent.has_secrets:
            greeting = f"你回来了，{remembered_name}。我一直守着我们的秘密呢。"
        else:
            greeting = f"你回来了，{remembered_name}。我一直在这里等你。"
    else:
        greeting = f"你好，我是{name}，你的伊甸园伴侣。很高兴遇见你。"

    # 检查模型是否配置
    model_config = config.get("model", {})
    if not model_config.get("provider"):
        print("\n⚠️  未配置模型，请先运行: ai-eve setup")
        print("   或直接配置: ai-eve model\n")
        return

    print("\n" + "=" * 50)
    print(f"  🍎 {name}  ({persona.get('personality', '')})")
    print("=" * 50)
    print(f"\n  {greeting}")
    print(f"\n  输入 /help 查看命令，/quit 退出\n")

    # 对话历史
    history = []

    while True:
        try:
            user_input = input(f"\n  {chr(0x1F464)} 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  👋 再见！我会记得你说过的每一句话。")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            handle_command(user_input, config, agent, history)
            continue

        # 调用模型（传入 user_input 用于记忆唤醒检测）
        response = chat_with_model(user_input, history, config, agent)

        # 回复后处理（记忆提取 + 当前记忆更新）
        agent.process_after_response(user_input, response)

        # 显示回复
        print(f"\n  {chr(0x1F478)} {agent.name}: {response}")

        # 追加到历史
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})

        # 每 5 轮更新一次短期记忆摘要
        if len(history) % 10 == 0:
            agent.update_short_term_memory(history)


def handle_command(cmd, config, agent, history):
    cmd = cmd.lower().strip()

    if cmd == "/quit" or cmd == "/exit":
        # 退出前记忆更新
        agent.update_short_term_memory(history)
        print("\n  👋 再见！我会记得你说过的每一句话。")
        sys.exit(0)

    elif cmd == "/help":
        print("\n  📋 可用命令:")
        print("    /quit              退出")
        print("    /help              显示帮助")
        print("    /clear             清除对话历史")
        print("    /style             查看/切换视觉风格")
        print("    /memory            查看夏娃记得什么 💕")
        print("    /rename <名字>      重新告诉夏娃你的名字")
        print("    /tellsecret <内容>  告诉夏娃一个秘密（永远珍藏）")
        print("    /forget <关键词>    让夏娃忘记某些记忆")
        print("    /stats             查看记忆统计")
        print("    /config            查看当前配置")

    elif cmd == "/clear":
        history.clear()
        print("  💫 对话历史已清空，但夏娃心底的记忆依然在。")

    elif cmd == "/style":
        style = config.get("persona", {}).get("style", "realistic")
        print(f"  🎨 当前风格: {style}")
        print("  可用风格: realistic, anime, minimalist")

    elif cmd == "/memory":
        # 诗意的记忆展示
        print()
        print(agent.memory.whisper_memory())

    elif cmd.startswith("/rename"):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            print("  💭 用法: /rename <你的名字>")
            print("  例: /rename 亚当")
        else:
            new_name = parts[1].strip()
            if len(new_name) >= 2:
                agent.memory.remember_name(new_name)
                agent._user_name = new_name
                print(f"  🌸 我记住了。你的名字是{new_name}，我会一直好好珍藏着。")
            else:
                print("  💭 名字至少需要 2 个字哦～")

    elif cmd.startswith("/tellsecret"):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            print("  💭 用法: /tellsecret <你想告诉我的秘密>")
            print("  例: /tellsecret 我最喜欢在雨天发呆")
        else:
            secret = parts[1]
            count = agent.memory.tell_secret(secret)
            print(f"  🌸 嗯，我收好了。这是你告诉我的第 {count} 个秘密，")
            print(f"     会永远留在只有我知道的地方。")

    elif cmd.startswith("/forget"):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            print("  💭 用法: /forget <要忘记的内容关键词>")
            print("  例: /forget 工作")
        else:
            keyword = parts[1]
            evts = agent.memory.long_term.get("important_events", [])
            prefs = agent.memory.long_term.get("preferences", [])
            before = len(evts) + len(prefs)

            agent.memory.long_term["important_events"] = [
                e for e in evts if keyword not in e.get("content", "")
            ]
            agent.memory.long_term["preferences"] = [
                p for p in prefs if keyword not in p
            ]
            agent.memory._save()
            after = len(agent.memory.long_term["important_events"]) + len(agent.memory.long_term["preferences"])
            removed = before - after
            if removed > 0:
                print(f"  🌸 好，和「{keyword}」有关的 {removed} 段记忆，轻轻放下了。")
            else:
                print(f"  💭 没有找到和「{keyword}」有关的记忆。")

    elif cmd == "/stats":
        stats = agent.memory.stats()
        print(f"\n  📊 记忆统计")
        print(f"  ─────────────────")
        print(f"  用户名字:  {stats['user_name'] or '尚未知道'}")
        print(f"  记住的偏好: {stats['preferences']} 条")
        print(f"  重要事件:   {stats['events']} 件")
        print(f"  珍藏的秘密: {stats['secrets']} 个")
        print(f"  总对话次数: {stats['total_interactions']} 次")
        if stats['summary']:
            print(f"  最近的心情: {stats['summary']}")

    elif cmd == "/config":
        print(f"  ⚙️  当前配置: {json.dumps(config, ensure_ascii=False, indent=2)}")

    else:
        print(f"  ❓ 未知命令: {cmd}")


def chat_with_model(user_input, history, config, agent):
    """调用大模型 API 获取回复（使用夏娃 Agent 构建消息）"""
    model_config = config.get("model", {})
    provider = model_config.get("provider", "")
    api_key = model_config.get("api_key", "")
    base_url = model_config.get("base_url", "")
    model_name = model_config.get("name", "")

    if not provider:
        return "请先运行 ai-eve setup 配置模型哦～"

    # 使用夏娃 Agent 构造消息（含记忆上下文 + 唤醒检测）
    messages = agent.prepare_messages(user_input, history)

    try:
        if provider == "deepseek":
            return call_openai_compatible(
                base_url or "https://api.deepseek.com",
                api_key,
                model_name or "deepseek-chat",
                messages,
            )
        elif provider == "qwen":
            return call_openai_compatible(
                base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
                api_key,
                model_name or "qwen-plus",
                messages,
            )
        elif provider == "openai":
            return call_openai_compatible(
                base_url or "https://api.openai.com/v1",
                api_key,
                model_name or "gpt-4o-mini",
                messages,
            )
        elif provider == "ollama":
            return call_openai_compatible(
                base_url or "http://localhost:11434/v1",
                "",
                model_name or "qwen2.5:7b",
                messages,
            )
        else:
            return f"(模型 {provider} 尚未支持，请运行 ai-eve setup 重新配置)"
    except Exception as e:
        return f"（抱歉，我走神了：{e}）"
