# Windows 版本优化记录

> 记录 AI 夏娃在 Windows 原生环境下的适配优化过程

## 背景

项目最初以 macOS/Linux 为第一优先级，Windows 仅支持 WSL2 方式运行。本次优化使其能在 **Windows 原生环境**（无需 WSL）下直接运行。

---

## 优化内容

### 1. 修复 `readline` 模块缺失问题

**问题**：`cli/commands/chat.py` 第5行 `import readline` — `readline` 是 Unix-only 模块，Windows 上没有。

**触发路径**：Web UI (`ui/web/server.py`) 在 `_chat_with_model` 中执行 `from cli.commands.chat import _call_openai_compatible` 时，会触发 `chat.py` 顶层 import，导致 `ModuleNotFoundError`。

**修复方案**：职责分离，将模型调用函数提取到独立模块。

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `cli/api_client.py` | 纯 API 客户端，无 readline 依赖，只负责调用 OpenAI 兼容接口 |
| 修改 | `cli/commands/chat.py` | 删除 `import readline`，改为 `from cli.api_client import call_openai_compatible` |
| 修改 | `ui/web/server.py` | 导入源从 `cli.commands.chat` 改为 `cli.api_client` |

**效果**：
- CLI 模式：`chat.py` 正常通过 `input()` 交互，不受影响
- Web 模式：完全不加载 chat.py，无 readline 依赖
- 逻辑零重复，两边共享同一份 API 调用代码

---

### 2. 修复 `pyproject.toml` 构建配置

**问题一**：`build-backend` 路径错误

```toml
# 错误（此模块路径不存在）
build-backend = "setuptools.backends._legacy:_Backend"

# 修正
build-backend = "setuptools.build_meta"
```

**问题二**：`license` 字段使用了废弃的 TOML 表格式

```toml
# 错误（触发 SetuptoolsDeprecationWarning）
license = {text = "MIT"}

# 修正
license = "MIT"
```

**问题三**：flat-layout 下多个顶层包自动发现冲突

```toml
# 新增 — 显式声明所有 Python 包
[tool.setuptools]
packages = [
    "cli", "cli.commands",
    "core", "core.memory", "core.model", "core.skills",
    "gateway", "gateway.discord", "gateway.feishu", "gateway.telegram", "gateway.wechat",
    "ui", "ui.terminal", "ui.voice", "ui.web",
]
```

---

### 3. 创建 Windows 批处理入口

**`ai-eve.bat`** — 项目根目录下创建，作为 `ai-eve` 命令的 Windows 原生入口。

```batch
@echo off
cd /d "%~dp0"
python -m cli.main %*
```

**使用方式**：
- 在项目目录内直接执行：`ai-eve web`
- 如需全局可用，将项目目录添加到 PATH，或复制 `ai-eve.bat` 到 `%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\`

---

### 4. API 余额不足（402 错误）

现象：调用 DeepSeek API 返回 `HTTP 402 Insufficient Balance`

原因：API Key 对应的账户余额不足，需要充值。

处理：不影响代码逻辑，充值后自动恢复。错误已在 `_call_openai_compatible` 中友好处理（`请求失败 (HTTP 402): ...`）。

---

### 5. Token 审计日志系统

**目的**：每调用一次 AI 模型，自动记录消耗的 token 数量；飞将军可以随时查询任意时间段内的 token 消耗统计。

**实现方案**：

在 `cli/api_client.py` 的 `call_openai_compatible()` 函数中，API 返回后自动提取 `usage` 字段并写入日志文件：

```python
_log_token_usage(model, prompt_tokens, completion_tokens, total_tokens)
```

日志存储位置：

```
~/.ai-eve/data/logs/token_usage.jsonl
```

格式为 JSON Lines，每条记录包含：

| 字段 | 说明 |
|------|------|
| `timestamp` | ISO 8601 UTC 时间戳 |
| `model` | 模型名称（如 `deepseek-chat`） |
| `prompt_tokens` | 输入 token 数 |
| `completion_tokens` | 输出 token 数 |
| `total_tokens` | 总消耗 token 数 |

**查询命令**：`python -m cli.main token`

输出示例：

```
  📊 Token 消耗统计
  ==================================================
  累计调用次数: 5
  累计 Prompt tokens: 1,030
  累计 Completion tokens: 920
  累计总消耗:       1,950

  时间段        调用次数    Prompt   Completion      总计
  ------------ -------- ---------- ------------ ----------
  本月                 5      1,030          920     1,950
  昨天                 0          -            -         -
  今天                 5      1,030          920     1,950
  12小时内             5      1,030          920     1,950
  8小时内              5      1,030          920     1,950
  4小时内              5      1,030          920     1,950
  2小时内              5      1,030          920     1,950
  1小时内              3        680          720     1,400
  30分钟内             3        680          720     1,400
  15分钟内             1         80           20       100
```

**涉及的代码文件**：

| 文件 | 操作 | 说明 |
|------|------|------|
| `cli/api_client.py` | 修改 | 添加 `_log_token_usage()` 和 Token 日志路径常量 |
| `cli/commands/token_stats.py` | **新增** | Token 用量查询模块，按时间段汇总统计 |
| `cli/main.py` | 修改 | 添加 `token` 子命令入口 |

---

## 修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `ai-eve.bat` | **新增** | Windows 批处理入口 |
| `cli/api_client.py` | **新增** → 修改 | API 客户端独立模块，随后添加 Token 日志记录 |
| `cli/commands/token_stats.py` | **新增** | Token 用量查询 |
| `cli/commands/chat.py` | 修改 | 删除 readline 导入，改为引用 api_client |
| `cli/main.py` | 修改 | 添加 `token` 子命令入口 |
| `ui/web/server.py` | 修改 | 导入路径切换 |
| `pyproject.toml` | 修改 | 修复 build-backend、license、package discovery |
| `README.md` | 修改 | 更新 Windows + Token 使用说明 |
