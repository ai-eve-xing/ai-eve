# AI 夏娃 (AI Eve) — Windows 部署手册

> **文档版本**: v1.0
> **适用平台**: Windows 10 / 11（x64）
> **适用对象**: 运维工程师 / Windows 用户
> **项目版本**: 0.1.0

---

## 目录

1. [概述](#1-概述)
2. [环境准备](#2-环境准备)
3. [项目传输与安装](#3-项目传输与安装)
4. [配置文件详解](#4-配置文件详解)
5. [大模型接入方案](#5-大模型接入方案)
6. [启动与验证](#6-启动与验证)
7. [后台运行（Windows 服务化）](#7-后台运行windows-服务化)
8. [运维命令速查](#8-运维命令速查)
9. [故障排查](#9-故障排查)
10. [附录：WSL2 替代方案](#10-附录wsl2-替代方案)

---

## 1. 概述

### 1.1 什么是 AI Eve

AI 夏娃 (AI Eve) 是一款开源的 AI 伴侣应用，支持 CLI 命令行和 Web UI 两种交互方式，具备四层记忆系统。

### 1.2 Windows 平台特点

| 特性 | 说明 |
|------|------|
| **零外部依赖** | 纯 Python 标准库，Windows 下无需安装任何第三方 pip 包 |
| **自带启动脚本** | 项目自带 `ai-eve.bat`，双击即可启动 |
| **Web UI 默认端口** | 10110（可通过代码修改） |
| **本地持久化** | 记忆数据存储为 JSON 文件，无需数据库 |
| **WSL 可选** | 也支持在 WSL2 内运行（见附录） |

### 1.3 文件架构

```
ai-eve/
+-- cli/                        # CLI 命令行工具
|   +-- main.py                # 入口
|   +-- api_client.py          # API 调用客户端
|   +-- setup.py               # 配置向导
|   +-- commands/
|       +-- chat.py            # 对话循环
|       +-- model_config.py    # 模型配置
|       +-- token_stats.py     # Token 统计
+-- core/                       # 引擎层
|   +-- agent.py               # AI 对话引擎
|   +-- memory/
|       +-- memory_manager.py  # 四层记忆系统
+-- ui/web/                     # Web UI
|   +-- server.py              # HTTP 服务器（端口 10110）
+-- docs/                       # 文档
|   +-- Windows部署手册.md     # 本文档
+-- ai-eve.bat                  # Windows 启动脚本
+-- pyproject.toml              # 项目元数据
```

---

## 2. 环境准备

### 2.1 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Windows 10 (x64) | Windows 11 |
| Python | 3.10+ | 3.12 或 3.13 |
| 磁盘空间 | 50 MB（项目本体） | 10 GB+（如需本地大模型） |
| 内存 | 512 MB（仅服务） | 8 GB+（含本地大模型） |
| GPU（可选） | --- | NVIDIA + CUDA（本地推理加速） |

### 2.2 安装 Python

**方法 1：从微软商店安装（推荐）**

1. 打开 Microsoft Store，搜索 "Python"
2. 选择 **Python 3.12** 或 **Python 3.13**，点击安装
3. 安装完成后，打开命令提示符或 PowerShell 验证：

```cmd
python --version
```

**方法 2：从官网下载安装**

1. 访问 https://www.python.org/downloads/
2. 下载 Windows Installer (64-bit)
3. **重要**：安装时勾选 "Add Python to PATH"
4. 完成后验证：

```cmd
python --version
```

> **提示**：Windows 下命令是 `python` 和 `pip`，不是 `python3` 和 `pip3`。

### 2.3 验证 Python 安装

```powershell
# PowerShell 或 CMD
python --version
# 预期: Python 3.10.x 或更高

pip --version
# 预期: pip 24.x from ...

# 确认标准库完整（项目依赖）
python -c "import json, http.server, pathlib, urllib.request; print('OK')"
# 预期输出: OK
```

### 2.4 端口检查

默认 Web UI 端口为 **10110**，请确保未被占用：

```powershell
# 检查端口占用（PowerShell）
netstat -ano | findstr :10110

# 如看到 LISTENING 记录，表示端口被占用
# 可修改 server.py 中的 port 参数（第 382 行）
```

如需对外开放访问，请配置 Windows Defender 防火墙：

```powershell
# 以管理员身份运行 PowerShell
New-NetFirewallRule -DisplayName "AI Eve Web" -Direction Inbound -Protocol TCP -LocalPort 10110 -Action Allow
```

---

## 3. 项目传输与安装

### 3.1 获取项目文件

**方式 1：从有网络的机器拷贝**

将项目文件夹从开发机通过 U 盘、内网共享、或 SCP 等方式复制到目标 Windows 机器。

**方式 2：内网 Git 仓库**

```cmd
# 如果存在内网 GitLab/Gitea
git clone http://内网地址/ai-eve.git
```

**推荐放置位置**：

```
C:\Program Files\ai-eve\       # 系统级安装（需管理员权限）
D:\ai-eve\                      # 用户数据盘
E:\AI项目\ai-eve\               # 用户习惯路径
```

### 3.2 两种启动方式

| 启动方式 | 命令 | 需要 pip 安装？ | 推荐场景 |
|---------|------|:--------------:|---------|
| **批处理模式**（推荐） | 双击 `ai-eve.bat` 或 `ai-eve.bat web` | 不需要 | 最简操作 |
| **模块模式** | `python -m cli.main` | 不需要 | 命令行高级用户 |
| **命令模式** | `ai-eve` | 需要 (`pip install -e .`) | 追求简洁体验 |

> **核心结论**：Windows 下**无需任何 pip 安装**，双击 `ai-eve.bat` 或在终端执行 `ai-eve.bat web` 即可启动。

### 3.3 pip 安装（仅当需要使用 `ai-eve` 裸命令时）

如果需要输入 `ai-eve` 而不是 `ai-eve.bat` 来启动：

```cmd
cd /d D:\ai-eve

# 可编辑模式安装
pip install -e .

# 验证
where ai-eve
ai-eve --help
```

**为什么内网也能 pip 安装？**

- 项目 `dependencies = []`，**pip 不会下载任何第三方包**
- 仅注册 `ai-eve.exe` 入口点到系统 PATH
- 验证安装后：

```cmd
ai-eve           # 启动 CLI
ai-eve web       # 启动 Web UI
```

### 3.4 验证项目完整性

```cmd
cd /d D:\ai-eve

# 检查核心文件是否存在
dir cli\main.py
dir cli\api_client.py
dir core\agent.py
dir ui\web\server.py
dir ai-eve.bat
dir pyproject.toml

# 确认 Python 可识别模块
python -c "import sys; sys.path.insert(0, '.'); from cli.main import load_config; print('OK')"
```

> 预期输出：`OK`

---

## 4. 配置文件详解

### 4.1 配置文件位置

配置文件存储在用户目录下：

```
C:\Users\<用户名>\.ai-eve\data\config\config.json
```

例如用户名为 `lvping`，路径为：

```
C:\Users\lvping\.ai-eve\data\config\config.json
```

首次运行时会自动创建目录结构，也可手工创建：

```cmd
mkdir C:\Users\%USERNAME%\.ai-eve\data\config
mkdir C:\Users\%USERNAME%\.ai-eve\data\logs
mkdir C:\Users\%USERNAME%\.ai-eve\data\memory
mkdir C:\Users\%USERNAME%\.ai-eve\data\avatars
```

### 4.2 完整配置模板

创建 `C:\Users\%USERNAME%\.ai-eve\data\config\config.json`，内容如下：

```json
{
  "version": "0.1.0",
  "persona": {
    "name": "紫薇",
    "english_name": "ziwei",
    "style": "anime",
    "personality": "知性优雅",
    "greeting": "你好，我是紫薇。很高兴认识你。"
  },
  "model": {
    "provider": "deepseek",
    "api_key": "***",
    "base_url": "http://内网IP:11434/v1",
    "name": "qwen2.5:7b"
  },
  "voice": {
    "enabled": false,
    "provider": "",
    "voice_id": ""
  },
  "platforms": {
    "telegram": { "enabled": false },
    "discord": { "enabled": false },
    "wechat": { "enabled": false }
  },
  "appearance": {
    "style": "anime",
    "theme": "light"
  }
}
```

### 4.3 关键配置说明

| 配置项 | 说明 | 内网建议 |
|--------|------|---------|
| `persona.name` | AI 伴侣名字 | 默认"紫薇"，可自定义 |
| `persona.personality` | AI 性格标签 | 默认"知性优雅" |
| `model.base_url` | 大模型 API 地址 | **必须改为内网地址** |
| `model.name` | 模型标识 | 根据内网后端填写 |
| `model.api_key` | API Key | 可留空 |
| `voice.enabled` | 语音合成 | 内网关闭 |

### 4.4 交互式配置向导

也可运行配置向导自动生成：

```cmd
cd /d D:\ai-eve
python -m cli.main setup
```

---

## 5. 大模型接入方案

### 5.1 方案一：Ollama for Windows（推荐）

Ollama 提供 Windows 原生支持，是最简便的内网大模型方案。

#### 5.1.1 安装 Ollama

1. 访问 https://ollama.com/download 下载 Windows 版本
2. 运行安装程序，默认安装到 `C:\Program Files\Ollama\`
3. 安装完成后，Ollama 会自动在系统托盘运行
4. 验证：

```cmd
ollama --version
```

#### 5.1.2 下载模型

在内网环境，需要先在能联网的机器下载模型文件，然后拷贝到内网。

**方法 A：直接拉取（需要网络）**

```cmd
ollama pull qwen2.5:7b
```

**方法 B：离线传输**

在有网络的电脑下载：

```cmd
ollama pull qwen2.5:7b
```

模型文件位置：`C:\Users\<用户名>\.ollama\models\`

将整个 `.ollama\models\` 目录拷贝到内网机的对应位置。

#### 5.1.3 配置 Ollama 允许远程访问（可选）

Ollama 默认只监听 `127.0.0.1`。如果需要其他机器访问：

1. 设置环境变量：

```cmd
setx OLLAMA_HOST "0.0.0.0"
```

2. 重启 Ollama（系统托盘右键 -> Quit，然后重新启动）
3. 确认监听地址：

```cmd
netstat -ano | findstr :11434
```

#### 5.1.4 验证 Ollama API

```cmd
curl http://localhost:11434/api/generate -d "{\"model\": \"qwen2.5:7b\", \"prompt\": \"你好\", \"stream\": false}"
```

> Windows 10/11 内置 curl，无需额外安装。

#### 5.1.5 配置示例

```json
{
  "model": {
    "provider": "deepseek",
    "api_key": "",
    "base_url": "http://localhost:11434/v1",
    "name": "qwen2.5:7b"
  }
}
```

### 5.2 方案二：企业内部 API 网关

如果企业已有大模型 API 服务（如阿里云专有云、华为云 ModelArts、内网 API 代理等），只要接口兼容 OpenAI 格式即可：

```json
{
  "model": {
    "provider": "deepseek",
    "api_key": "***",
    "base_url": "http://内网网关地址/v1",
    "name": "模型标识"
  }
}
```

### 5.3 无大模型时的降级验证

如暂无大模型后端，可暂不配置模型。系统会提示"请先配置模型"，但 Web 界面和 CLI 均可正常启动。

---

## 6. 启动与验证

### 6.1 方法一：双击批处理文件（最简单）

项目根目录下有 `ai-eve.bat`，双击即可启动 CLI 模式。

如需启动 Web UI：

```cmd
# 在项目目录打开命令提示符
ai-eve.bat web
```

或者创建 `ai-eve-web.bat` 快捷方式：

```cmd
@echo off
cd /d "D:\ai-eve"
python -m cli.main web
pause
```

### 6.2 方法二：命令提示符 / PowerShell

```powershell
# 进入项目目录
cd D:\ai-eve

# 启动 CLI 对话
python -m cli.main

# 启动 Web UI
python -m cli.main web

# 配置向导
python -m cli.main setup

# 查看帮助
python -m cli.main help
```

### 6.3 方法三：pip 安装后（可选）

如果已执行 `pip install -e .`：

```cmd
ai-eve           # 启动 CLI
ai-eve web       # 启动 Web
ai-eve help      # 查看帮助
```

### 6.4 预期输出

**CLI 模式**：

```
==================================================
  🍎 紫薇  (知性优雅)
==================================================

  你好，我是紫薇，你的伊甸园伴侣。很高兴遇见你。

  输入 /help 查看命令，/quit 退出

  👤 你: 你好，紫薇
```

**Web UI 模式**：

```
🍎 AI 夏娃 --- Web UI
========================================
  紫薇 正在等待你...
  访问地址: http://localhost:10110
  按 Ctrl+C 停止
```

### 6.5 浏览器访问

启动 Web UI 后，在浏览器中访问：

```
http://localhost:10110
```

局域网其他设备访问（需配置防火墙）：

```
http://本机IP:10110
```

### 6.6 功能验证清单

| 序号 | 验证项 | 预期结果 | 操作 |
|------|--------|---------|------|
| 1 | Web 页面可访问 | 浏览器显示聊天界面 | 访问 http://localhost:10110 |
| 2 | CLI 启动 | 显示欢迎语和人物名 | `python -m cli.main` |
| 3 | /help 命令 | 显示命令列表 | 输入 `/help` |
| 4 | /rename 命令 | 记录名字 | `/rename 张三` |
| 5 | /memory | 显示记忆内容 | `/memory` |
| 6 | /stats | 显示统计信息 | `/stats` |
| 7 | Web 发消息 | 正常返回回复 | 在 Web 输入框输入 |

---

## 7. 后台运行（Windows 服务化）

Windows 没有 systemd，推荐以下方式让 AI Eve 在后台持续运行：

### 7.1 方案一：使用 Windows 任务计划程序（推荐）

这是最稳定的 Windows 服务化方案。

#### 步骤 1：创建启动脚本

创建 `C:\Program Files\ai-eve\start-web.bat`：

```bat
@echo off
cd /d "D:\ai-eve"
python -m cli.main web
```

#### 步骤 2：创建任务计划

```powershell
# 以管理员身份运行 PowerShell

$action = New-ScheduledTaskAction -Execute "D:\ai-eve\start-web.bat"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "AI Eve" `
  -Action $action `
  -Trigger $trigger `
  -Principal $principal `
  -Description "AI 夏娃 Web 服务"
```

#### 步骤 3：手动启动/停止

```powershell
# 启动
Start-ScheduledTask -TaskName "AI Eve"

# 停止
Stop-ScheduledTask -TaskName "AI Eve"

# 查看状态
Get-ScheduledTask -TaskName "AI Eve" | fl State

# 查看任务计划程序
taskschd.msc
```

#### 步骤 4：日志查看

Web 输出默认在启动该任务的用户的上下文窗口中。建议将日志重定向：

修改 `start-web.bat`：

```bat
@echo off
cd /d "D:\ai-eve"
python -m cli.main web >> D:\ai-eve\logs\web.log 2>&1
```

### 7.2 方案二：NSSM（Windows Service Wrapper）

NSSM 可将任意程序注册为 Windows 服务。

#### 安装 NSSM

从 https://nssm.cc/download 下载 nssm.exe，放到 `C:\Windows\System32\`。

#### 注册服务

```cmd
nssm install "AI Eve" "D:\ai-eve\start-web.bat"
```

在弹出的图形界面中设置：

- **Application > Arguments**: 留空（已在 bat 中处理）
- **Details > Display Name**: AI 夏娃 Web 服务
- **Details > Startup type**: Automatic
- **Exit Actions > Restart**: 设置为 Restart

#### 管理服务

```cmd
# 启动
nssm start "AI Eve"

# 停止
nssm stop "AI Eve"

# 重启
nssm restart "AI Eve"

# 查看状态
nssm status "AI Eve"

# 或使用 services.msc 管理
services.msc
```

### 7.3 方案三：PowerShell 后台作业（轻量临时方案）

```powershell
# 启动后台作业
$job = Start-Job -ScriptBlock {
  Set-Location "D:\ai-eve"
  python -m cli.main web
}

# 查看作业状态
Get-Job $job

# 停止作业
Stop-Job $job
Remove-Job $job
```

> **注意**：PowerShell 后台作业在用户注销时会终止，仅适合临时使用。

---

## 8. 运维命令速查

```cmd
:: --- 启动（无需 pip 安装） ---
cd /d D:\ai-eve && python -m cli.main                    启动 CLI
cd /d D:\ai-eve && python -m cli.main web                启动 Web
cd /d D:\ai-eve && python -m cli.main setup              配置向导
cd /d D:\ai-eve && python -m cli.main help               查看帮助
cd /d D:\ai-eve && ai-eve.bat web                        双击/批处理启动

:: --- 如果已 pip install -e . ---
ai-eve                                                    启动 CLI
ai-eve web                                                启动 Web

:: --- 服务管理（任务计划程序） ---
Start-ScheduledTask -TaskName "AI Eve"                    启动服务
Stop-ScheduledTask -TaskName "AI Eve"                     停止服务
Get-ScheduledTask -TaskName "AI Eve"                      查看状态

:: --- 服务管理（NSSM） ---
nssm start "AI Eve"                                       启动服务
nssm stop "AI Eve"                                        停止服务
nssm restart "AI Eve"                                     重启服务
nssm status "AI Eve"                                      查看状态

:: --- 测试连通性 ---
curl http://localhost:10110/                               测试 Web 服务

:: --- 数据管理 ---
dir %USERPROFILE%\.ai-eve\data\config\                    配置文件位置
dir %USERPROFILE%\.ai-eve\data\memory\                    记忆文件位置
dir %USERPROFILE%\.ai-eve\data\logs\                      Token 日志

:: --- 进程管理 ---
tasklist | findstr python                                  查看进程
taskkill /F /IM python.exe                                 强制结束所有 Python
```

---

## 9. 故障排查

### 9.1 问题：'python' 不是内部或外部命令

**原因**：Python 未安装或未添加到 PATH

**解决**：

1. 确认已安装 Python
2. 手动添加到 PATH：

```cmd
# 查看 Python 安装路径
where python

# 如果未找到，重新安装并勾选 "Add Python to PATH"
# 或手动添加到系统环境变量
```

### 9.2 问题：Web 页面无法访问

```cmd
:: 第一步：确认服务正在运行
tasklist | findstr python

:: 第二步：确认端口监听
netstat -ano | findstr :10110

:: 第三步：检查防火墙
wf.msc
:: 查看是否有 AI Eve 的入站规则
```

### 9.3 问题：模型调用失败

```cmd
:: 第一步：手动测试 API 连通性
curl http://localhost:11434/v1/models

:: 第二步：测试对话接口
curl -X POST http://localhost:11434/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"model\": \"qwen2.5:7b\", \"messages\": [{\"role\": \"user\", \"content\": \"你好\"}]}"

:: 第三步：检查配置文件
type %USERPROFILE%\.ai-eve\data\config\config.json

:: 确认：
:: - base_url 正确（以 /v1 结尾）
:: - name 与模型名称匹配
:: - 无多余空格或语法错误
```

### 9.4 问题：Python 模块找不到

```cmd
:: 确认当前目录是项目根目录
cd /d D:\ai-eve
dir cli\main.py

:: 如仍有问题，手动设置 PYTHONPATH
set PYTHONPATH=D:\ai-eve
python -c "from cli.main import load_config; print('OK')"
```

### 9.5 问题：配置文件 JSON 格式错误

```cmd
:: 使用 Python 检查 JSON 语法
python -m json.tool %USERPROFILE%\.ai-eve\data\config\config.json

:: 常见错误：
:: - 末尾多了逗号
:: - 使用了单引号（JSON 必须用双引号）
:: - 键名缺少引号
:: - 中文冒号代替了英文冒号
```

### 9.6 问题：终端中文乱码

```cmd
:: 切换到 UTF-8 编码
chcp 65001

:: 或修改注册表使 PowerShell 默认 UTF-8
:: HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Nls\CodePage
:: 将 ACP、OEMCP、MACCP 改为 65001
```

### 9.7 问题：杀毒软件拦截

某些杀毒软件可能会误报 Python 脚本。请将项目目录添加至杀毒软件白名单：

```
D:\ai-eve\
%USERPROFILE%\.ai-eve\
```

---

## 10. 附录：WSL2 替代方案

如果更习惯 Linux 环境，也可在 WSL2 中运行 AI Eve。

### 10.1 安装 WSL2

```powershell
# 以管理员身份运行 PowerShell
wsl --install
# 默认安装 Ubuntu，重启后自动完成
```

### 10.2 在 WSL2 中部署

```bash
# 进入 WSL2
wsl

# 将项目复制到 WSL 内（或直接访问 Windows 文件系统）
cp -r /mnt/e/AI学习/AI项目/ai-eve ~/ai-eve
# 或直接在 Windows 路径下运行（性能稍低）
cd /mnt/d/ai-eve
```

> **注意**：如果项目在 Windows 磁盘上（`/mnt/c/`、`/mnt/d/`），WSL 可以访问，但文件性能较低。建议将项目复制到 WSL 原生文件系统（`~/ai-eve`）。

### 10.3 Windows 与 WSL 路径对照

| Windows 路径 | WSL 路径 |
|-------------|---------|
| `C:\Users\用户名` | `/mnt/c/Users/用户名` |
| `D:\ai-eve` | `/mnt/d/ai-eve` |
| `E:\AI项目\ai-eve` | `/mnt/e/AI学习/AI项目/ai-eve` |

### 10.4 WSL 下的配置提醒

WSL 下启动后用 `python3` 而非 `python`：

```bash
cd ~/ai-eve
python3 -m cli.main web
```

配置文件仍在 Windows 用户目录：

```
# WSL 中读取 Windows 用户目录
~/.ai-eve/data/config/config.json
# 实际对应: C:\Users\<用户名>\.ai-eve\data\config\config.json
```

> WSL 无需修改防火墙规则，端口 `10110` 会自动转发。

---

> **本文档版本 v1.0** — 专为 Windows 平台编写。
>
> 如有疑问，请查阅项目 README 或联系维护团队。
