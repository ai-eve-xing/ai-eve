"""AI 夏娃 — 语音对话引擎"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from cli.main import load_config


def start_voice_chat():
    config = load_config()
    persona = config.get("persona", {})
    name = persona.get("name", "夏娃")

    print(f"\n🎤 AI 夏娃 — 语音对话模式")
    print("=" * 40)

    # 检查 ffmpeg
    import shutil
    if not shutil.which("ffmpeg"):
        print("⚠️  未找到 ffmpeg")
        print("   语音功能需要 ffmpeg 支持")
        print("   Ubuntu: sudo apt install ffmpeg")
        print("   macOS:  brew install ffmpeg")
        return

    voice_enabled = config.get("voice", {}).get("enabled", False)
    if not voice_enabled:
        print(f"⚠️  语音功能未启用")
        print(f"   运行 ai-eve setup 重新配置并启用语音")
        return

    print(f"\n  🎤 {name} 正在倾听...")
    print(f"  按 Ctrl+C 退出\n")

    # TODO: 完整的语音对话实现
    # - 录音 → ASR 转文字
    # - 文字 → LLM 回复
    # - 回复 → TTS 语音合成
    # - 播放语音
    print("  (语音功能开发中，敬请期待)")
    print("  当前可使用文字模式: ai-eve")
