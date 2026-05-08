#!/usr/bin/env bash
#
# AI 夏娃 (AI Eve) — Installation Script
# =========================================
# Single-command installer for macOS, Linux, and Windows (WSL2).
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/muse960/ai-eve/main/scripts/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/muse960/ai-eve/main/scripts/install.sh | bash -s -- --dev
#

set -euo pipefail

# ── Color & Style ──────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

info()  { echo -e "${BLUE}💬${RESET} ${BOLD}$1${RESET}"; }
ok()    { echo -e "${GREEN}✅${RESET} $1"; }
warn()  { echo -e "${YELLOW}⚠️${RESET} $1"; }
error() { echo -e "${RED}❌${RESET} $1"; }
step()  { echo -e "\n${MAGENTA}━━━ ${BOLD}$1${RESET}${MAGENTA} ━━━${RESET}"; }
title() { echo -e "\n${CYAN}${BOLD}========================"; echo "   🍎 AI 夏娃 (AI Eve)"; echo "========================${RESET}\n"; }

# ── Configuration ──────────────────────────────────────────────
REPO="muse960/ai-eve"
BRANCH="${AI_EVE_BRANCH:-main}"
INSTALL_DIR="${AI_EVE_DIR:-$HOME/.ai-eve}"
BIN_DIR="${HOME}/.local/bin"
UV_BIN="${INSTALL_DIR}/.uv/bin/uv"
PYTHON_VERSION="3.11"

# ── Detect OS ──────────────────────────────────────────────────
detect_os() {
  case "$(uname -s)" in
    Darwin*)  echo "macos" ;;
    Linux*)   echo "linux" ;;
    CYGWIN*|MINGW*|MSYS*) echo "windows" ;;
    *)        echo "unknown" ;;
  esac
}

detect_arch() {
  case "$(uname -m)" in
    x86_64|amd64) echo "x86_64" ;;
    aarch64|arm64) echo "aarch64" ;;
    *)            echo "$(uname -m)" ;;
  esac
}

OS=$(detect_os)
ARCH=$(detect_arch)

# ── Prelude ────────────────────────────────────────────────────
title

if [ "$OS" = "windows" ]; then
  warn "Windows 原生支持尚在实验阶段，建议使用 WSL2。"
  info "安装 WSL2: wsl --install"
  info "然后在 WSL2 中执行本脚本。"
fi

info "系统: ${OS} (${ARCH})"
info "安装目录: ${INSTALL_DIR}"
info ""

# ── Dependency Check ───────────────────────────────────────────
step "检查系统依赖"

check_dep() {
  if command -v "$1" &>/dev/null; then
    ok "$1 已安装"
    return 0
  else
    warn "$1 未找到"
    return 1
  fi
}

MISSING=""
check_dep curl        || MISSING+=" curl"
check_dep git         || MISSING+=" git"
check_dep python3     || MISSING+=" python3"
check_dep pip3        || MISSING+=" pip3"

if [ -n "$MISSING" ]; then
  error "缺少依赖:${MISSING}"
  info "请先安装上述依赖再运行本脚本。"
  info "macOS: brew install curl git python"
  info "Ubuntu: sudo apt install curl git python3 python3-pip"
  exit 1
fi

# ── Create Directories ─────────────────────────────────────────
step "创建目录结构"

mkdir -p "${INSTALL_DIR}"
mkdir -p "${BIN_DIR}"
mkdir -p "${INSTALL_DIR}/data"
mkdir -p "${INSTALL_DIR}/data/memory"
mkdir -p "${INSTALL_DIR}/data/config"
mkdir -p "${INSTALL_DIR}/data/logs"
mkdir -p "${INSTALL_DIR}/data/avatars"

ok "目录创建完成"

# ── Install uv (Python Package Manager) ────────────────────────
step "安装 uv (Python 包管理器)"

if [ -f "${UV_BIN}" ]; then
  ok "uv 已安装 (${INSTALL_DIR}/.uv)"
else
  info "正在安装 uv..."
  export UV_INSTALL_DIR="${INSTALL_DIR}/.uv"
  curl -fsSL https://astral.sh/uv/install.sh | bash -s -- --no-modify-path 2>&1 | tail -1
  ok "uv 安装完成"
fi

# Make uv available
export PATH="${INSTALL_DIR}/.uv/bin:${PATH}"

# ── Clone / Download Repo ──────────────────────────────────────
step "获取 AI 夏娃 代码"

if [ -d "${INSTALL_DIR}/repo" ]; then
  info "正在更新..."
  cd "${INSTALL_DIR}/repo"
  git pull --ff-only origin "${BRANCH}" 2>&1 | tail -1
  ok "代码更新完成"
else
  info "正在克隆仓库..."
  git clone --depth 1 -b "${BRANCH}" "https://github.com/${REPO}.git" "${INSTALL_DIR}/repo" 2>&1 | tail -1
  ok "代码下载完成"
fi

# ── Create Virtual Environment & Install Dependencies ──────────
step "创建 Python 虚拟环境"

cd "${INSTALL_DIR}/repo"

if [ ! -d ".venv" ]; then
  info "创建 Python ${PYTHON_VERSION} 虚拟环境..."
  "${UV_BIN}" venv --python "${PYTHON_VERSION}" .venv 2>&1 | tail -1
  ok "虚拟环境创建完成"
fi

info "安装 Python 依赖..."
"${UV_BIN}" pip install -e "." 2>&1 | tail -3
ok "依赖安装完成"

# ── Install CLI Entry Point ────────────────────────────────────
step "安装 CLI 命令"

cat > "${INSTALL_DIR}/ai-eve" << 'ENTRY'
#!/usr/bin/env bash
set -euo pipefail
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="${INSTALL_DIR}/.uv/bin:${PATH}"
cd "${INSTALL_DIR}/repo"
exec "${INSTALL_DIR}/.uv/bin/uv" run python -m cli.main "$@"
ENTRY

chmod +x "${INSTALL_DIR}/ai-eve"

# Create symlink
ln -sf "${INSTALL_DIR}/ai-eve" "${BIN_DIR}/ai-eve"

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
  warn "${BIN_DIR} 不在 PATH 中，请添加:"
  echo "  export PATH=\"\${HOME}/.local/bin:\${PATH}\""
  echo "  或在 ~/.bashrc / ~/.zshrc 中添加上述行"
fi

# ── Create Default Config ──────────────────────────────────────
step "创建默认配置"

CONFIG_FILE="${INSTALL_DIR}/data/config/config.json"
if [ ! -f "${CONFIG_FILE}" ]; then
  cat > "${CONFIG_FILE}" << 'CONFIG'
{
  "version": "0.1.0",
  "model": {
    "provider": "",
    "api_key": "",
    "base_url": "",
    "name": ""
  },
  "persona": {
    "name": "夏娃",
    "english_name": "Eve",
    "style": "realistic",
    "personality": "温柔、知性、善解人意",
    "greeting": "你好，我是夏娃。很高兴认识你。"
  },
  "voice": {
    "enabled": false,
    "provider": "",
    "voice_id": ""
  },
  "platforms": {
    "telegram": {"enabled": false},
    "discord": {"enabled": false},
    "wechat": {"enabled": false},
    "feishu": {"enabled": false}
  },
  "memory": {
    "enabled": true,
    "type": "local"
  },
  "data_dir": "${INSTALL_DIR}/data"
}
CONFIG
  ok "默认配置已创建"
else
  info "配置文件已存在，跳过"
fi

# ── Done ───────────────────────────────────────────────────────
echo ""
title
ok "${BOLD}AI 夏娃 (AI Eve) 安装完成!${RESET}"
echo ""
info "快速开始:"
echo ""
echo "  ${GREEN}ai-eve setup${RESET}         # 交互式配置向导"
echo "  ${GREEN}ai-eve${RESET}                # 启动 CLI 对话"
echo "  ${GREEN}ai-eve web${RESET}            # 启动 Web UI"
echo "  ${GREEN}ai-eve help${RESET}           # 查看全部命令"
echo ""
info "安装目录: ${INSTALL_DIR}"
info "配置文件: ${CONFIG_FILE}"
echo ""

if [ "$OS" = "linux" ]; then
  info "需要安装 ffmpeg 以支持语音功能:"
  info "  Ubuntu/Debian: sudo apt install ffmpeg"
  info "  macOS: brew install ffmpeg"
fi
