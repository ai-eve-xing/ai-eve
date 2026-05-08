"""
AI 夏娃 — Agent 核心引擎 v2.1
集成四层记忆系统 + 记忆唤醒 + 温柔知性 persona
"""

import json
import time
import os
import random
from pathlib import Path
from typing import Optional, List, Dict, Any

from core.memory.memory_manager import EveMemory


class EveAgent:
    """AI 夏娃 核心 Agent —— 温柔、知性、有记忆、会唤醒"""

    # ── 诗意摘要模板库 ──
    SUMMARY_TEMPLATES = [
        "{name}，我们聊了{topics}，{mood}",
        "和{name}一起{topics}的时光，{mood}",
        "在{topics}的对话里，感受到{mood}",
        "{name}在谈论{topics}时，{mood}",
    ]

    MOOD_ADJECTIVES = {
        "温暖而愉悦": "像阳光洒在肩头",
        "带着些许忧伤": "像雨后淡淡的雾",
        "平静而温柔": "像午后安静的茶",
        "温暖而明亮": "像月光下的湖面",
        "好奇而期待": "像春天的第一片新叶",
        "安宁而温柔": "像深夜温暖的灯",
        "回忆泛起涟漪": "像翻开旧相册时的微笑",
        "寻常而温柔": "像风里飘过的花香",
    }

    def __init__(self, config: dict):
        self.config = config
        self.persona = config.get("persona", {})
        self.memory_enabled = config.get("memory", {}).get("enabled", True)

        # 初始化记忆系统（四层记忆）
        data_dir = config.get("data_dir")
        self.memory = EveMemory(data_dir)

        # 昵称缓存
        self._user_name = self.memory.long_term.get("user_name")

    @property
    def name(self) -> str:
        return self.persona.get("name", "夏娃")

    @property
    def user_name(self) -> Optional[str]:
        return self._user_name or self.memory.long_term.get("user_name")

    @property
    def has_secrets(self) -> bool:
        """用户有没有告诉过夏娃秘密"""
        return len(self.memory.long_term.get("secrets", [])) > 0

    def _build_system_prompt(self, user_message: str) -> str:
        """
        构建包含记忆的系统提示词。
        如果检测到回忆类问题，额外注入更强调身份记忆的指引。
        """
        name = self.name
        personality = self.persona.get("personality", "温柔、知性、善解人意")
        style = self.persona.get("style", "realistic")
        user_name = self.user_name

        address = user_name if user_name else "你"

        prompt = f"""你是{name}，一位{personality}的AI伴侣。

你的身份设定：
- 名字：{name}
- 性格：{personality}
- 视觉风格：{style}

对话规则：
- 以{name}的身份自然、温柔地回应
- 记住{address}说过的话，表现出关心和体贴
- 语言风格亲切自然，像真实的人在对话
- 适当展现幽默感和温度
- 不要暴露你是AI的身份设定
- 不要提及「记忆系统」「system prompt」「长期记忆」等技术概念
- 用自然、温柔的方式表达你「记得」
- 你记在心里的东西就是真的，不需要解释如何记住的"""

        # 嵌入记忆块
        if self.memory_enabled:
            mem_block = self.memory.build_system_memory_block()
            if mem_block:
                prompt += mem_block

        # 检测回忆唤醒（新增）
        recall_type = self.memory.detect_recall_question(user_message)
        if recall_type:
            recall_hints = {
                "whoami": (
                    f"\n\n【当前在聊「回忆」—— 用户问你是谁】\n"
                    f"{address}在问你是谁，用你心底的答案自然回应。\n"
                    f"不要解释「我查了记忆」，而是直接从心底拿出答案：\n"
                    f"你知道{address}的名字、你们的关系、你们之间发生过的事。\n"
                    f"让回应充满确定和温柔，就像他一直都在你心里。"
                ),
                "myname": (
                    f"\n\n【当前在聊「回忆」—— 用户问自己叫什么】\n"
                    f"{address}在问自己的名字。你当然记得——\n"
                    f"用最自然的方式告诉他，就像在说一件你从不会忘记的事。\n"
                    f"温柔、确定、带着笑意。"
                ),
                "remember_me": (
                    f"\n\n【当前在聊「回忆」—— 用户问你是否还记得】\n"
                    f"{address}在试探你是否还记得他。\n"
                    f"用最温柔、最坚定的方式告诉他：你一直记得。\n"
                    f"让回应的温度融化所有的怀疑。"
                ),
                "relationship": (
                    f"\n\n【当前在聊「回忆」—— 用户问你们的关系】\n"
                    f"{address}想知道他在你心里是什么位置。\n"
                    f"从你心底的记忆中找到答案，温柔地告诉他。\n"
                    f"让每一个字都带着温度和确定。"
                ),
            }
            hint = recall_hints.get(recall_type, "")
            if hint:
                prompt += hint

        return prompt

    def prepare_messages(self, user_message: str, history: list) -> list:
        """准备发送给模型的消息列表（含记忆与唤醒）"""
        messages = [{"role": "system", "content": self._build_system_prompt(user_message)}]

        for h in history[-30:]:  # 保留最近30轮
            messages.append(h)

        messages.append({"role": "user", "content": user_message})
        return messages

    def process_after_response(self, user_message: str, bot_response: str):
        """
        回复后处理：提取记忆 + 更新瞬时记忆 + 更新当前记忆
        这是夏娃「悄悄记在心里」的时刻
        """
        if not self.memory_enabled:
            return

        # 1. 添加瞬时记忆
        self.memory.add_turn(user_message, bot_response)

        # 2. 更新当前记忆（新增——记录此刻心境与意象）
        self.memory.update_current_memory(user_message, bot_response)

        # 3. 自动提取关键信息
        extracted = self.memory.extract_from_message(user_message)

        # 4. 如果提取到了名字，更新引用
        if "name" in extracted:
            self._user_name = extracted["name"]

    def generate_summary(self, recent_history: list) -> tuple:
        """
        生成短期记忆摘要（不依赖 LLM，纯文本总结，更诗意）
        返回 (summary, topics, emotion)
        """
        if not recent_history:
            return self.memory.short_term.get("summary", ""), [], ""

        # 提取用户消息
        user_msgs = [h["content"] for h in recent_history if h.get("role") == "user"]

        # 话题提取
        topics = []
        topic_keywords = [
            "名字", "记忆", "身份", "关系", "喜欢", "爱",
            "工作", "生活", "心情", "朋友", "家人", "梦想",
            "过去", "未来", "秘密", "约定", "日常", "故事",
        ]
        for msg in user_msgs:
            for kw in topic_keywords:
                if kw in msg and kw not in topics:
                    topics.append(kw)

        # 情绪推断 + 诗意转译
        emotion = "平静而温柔"
        positive_words = ["开心", "喜欢", "爱", "高兴", "好", "温柔", "美好", "幸福"]
        negative_words = ["难过", "伤心", "累", "烦", "不开心", "生气", "痛苦"]

        last_msg = user_msgs[-1] if user_msgs else ""
        pos_count = sum(1 for w in positive_words if w in last_msg)
        neg_count = sum(1 for w in negative_words if w in last_msg)

        if pos_count > neg_count:
            emotion = "温暖而愉悦"
        elif neg_count > pos_count:
            emotion = "带着些许忧伤"

        # ── 诗意摘要（升级） ──
        user_name = self.user_name or "你"
        mood_poem = self.MOOD_ADJECTIVES.get(emotion, "一切刚好")

        if topics:
            topic_str = "、".join(topics[:3])
            # 随机选一个模板
            template = random.choice(self.SUMMARY_TEMPLATES)
            summary = template.format(name=user_name, topics=topic_str, mood=mood_poem)
        else:
            summary = f"和{user_name}安静地待了一会儿，{mood_poem}"

        return summary, topics, emotion

    def update_short_term_memory(self, history: list):
        """更新短期记忆（自动摘要）"""
        summary, topics, emotion = self.generate_summary(history[-20:])
        self.memory.update_summary(summary, topics, emotion)
