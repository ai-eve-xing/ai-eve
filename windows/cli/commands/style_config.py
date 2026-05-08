"""AI 夏娃 — 视觉风格配置"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from cli.main import load_config, save_config, AVATAR_DIR


def configure_style():
    config = load_config()

    print("\n🎨 AI 夏娃 — 视觉风格配置")
    print("=" * 40)

    current = config.get("persona", {})
    current_style = current.get("style", "realistic")

    print(f"\n当前风格: {style_display(current_style)}")
    print(f"  她的名字: {current.get('name', '夏娃')}")
    print(f"  性格: {current.get('personality', '温柔、知性')}")
    print()

    styles = {
        "1": ("realistic", "写实风格", "接近真人照片的写实画风"),
        "2": ("anime", "二次元/动漫", "日系动漫风格的可爱形象"),
        "3": ("minimalist", "抽象极简", "线条简洁的抽象设计"),
    }

    print("可选风格:")
    for k, (_, name, desc) in styles.items():
        marker = " ◀ 当前" if name == style_display(current_style) else ""
        print(f"  {k}) {name} — {desc}{marker}")

    choice = input(f"\n请选择 [{current_style[0] if current_style in ['realistic','anime','minimalist'] else '1'}]: ").strip()
    style_info = styles.get(choice)
    if not style_info:
        style_info = styles["1"]

    style_key, style_name, _ = style_info

    # 更新
    if "persona" not in config:
        config["persona"] = {}
    config["persona"]["style"] = style_key

    save_config(config)
    print(f"\n✅ 视觉风格已切换为: {style_name}")
    print(f"  现在运行 ai-eve 即可体验新形象\n")

    # 提示更换头像
    avatar_dir = AVATAR_DIR / style_key
    if avatar_dir.exists():
        files = list(avatar_dir.glob("*.*"))
        if files:
            print(f"  可用头像: {len(files)} 个")
            print(f"  头像目录: {avatar_dir}")
    else:
        print(f"  提示: 可将头像文件放入 {avatar_dir}")


def style_display(style_key):
    mapping = {"realistic": "写实风格", "anime": "二次元/动漫", "minimalist": "抽象极简"}
    return mapping.get(style_key, style_key)
