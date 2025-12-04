#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$PROJECT_ROOT/infra/cdk"
VENV_DIR="$INFRA_DIR/.venv"
STACK_NAME="SmartDocProcessingStack"

info() { printf "[INFO] %s\n" "$*"; }
warn() { printf "[WARN] %s\n" "$*"; }
error() { printf "[ERROR] %s\n" "$*" >&2; }

command -v aws >/dev/null 2>&1 || { error "未检测到 aws CLI, 请先安装并执行 aws configure"; exit 1; }
command -v python3 >/dev/null 2>&1 || { error "未检测到 python3"; exit 1; }
command -v pip >/dev/null 2>&1 || { error "未检测到 pip"; exit 1; }

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  error "未检测到有效的 AWS 凭证, 请先运行 aws configure 或设置 AWS_PROFILE"
  exit 1
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  read -rsp "请输入 OPENAI_API_KEY: " OPENAI_API_KEY
  printf "\n"
fi

mkdir -p "$INFRA_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  info "创建 Python 虚拟环境"
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

info "安装/更新 Python 依赖"
pip install --upgrade pip
pip install -r "$INFRA_DIR/requirements.txt"

pushd "$INFRA_DIR" >/dev/null

if [[ "${SKIP_BOOTSTRAP:-0}" != "1" ]]; then
  info "执行 cdk bootstrap (每个 AWS 账户/区域仅需一次)"
  cdk bootstrap
else
  warn "跳过 cdk bootstrap"
fi

info "部署 $STACK_NAME"
OPENAI_API_KEY="$OPENAI_API_KEY" cdk deploy "$STACK_NAME" --require-approval never

popd >/dev/null

info "部署完成。API 与前端链接请查看 cdk 输出。"
