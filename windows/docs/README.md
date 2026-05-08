# 🍎 AI 夏娃 (AI Eve)

> 你的专属 AI 伴侣 —— 为男性用户设计的智能陪伴助手

AI 夏娃是一款开源的、支持自部署的 AI 伴侣应用。她不仅是聊天机器人，更是一位有性格、有记忆、有温度的虚拟伴侣。

## ✨ 特性

- **跨平台支持** — macOS / Linux / Windows（原生 + WSL2）
- **一键安装** — 单条命令 curl 安装，零依赖
- **多模型支持** — 配置云端大模型 API（DeepSeek、通义千问、OpenAI、OpenRouter等），也支持本地模型（vLLM、Ollama）
- **多模态交互** — 文字聊天、语音对话、图片理解、视频理解
- **持久记忆** — 记住你的喜好、习惯、说过的话，无需重复解释
- **多平台接入** — Telegram、Discord、微信、飞书、Web 终端
- **视觉自定义** — 支持写实风格、二次元/动漫风格、抽象极简风格
- **自有知识库** — 支持导入文档、链接，构建专属知识
- **100% 本地化部署** — 数据完全在你的设备上，无云端依赖
- **日程与提醒** — 定时任务、每日简报、重要提醒

## 🚀 快速开始

### 一键安装（macOS / Linux）

```bash
curl -fsSL https://raw.githubusercontent.com/muse960/ai-eve/main/scripts/install.sh | bash
```

### Windows 原生安装

项目已适配 Windows 原生环境（无需 WSL）。

```cmd
# 1. 克隆或下载项目
git clone https://github.com/muse960/ai-eve.git
cd ai-eve

# 2. （可选）安装为系统命令，之后可直接使用 ai-eve
pip install -e .

# 3. 直接使用（不安装也可）
python -m cli.main web
```

项目根目录下的 `ai-eve.bat` 提供了快捷入口，在项目目录内可直接：

```cmd
ai-eve web        # 启动 Web UI
ai-eve            # 启动 CLI 聊天
ai-eve setup      # 配置向导
```

> 如需在任意目录使用 `ai-eve` 命令，可将项目目录添加到 PATH 环境变量。

### 配置

```bash
# 交互式配置向导
ai-eve setup

# 配置大模型
ai-eve model

# 选择视觉风格
ai-eve style
```

### 启动

```bash
# CLI 模式
ai-eve

# Web UI 模式（浏览器访问 http://localhost:10110）
ai-eve web

# 启动语音对话
ai-eve voice

# 查看 Token 消耗统计
ai-eve token
```

### 应急操作命令

如果 `ai-eve` 命令不可用（未安装或未加入 PATH），可使用以下命令直接启动：

```bash
# CLI 模式
python -m cli.main

# 查看帮助
python -m cli.main help

# Web UI 模式
python -m cli.main web

# 配置向导
python -m cli.main setup

# 配置模型
python -m cli.main model

# 切换风格
python -m cli.main style

# 语音对话
python -m cli.main voice

# 查看 Token 消耗统计
python -m cli.main token
```

## 📦 安装方式

### macOS

```bash
brew install ai-eve/tap/ai-eve
# 或
curl -fsSL https://raw.githubusercontent.com/muse960/ai-eve/main/scripts/install.sh | bash
```

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/muse960/ai-eve/main/scripts/install.sh | bash
```

### Windows

#### 原生（推荐）

项目已适配 Windows 原生环境，无需 WSL。

```cmd
# 克隆项目
git clone https://github.com/muse960/ai-eve.git
cd ai-eve

# 直接启动（零安装）
python -m cli.main web

# 或使用批处理文件
ai-eve web
```

#### WSL2（备选）

```powershell
wsl --install
# 在 WSL2 中运行
curl -fsSL https://raw.githubusercontent.com/muse960/ai-eve/main/scripts/install.sh | bash
```

## 🔧 配置说明

### 大模型配置

| 类型 | 方式 | 示例 |
|------|------|------|
| 云端 API | 配置 API Key | DeepSeek、通义千问、OpenAI |
| 聚合平台 | OpenRouter | 200+ 模型可选 |
| 本地模型 | Ollama / vLLM | Qwen、Llama、DeepSeek 本地部署 |

```bash
# 使用云端 API
ai-eve config set model.provider deepseek
ai-eve config set model.api_key sk-xxx

# 使用本地模型
ai-eve config set model.provider ollama
ai-eve config set model.name qwen2.5:7b
```

### 视觉风格

```bash
# 查看可用风格
ai-eve style list

# 设置风格
ai-eve style set realistic    # 写实风格
ai-eve style set anime        # 二次元/动漫
ai-eve style set minimalist   # 抽象极简
```

## 🗂️ 项目结构

```
ai-eve/
├── cli/                    # CLI 命令行工具
│   ├── api_client.py      # API 客户端（模型调用层）
│   ├── main.py            # 入口
│   ├── setup.py           # 安装配置向导
│   └── commands/          # 子命令
│       └── token_stats.py # Token 消耗统计
├── core/                   # 核心逻辑
│   ├── agent.py           # Agent 核心
│   ├── memory/            # 记忆系统
│   ├── model/             # 模型适配层
│   └── skills/            # 技能系统
├── ui/                     # 用户界面
│   ├── web/               # Web UI (React)
│   ├── terminal/          # 终端 UI
│   └── voice/             # 语音交互
├── gateway/                # 消息网关
│   ├── telegram/
│   ├── discord/
│   ├── wechat/
│   └── feishu/
├── assets/                 # 资源文件
│   └── avatars/           # 不同风格的虚拟形象
├── scripts/                # 安装部署脚本
│   ├── install.sh
│   └── setup.sh
├── config/                 # 配置模板
└── docs/                   # 文档
```

## 📄 开源协议

MIT License

## 🤝 参与贡献

欢迎 PR、Issue、功能建议！
