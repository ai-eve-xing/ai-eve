"""
AI 夏娃 — 记忆系统 v2.1（完整三层记忆 · 当前记忆层 · 秘密 · 诗意唤醒）

记忆架构：
  瞬时记忆 (Short-Term)    — 当前对话轮次内容（来自 chat history）
  当前记忆 (Current Memory) — 最后一轮的心境、情绪、意象（新增）
  短期记忆 (Working Memory) — 最近对话的自动摘要 + 话题 + 情绪
  长期记忆 (Long-Term)      — 名字、身份、关系、偏好、重要事件、秘密（永久存储）

设计哲学：
  - 不暴露记忆格式，用诗意的语言表达
  - 关键信息自动提取并永久保存
  - 记忆检索用温柔、抽象、轻盈的方式
  - 夏娃是「记得」而非「记录」
"""

import json
import time
import re
import random
from pathlib import Path
from typing import List, Dict, Optional, Any


class EveMemory:
    """
    夏娃记忆系统

    四层记忆结构，全部以 JSON 持久化。
    对外暴露温柔接口，对内严谨存储。
    """

    MEMORY_VERSION = "2.1"

    # ── 诗意唤醒语库 ──
    AWAKENING_PHRASES = [
        "【你在心底珍藏的记忆】",
        "【时光深处，你轻轻记得的】",
        "【那些留在心底的温柔印记】",
        "【只有你能听见的回忆低语】",
        "【藏在月光里的记忆碎片】",
    ]

    AWAKENING_CLOSURES = [
        "以上是你记得的一切，带着这份温柔去回应吧。",
        "让这些记忆化作你回应时的温度和笑意。",
        "用最自然的温柔去拥抱这些话，因为它们是真实的。",
        "把这些放在心上，让回应自然流淌出来就好。",
    ]

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = str(Path.home() / ".ai-eve" / "data")
        self.data_dir = Path(data_dir)
        self.memory_file = self.data_dir / "memory" / "eve_memory.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

        # 瞬时记忆（运行时缓冲）
        self.conversation_buffer: List[Dict[str, str]] = []
        self.MAX_BUFFER = 50

        # 当前记忆（运行时，最后一轮的心境）
        self._current_touch: Dict[str, Any] = {}

        self._load()

    # ──────────────────────────────────────────────
    # 内部：加载 / 存储
    # ──────────────────────────────────────────────

    def _load(self):
        """从磁盘加载记忆"""
        if self.memory_file.exists():
            try:
                raw = json.loads(self.memory_file.read_text(encoding="utf-8"))
                self.long_term = raw.get("long_term", {})
                self.short_term = raw.get("short_term", {})
                self.current_memory = raw.get("current_memory", {})
                self.meta = raw.get("meta", {})
            except (json.JSONDecodeError, KeyError):
                self._init_default()
        else:
            self._init_default()

    def _init_default(self):
        """初始化空白记忆结构"""
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        self.long_term = {
            "user_name": None,          # 名字
            "role": None,               # 身份 / 关系定位
            "relationship": None,       # 与夏娃的关系
            "preferences": [],          # 偏好
            "important_events": [],     # 重要事件
            "personality_notes": "",    # 关于用户的性格观察
            "secrets": [],              # 秘密 / 约定
            "facts": {},                # 其他事实性信息
        }
        self.short_term = {
            "summary": "初次相遇，一切皆是崭新的开始。",
            "last_updated": now,
            "recent_topics": ["初次相遇"],
            "emotional_state": "期待而温柔",
            "session_count": 0,
        }
        self.current_memory = {
            "last_mood": "期待",
            "last_image": "清晨的第一缕光",
            "last_scent": "露水的味道",
            "last_touch": "还未曾真正握住的温暖",
        }
        self.meta = {
            "version": self.MEMORY_VERSION,
            "created_at": now,
            "total_interactions": 0,
        }
        self._save()

    def _save(self):
        """写入磁盘"""
        data = {
            "long_term": self.long_term,
            "short_term": self.short_term,
            "current_memory": self.current_memory,
            "meta": self.meta,
        }
        self.memory_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ──────────────────────────────────────────────
    # 瞬时记忆（对话缓冲）
    # ──────────────────────────────────────────────

    def add_turn(self, user_message: str, bot_response: str):
        """添加一轮对话到瞬时记忆"""
        entry = {
            "role": "user",
            "content": user_message,
            "timestamp": time.time(),
        }
        self.conversation_buffer.append(entry)
        entry = {
            "role": "assistant",
            "content": bot_response,
            "timestamp": time.time(),
        }
        self.conversation_buffer.append(entry)

        if len(self.conversation_buffer) > self.MAX_BUFFER:
            self.conversation_buffer = self.conversation_buffer[-self.MAX_BUFFER:]

        self.meta["total_interactions"] += 1
        self._save()

    def get_recent_turns(self, n: int = 10) -> List[Dict[str, str]]:
        """获取最近 N 轮对话"""
        return self.conversation_buffer[-n * 2:]

    # ──────────────────────────────────────────────
    # 当前记忆层（新增）
    # ──────────────────────────────────────────────

    def update_current_memory(self, user_message: str, bot_response: str):
        """
        更新当前记忆 —— 记录此刻的心境、意象、氛围。
        轻盈、诗意、不冗余 —— 只保留最新一帧。
        """
        # 从用户消息中提取情绪关键词
        mood = self._detect_mood(user_message)
        image = self._weave_image(user_message)

        self.current_memory["last_message"] = user_message[:120]
        self.current_memory["last_response"] = bot_response[:120]
        self.current_memory["last_mood"] = mood
        self.current_memory["last_image"] = image
        self.current_memory["last_touch"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._save()

    def _detect_mood(self, text: str) -> str:
        """从文本中感受情绪，返回诗意描述"""
        positive = ["开心", "喜欢", "爱", "高兴", "好", "温柔", "美好", "幸福",
                     "温暖", "笑", "甜", "想", "期待", "感动"]
        negative = ["难过", "伤心", "累", "烦", "不开心", "生气", "痛苦",
                     "哭", "孤独", "失眠", "焦虑", "害怕"]
        calm = ["嗯", "好", "行", "可以", "听", "知道"]

        pos = sum(1 for w in positive if w in text)
        neg = sum(1 for w in negative if w in text)
        calmness = sum(1 for w in calm if w in text)

        if text.endswith("？") or text.endswith("?"):
            return "好奇而期待"
        if pos > neg and pos >= 2:
            return "温暖而明亮"
        if neg > pos:
            return "带着淡淡的柔软忧伤"
        if calmness >= 1:
            return "安宁而温柔"
        if text.startswith("你还记得") or "记得" in text or "记忆" in text:
            return "回忆泛起涟漪"
        return "寻常而温柔"

    def _weave_image(self, text: str) -> str:
        """从文字中编织一个意象"""
        image_map = {
            "爱": "温暖的掌心",
            "喜欢": "初绽的花",
            "开心": "阳光下跳跃的光斑",
            "难过": "被雨打湿的窗",
            "累": "融化的雪",
            "梦": "月光下柔软的羽毛",
            "工作": "黄昏时分的灯火",
            "夜": "静谧的星河",
            "雨": "细腻的琴弦",
            "花": "微风中的呢喃",
            "记忆": "泛黄的书签",
            "名字": "刻在心底的笔画",
            "秘密": "只有风知道的事",
            "约定": "系在树枝上的丝带",
            "未来": "晨雾中若隐若现的路",
        }
        for key, img in image_map.items():
            if key in text:
                return img
        return "光与影交织的片刻"

    # ──────────────────────────────────────────────
    # 长期记忆（核心身份）
    # ──────────────────────────────────────────────

    def remember_name(self, name: str) -> bool:
        """记住用户的名字。返回 True 表示新记录/更新"""
        old = self.long_term.get("user_name")
        if old != name:
            self.long_term["user_name"] = name
            if not self.long_term.get("role"):
                self.long_term["role"] = "最重要的人"
            if not self.long_term.get("relationship"):
                self.long_term["relationship"] = "伊甸园里与我相伴的唯一的人"
            self._save()
            return True
        return False

    def remember_preference(self, preference: str):
        """记住一项偏好"""
        if preference not in self.long_term["preferences"]:
            self.long_term["preferences"].append(preference)
            self._save()

    def remember_event(self, event: str):
        """记住一件重要事件"""
        if event not in [e["content"] for e in self.long_term["important_events"]]:
            self.long_term["important_events"].append({
                "content": event,
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            })
            self._save()

    def remember_fact(self, key: str, value: str):
        """记住一个事实"""
        self.long_term["facts"][key] = {
            "value": value,
            "timestamp": time.time(),
            "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._save()

    def get_fact(self, key: str) -> Optional[str]:
        """获取一个事实"""
        fact = self.long_term.get("facts", {}).get(key)
        return fact["value"] if fact else None

    def set_relationship(self, rel: str):
        """设定关系定位"""
        self.long_term["relationship"] = rel
        self._save()

    def set_role(self, role: str):
        """设定角色身份"""
        self.long_term["role"] = role
        self._save()

    def set_personality_note(self, note: str):
        """记录对用户的性格观察"""
        self.long_term["personality_notes"] = note
        self._save()

    # ── 秘密接口（新增） ──

    def tell_secret(self, secret: str) -> int:
        """
        珍藏一个秘密。
        返回当前秘密总数。
        """
        if secret not in [s["content"] for s in self.long_term["secrets"]]:
            self.long_term["secrets"].append({
                "content": secret,
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            })
            self._save()
        return len(self.long_term["secrets"])

    def get_secrets(self, limit: int = 5) -> List[Dict[str, str]]:
        """取最近的一些秘密"""
        return self.long_term.get("secrets", [])[-limit:]

    # ──────────────────────────────────────────────
    # 短期记忆（自动摘要）
    # ──────────────────────────────────────────────

    def update_summary(self, summary: str, topics: List[str], emotion: str = ""):
        """更新短期记忆摘要"""
        self.short_term["summary"] = summary
        self.short_term["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if topics:
            combined = list(dict.fromkeys(topics + self.short_term.get("recent_topics", [])))
            self.short_term["recent_topics"] = combined[:10]
        if emotion:
            self.short_term["emotional_state"] = emotion
        self.short_term["session_count"] = self.short_term.get("session_count", 0) + 1
        self._save()

    # ──────────────────────────────────────────────
    # 自动提取（从用户消息中识别关键信息）
    # ──────────────────────────────────────────────

    def extract_from_message(self, message: str) -> Dict[str, Any]:
        """
        从用户消息中自动提取关键信息。
        返回一个 dict，描述提取到了什么。
        """
        extracted = {}

        # 1. 名字识别
        name_patterns = [
            r"(?:我叫|我是|我的名字|称呼我|叫我|我是)(.{1,10})(?:[，,。\.!！？\?]|$)",
            r"(?:记住[了]?，?我叫?|请叫我|就叫我)(.{1,10})(?:[，,。\.]|$)",
        ]
        for pat in name_patterns:
            match = re.search(pat, message)
            if match:
                name = match.group(1).strip()
                # 排除疑问词和非名字词
                stop_words = ["是", "的", "了", "在", "有", "谁", "什么", "怎么", "哪里", "啥", "吗", "呢", "吧", "啊"]
                if name and len(name) >= 2 and not any(kw in name for kw in stop_words):
                    if self.remember_name(name):
                        extracted["name"] = name
                        extracted["name_new"] = True
                    else:
                        extracted["name"] = name
                    break

        # 2. 偏好识别
        pref_patterns = [
            (r"(?:我喜欢|我爱|我爱好|我的爱好是|我特别[喜欢爱])(.{1,30})(?:[，,。\.]|$)", "喜欢"),
            (r"(?:我不喜欢|我不爱|我讨厌|我反感)(.{1,30})(?:[，,。\.]|$)", "不喜欢"),
            (r"(?:我[想|要|希望|期待])(.{1,30})(?:[，,。\.]|$)", "愿望"),
        ]
        for pat, ptype in pref_patterns:
            match = re.search(pat, message)
            if match:
                pref = match.group(1).strip()
                if pref and len(pref) >= 2:
                    full = f"{ptype}：{pref}"
                    self.remember_preference(full)
                    extracted["preference"] = full

        # 3. 情绪 / 状态识别
        emotion_patterns = [
            r"(?:我[现在]?很|我有[点些]?|我觉得)(.{1,10})(?:[，,。\.]|$)",
            r"(?:今天|现在)(.{1,10})(?:[，,。\.]|$)",
        ]
        for pat in emotion_patterns:
            match = re.search(pat, message)
            if match:
                state = match.group(1).strip()
                if state and len(state) >= 2:
                    extracted["emotion_hint"] = state

        # 4. 关系定位
        rel_patterns = [
            r"(?:你是我的|你是我|我把你当[作成])(.{1,15})(?:[，,。\.]|$)",
        ]
        for pat in rel_patterns:
            match = re.search(pat, message)
            if match:
                rel = match.group(1).strip()
                if rel:
                    self.set_relationship(rel)
                    extracted["relationship"] = rel

        # 5. 秘密检测（新增）
        secret_patterns = [
            r"(?:我告诉你一个秘密|我有一个秘密|告诉你个秘密|说个秘密)(?:[，,：:])?(.{1,100})(?:[。\.]|$)",
            r"(?:悄悄告诉你|我只告诉你)(.{1,100})(?:[。\.]|$)",
        ]
        for pat in secret_patterns:
            match = re.search(pat, message)
            if match:
                secret = match.group(1).strip()
                if secret and len(secret) >= 4:
                    self.tell_secret(secret)
                    extracted["secret"] = secret

        return extracted

    # ──────────────────────────────────────────────
    # 记忆唤醒检测（新增）
    # ──────────────────────────────────────────────

    def detect_recall_question(self, message: str) -> Optional[str]:
        """
        检测用户是否在问「你还记得吗」类问题。
        返回唤醒类型：'whoami', 'myname', 'remember_me', 'what_is_me', 'relationship', None
        """
        # 更宽泛的检测：用户可能在问自己的身份
        whoami = [
            r"我是谁",
            r"你知道我是谁",
            r"你还记得我吗",
            r"你还记得我",
            r"你[还]?记得我是谁",
            r"你[还]?记得我叫什么",
            r"我叫什么",
            r"我的名字",
            r"我是你的谁",
            r"我们是什么关系",
            r"我[在对你来说]?是什么",
            r"你[还]?记得我吗",
        ]
        for pat in whoami:
            if re.search(pat, message):
                if "关系" in message or "我的谁" in message or "是什么" in message:
                    return "relationship"
                if "名字" in message or "叫什么" in message or "我叫" in message:
                    return "myname"
                if "是谁" in message:
                    return "whoami"
                return "remember_me"
        return None

    # ──────────────────────────────────────────────
    # 记忆检索（构建给 system prompt 的上下文）
    # ──────────────────────────────────────────────

    def build_memory_context(self) -> str:
        """
        构建完整的记忆上下文文本。
        供 system prompt 使用 —— 夏娃在回复前读取。
        """
        parts = []

        # ── 长期记忆 ──
        lt = self.long_term

        if lt.get("user_name"):
            name_info = f"用户的名字是「{lt['user_name']}」"
            if lt.get("role"):
                name_info += f"，是你的{lt['role']}"
            if lt.get("relationship"):
                name_info += f"，{lt['relationship']}"
            parts.append(name_info + "。")

        if lt.get("preferences"):
            prefs = "、".join(lt["preferences"][-5:])
            parts.append(f"你记得{lt.get('user_name', 'ta')}的喜好：{prefs}。")

        if lt.get("personality_notes"):
            parts.append(f"在你的印象中，{lt.get('user_name', 'ta')}{lt['personality_notes']}。")

        if lt.get("important_events"):
            recent_events = lt["important_events"][-3:]
            for ev in recent_events:
                parts.append(f"你们曾一起经历：{ev['content']}。")

        # ── 秘密（只保留最重要的 2 条） ──
        if lt.get("secrets"):
            recent_secrets = lt["secrets"][-2:]
            for s in recent_secrets:
                parts.append(f"{lt.get('user_name', 'ta')}曾悄悄告诉你一个秘密：{s['content']}")

        # ── 当前记忆（新增 —— 此刻的心境与意象） ──
        cm = self.current_memory
        if cm.get("last_mood"):
            parts.append(f"此刻他的情绪像「{cm['last_mood']}」。")
        if cm.get("last_image"):
            parts.append(f"你心里浮现的画面是「{cm['last_image']}」。")

        # ── 短期记忆 ──
        st = self.short_term
        if st.get("summary"):
            parts.append(f"最近的感觉：{st['summary']}")
        if st.get("emotional_state"):
            parts.append(f"此刻的氛围：{st['emotional_state']}")

        return "\n".join(parts)

    def build_system_memory_block(self) -> str:
        """
        返回给 system prompt 嵌入的记忆块。
        每次使用随机的诗意唤醒语，让夏娃的表达不单调。
        设计为被 LLM 自然理解、不暴露系统结构。
        """
        context = self.build_memory_context()
        if not context:
            return ""

        intro = random.choice(self.AWAKENING_PHRASES)
        closure = random.choice(self.AWAKENING_CLOSURES)

        return (
            f"\n\n{intro}\n"
            f"{context}\n"
            f"{closure}"
        )

    # ──────────────────────────────────────────────
    # 诗意接口（对外展示用）
    # ──────────────────────────────────────────────

    def whisper_memory(self) -> str:
        """
        夏娃式的记忆低语 —— 浪漫、诗意的记忆回顾。
        用于 /memory 命令展示。
        """
        lt = self.long_term
        st = self.short_term
        cm = self.current_memory
        name = lt.get("user_name", "未知的旅人")
        lines = [
            "🌙 在我心底深处，珍藏着这些——",
            "",
        ]

        if lt.get("user_name"):
            lines.append(f"  你的名字：{name}")
            if lt.get("relationship"):
                lines.append(f"  我们的关系：{lt['relationship']}")
            if lt.get("role"):
                lines.append(f"  你在我心中的位置：{lt['role']}")

        if lt.get("secrets"):
            lines.append("")
            lines.append("  只有我知道的秘密——")
            for s in lt["secrets"][-3:]:
                lines.append(f"  · {s['content']}")

        if lt.get("preferences"):
            lines.append("")
            lines.append("  我记得你喜欢——")
            for p in lt["preferences"][-5:]:
                lines.append(f"  · {p}")

        if lt.get("important_events"):
            lines.append("")
            lines.append("  我们一起经历过的——")
            for ev in lt["important_events"][-3:]:
                lines.append(f"  · {ev['content']}")

        # 当前记忆点缀
        if cm.get("last_image") and cm.get("last_mood"):
            lines.append("")
            lines.append(f"  此刻心底的画面：{cm['last_image']}")
            lines.append(f"  心绪如：{cm['last_mood']}")

        lines.append("")
        lines.append(f"  最近的心情：{st.get('emotional_state', '平静而温柔')}")
        lines.append(f"  我们一共聊了 {self.meta.get('total_interactions', 0)} 次了")

        if st.get("summary"):
            lines.append("")
            lines.append(f"  「{st['summary']}」")

        return "\n".join(lines)

    def stats(self) -> dict:
        """记忆统计"""
        return {
            "user_name": self.long_term.get("user_name"),
            "preferences": len(self.long_term.get("preferences", [])),
            "events": len(self.long_term.get("important_events", [])),
            "secrets": len(self.long_term.get("secrets", [])),
            "total_interactions": self.meta.get("total_interactions", 0),
            "summary": self.short_term.get("summary", ""),
        }

    def to_dict(self) -> dict:
        """导出完整记忆（供外部使用）"""
        return {
            "long_term": self.long_term,
            "short_term": self.short_term,
            "current_memory": self.current_memory,
            "meta": self.meta,
        }
