"""
AI 夏娃 (AI Eve) — 入口模块
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 确保在正确的目录
INSTALL_DIR = Path.home() / ".ai-eve"
DATA_DIR = INSTALL_DIR / "data"
CONFIG_DIR = DATA_DIR / "config"
LOG_DIR = DATA_DIR / "logs"
MEMORY_DIR = DATA_DIR / "memory"
AVATAR_DIR = DATA_DIR / "avatars"


def get_config_path():
    return CONFIG_DIR / "config.json"


def load_config():
    config_path = get_config_path()
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}


def save_config(config):
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        prog="ai-eve",
        description="🍎 AI 夏娃 (AI Eve) — 你的专属 AI 伴侣",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
命令:
  setup         交互式配置向导
  model         配置大模型
  style         设置视觉风格
  web           启动 Web UI
  voice         启动语音对话
  token         查看 Token 消耗统计
  update        更新到最新版本
  help          显示此帮助

快速开始:
  ai-eve setup     # 首次配置
  ai-eve           # 启动对话
        """,
    )
    parser.add_argument("command", nargs="?", default="chat", help="子命令")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="子命令参数")

    args = parser.parse_args()

    # 确保数据目录存在
    for d in [DATA_DIR, CONFIG_DIR, LOG_DIR, MEMORY_DIR, AVATAR_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    command_map = {
        "setup": cmd_setup,
        "model": cmd_model,
        "style": cmd_style,
        "web": cmd_web,
        "voice": cmd_voice,
        "token": cmd_token,
        "chat": cmd_chat,
        "update": cmd_update,
        "help": lambda _: parser.print_help(),
    }

    cmd_func = command_map.get(args.command)
    if cmd_func:
        cmd_func(args.args)
    else:
        print(f"未知命令: {args.command}")
        parser.print_help()


def cmd_setup(_):
    """交互式配置向导"""
    from cli.setup import run_setup_wizard
    run_setup_wizard()


def cmd_model(_):
    """配置大模型"""
    from cli.commands.model_config import configure_model
    configure_model()


def cmd_style(_):
    """设置视觉风格"""
    from cli.commands.style_config import configure_style
    configure_style()


def cmd_web(_):
    """启动 Web UI"""
    from ui.web.server import start_web_server
    start_web_server()


def cmd_voice(_):
    """启动语音对话"""
    from ui.voice.engine import start_voice_chat
    start_voice_chat()


def cmd_token(_):
    """查看 Token 消耗统计"""
    from cli.commands.token_stats import show_token_stats
    show_token_stats()


def cmd_chat(_):
    """启动 CLI 对话"""
    from cli.commands.chat import start_chat
    start_chat()


def cmd_update(_):
    """更新到最新版本"""
    import subprocess
    print("正在检查更新...")
    repo_dir = INSTALL_DIR / "repo"
    if repo_dir.exists():
        result = subprocess.run(
            ["git", "pull", "--ff-only", "origin", "main"],
            cwd=str(repo_dir),
            capture_output=True, text=True,
        )
        print(result.stdout)
        if "Already up to date" in result.stdout:
            print("✅ 已是最新版本")
        else:
            print("✅ 更新完成，请重新启动 ai-eve")
    else:
        print("❌ 未找到仓库目录，请重新安装")


if __name__ == "__main__":
    main()
