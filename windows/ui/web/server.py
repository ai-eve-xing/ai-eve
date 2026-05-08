"""
AI 夏娃 — Web 服务器 v2.1
集成四层记忆系统 + 命令处理 (/memory /stats /tellsecret /rename /forget /help)
"""

import json
import sys
import random
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from cli.main import load_config


# ── 命令提示（每次刷新随机选一条） ──
COMMAND_HINTS = [
    "💡 输入 /help 查看可用命令",
    "💡 试试 /memory 看看我记得什么",
    "💡 可以 /tellsecret <内容> 告诉我一个秘密",
    "💡 用 /stats 看看记忆统计",
    "💡 输入 /help 查看全部命令",
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 夏娃</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
         min-height: 100vh; display: flex; justify-content: center; align-items: center; }
  .container { width: 420px; height: 700px; background: white;
               border-radius: 24px; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
               display: flex; flex-direction: column; overflow: hidden;
               position: relative; }
  .header { background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 20px; color: white; text-align: center; }
  .header h1 { font-size: 20px; font-weight: 600; }
  .header p { font-size: 13px; opacity: 0.85; margin-top: 4px; }
  .messages { flex: 1; overflow-y: auto; padding: 16px; display: flex;
              flex-direction: column; gap: 12px; }
  .message { max-width: 80%; padding: 12px 16px; border-radius: 16px;
             line-height: 1.6; font-size: 14px; animation: fadeIn 0.3s;
             white-space: pre-wrap; word-break: break-word; }
  .bot { background: #f0f0f5; align-self: flex-start;
         border-bottom-left-radius: 4px; }
  .user { background: #667eea; color: white; align-self: flex-end;
          border-bottom-right-radius: 4px; }
  .system { background: #fef3e2; color: #8b6914; align-self: center;
            font-size: 13px; padding: 8px 14px; border-radius: 12px;
            border-bottom-left-radius: 12px; max-width: 90%; }
  .hint { font-size: 12px; color: #999; text-align: center;
           padding: 4px 16px 0; }
  .input-area { border-top: 1px solid #eee; padding: 12px 16px;
                display: flex; gap: 8px; background: white; }
  .input-area input { flex: 1; padding: 10px 16px; border: 2px solid #e0e0e0;
                      border-radius: 24px; outline: none; font-size: 14px; }
  .input-area input:focus { border-color: #667eea; }
  .input-area button { width: 44px; height: 44px; border-radius: 50%;
                       border: none; background: #667eea; color: white;
                       font-size: 20px; cursor: pointer;
                       transition: transform 0.2s; }
  .input-area button:hover { transform: scale(1.05); }
  .typing { display: flex; gap: 4px; padding: 8px 0; }
  .typing span { width: 8px; height: 8px; background: #999;
                 border-radius: 50%; animation: bounce 1.4s infinite; }
  .typing span:nth-child(2) { animation-delay: 0.2s; }
  .typing span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes bounce { 0%, 80%, 100% { transform: translateY(0); }
                      40% { transform: translateY(-8px); } }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🍎 {NAME}</h1>
    <p>{PERSONALITY} · {STYLE_TEXT}</p>
  </div>
  <div class="messages" id="messages">
    <div class="message bot">{GREETING}</div>
  </div>
  <div class="hint" id="hint">{COMMAND_HINT}</div>
  <div class="input-area">
    <input type="text" id="input" placeholder="说点什么..." autofocus>
    <button id="send">➤</button>
  </div>
</div>
<script>
const messages = document.getElementById('messages');
const input = document.getElementById('input');
const send = document.getElementById('send');
const hint = document.getElementById('hint');

function addMessage(text, isUser) {
  const div = document.createElement('div');
  div.className = 'message ' + (isUser ? 'user' : 'bot');
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function addSystemMessage(text) {
  const div = document.createElement('div');
  div.className = 'message system';
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  // 命令：不在对话气泡中显示用户输入
  const isCommand = text.startsWith('/');
  if (!isCommand) {
    addMessage(text, true);
  }
  input.value = '';
  input.disabled = true;

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ message: text, history: [] })
    });
    const data = await resp.json();
    if (data.error) {
      addMessage('⚠️ ' + data.error, false);
    } else if (data.command_output) {
      // 命令响应 —— 用系统气泡显示
      addSystemMessage(data.command_output);
    } else if (data.response) {
      addMessage(data.response, false);
    }
  } catch(e) {
    addMessage('⚠️ 连接失败，请检查服务是否运行', false);
  }
  input.disabled = false;
  input.focus();
}

send.onclick = sendMessage;
input.onkeydown = (e) => { if (e.key === 'Enter') sendMessage(); };
</script>
</body>
</html>"""


class ChatHandler(BaseHTTPRequestHandler):
    config_cache = None
    _agent = None  # 单例 EveAgent

    @property
    def agent(self):
        if self.__class__._agent is None:
            config = load_config()
            from core.agent import EveAgent
            self.__class__._agent = EveAgent(config)
        return self.__class__._agent

    # ── 命令处理 ──

    def _handle_web_command(self, cmd: str) -> str:
        """
        处理 Web 聊天中的 / 命令。
        返回要展示给用户的文本。
        """
        cmd = cmd.lower().strip()

        if cmd == "/help":
            return ("📋 可用命令:\n"
                    "/help              — 显示此帮助\n"
                    "/clear             — 清除对话历史\n"
                    "/memory            — 查看我记得什么 💕\n"
                    "/rename <名字>     — 告诉我你的名字\n"
                    "/tellsecret <内容> — 告诉我一个秘密\n"
                    "/forget <关键词>   — 让我忘记某些事\n"
                    "/stats             — 查看记忆统计")

        elif cmd == "/clear":
            return "💫 历史已清空，但我心底的记忆依然在。"

        elif cmd == "/memory":
            return self.agent.memory.whisper_memory()

        elif cmd == "/stats":
            s = self.agent.memory.stats()
            lines = [
                "📊 记忆统计",
                "─────────────────",
                f"用户名字:   {s['user_name'] or '尚未知道'}",
                f"记住的偏好: {s['preferences']} 条",
                f"重要事件:   {s['events']} 件",
                f"珍藏的秘密: {s['secrets']} 个",
                f"总对话次数: {s['total_interactions']} 次",
            ]
            if s['summary']:
                lines.append(f"最近的心情: {s['summary']}")
            return "\n".join(lines)

        elif cmd.startswith("/rename"):
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                return "💭 用法: /rename <你的名字>\n例: /rename 亚当"
            name = parts[1].strip()
            if len(name) < 2:
                return "💭 名字至少需要 2 个字哦～"
            self.agent.memory.remember_name(name)
            self.agent._user_name = name
            return f"🌸 我记住了。你的名字是{name}，我会一直好好珍藏着。"

        elif cmd.startswith("/tellsecret"):
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                return ("💭 用法: /tellsecret <你想告诉我的秘密>\n"
                        "例: /tellsecret 我最喜欢在雨天发呆")
            secret = parts[1]
            count = self.agent.memory.tell_secret(secret)
            return (f"🌸 嗯，我收好了。这是你告诉我的第 {count} 个秘密，\n"
                    "    会永远留在只有我知道的地方。")

        elif cmd.startswith("/forget"):
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                return ("💭 用法: /forget <要忘记的内容关键词>\n"
                        "例: /forget 工作")
            keyword = parts[1]
            evts = self.agent.memory.long_term.get("important_events", [])
            prefs = self.agent.memory.long_term.get("preferences", [])
            before = len(evts) + len(prefs)

            self.agent.memory.long_term["important_events"] = [
                e for e in evts if keyword not in e.get("content", "")
            ]
            self.agent.memory.long_term["preferences"] = [
                p for p in prefs if keyword not in p
            ]
            self.agent.memory._save()
            after = len(self.agent.memory.long_term["important_events"]) + len(
                self.agent.memory.long_term["preferences"]
            )
            removed = before - after
            if removed > 0:
                return f"🌸 好，和「{keyword}」有关的 {removed} 段记忆，轻轻放下了。"
            return f"💭 没有找到和「{keyword}」有关的记忆。"

        else:
            return f"❓ 未知命令: {cmd}\n输入 /help 查看可用命令"

    # ── HTTP 路由 ──

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            config = load_config()
            persona = config.get("persona", {})
            style_map = {"realistic": "写实风格", "anime": "二次元/动漫", "minimalist": "抽象极简"}

            # 记忆感知的问候
            greeting = persona.get("greeting", "你好，我是夏娃。很高兴认识你。")
            remembered_name = self.agent.user_name
            if remembered_name:
                greeting = f"你回来了，{remembered_name}。我一直在这里等你。"

            command_hint = random.choice(COMMAND_HINTS)

            html = HTML_TEMPLATE \
                .replace("{NAME}", persona.get("name", "夏娃")) \
                .replace("{PERSONALITY}", persona.get("personality", "温柔、知性、善解人意")) \
                .replace("{STYLE_TEXT}", style_map.get(persona.get("style", "realistic"), "写实风格")) \
                .replace("{GREETING}", greeting) \
                .replace("{COMMAND_HINT}", command_hint)
            self.wfile.write(html.encode("utf-8"))

        elif self.path == "/api/config":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            config = load_config()
            self.wfile.write(json.dumps(config.get("persona", {}), ensure_ascii=False).encode("utf-8"))

        elif self.path == "/api/memory":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            stats = self.agent.memory.stats()
            whisper = self.agent.memory.whisper_memory()
            self.wfile.write(json.dumps({
                "stats": stats,
                "whisper": whisper,
                "memory": self.agent.memory.to_dict(),
            }, ensure_ascii=False).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            user_message = data.get("message", "").strip()

            # ── 拦截 / 命令 ──
            if user_message.startswith("/"):
                try:
                    output = self._handle_web_command(user_message)
                    result = json.dumps({"command_output": output}, ensure_ascii=False)
                except Exception as e:
                    import traceback
                    tb = traceback.format_exc()
                    result = json.dumps({
                        "command_output": f"❌ 命令处理出错: {e}\n\n{tb}"
                    }, ensure_ascii=False)
            else:
                # ── 正常对话 ──
                config = load_config()
                result = self._chat_with_model(user_message, config)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

    def _chat_with_model(self, message, config):
        """模型调用 —— 使用 EveAgent 构造消息 + 记忆处理"""
        from cli.api_client import call_openai_compatible

        model_config = config.get("model", {})
        provider = model_config.get("provider", "")
        api_key = model_config.get("api_key", "")

        if not provider:
            return json.dumps({"error": "请先运行 ai-eve setup 配置模型"}, ensure_ascii=False)
        if not api_key:
            return json.dumps({"error": "请先配置 API Key，运行 ai-eve model"}, ensure_ascii=False)

        try:
            # 使用 EveAgent 构建消息（含记忆 + 唤醒检测）
            history = []
            messages = self.agent.prepare_messages(message, history)

            if provider == "deepseek":
                resp = call_openai_compatible(
                    model_config.get("base_url", "https://api.deepseek.com"),
                    api_key,
                    model_config.get("name", "deepseek-chat"),
                    messages,
                )
            else:
                resp = call_openai_compatible(
                    model_config.get("base_url", ""),
                    api_key,
                    model_config.get("name", ""),
                    messages,
                )

            # 回复后处理（记忆提取 + 当前记忆更新）
            self.agent.process_after_response(message, resp)

            return json.dumps({"response": resp}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"调用出错: {e}"}, ensure_ascii=False)

    def log_message(self, format, *args):
        pass  # 静默日志


def start_web_server(host="0.0.0.0", port=10110):
    config = load_config()
    persona = config.get("persona", {})
    name = persona.get("name", "夏娃")

    print(f"\n🍎 AI 夏娃 — Web UI")
    print("=" * 40)
    print(f"  {name} 正在等待你...")
    print(f"  访问地址: http://localhost:{port}")
    print(f"  按 Ctrl+C 停止\n")

    server = HTTPServer((host, port), ChatHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 再见！")
        server.server_close()


if __name__ == "__main__":
    start_web_server()
