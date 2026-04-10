#!/bin/bash
# 创建或校验当前目录下的 .vllm Python 3.12 虚拟环境。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.vllm"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
PYTORCH_INDEX_URL="${PYTORCH_INDEX_URL:-https://download.pytorch.org/whl/cu130}"
REINSTALL=0

usage() {
    cat <<'EOF'
用法:
  ./scripts/setup_vllm_env.sh [--reinstall] [--help]

说明:
  默认复用已有 .vllm；如果缺包会安装 requirements-vllm.txt。
  使用 --reinstall 时，会在现有虚拟环境上重新执行安装。
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reinstall)
            REINSTALL=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            usage
            exit 1
            ;;
    esac
done

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "错误: 找不到 $PYTHON_BIN"
    exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    echo "创建虚拟环境: $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

if [[ "$REINSTALL" -eq 1 ]]; then
    NEED_INSTALL=1
else
    if python -c "import openai, torch, vllm; raise SystemExit(0 if getattr(torch.version, 'cuda', None) == '13.0' and torch.cuda.is_available() else 1)" >/dev/null 2>&1; then
        NEED_INSTALL=0
    else
        NEED_INSTALL=1
    fi
fi

if [[ "$NEED_INSTALL" -eq 1 ]]; then
    python -m pip install --upgrade pip
    python -m pip install --upgrade --force-reinstall \
        --index-url "$PYTORCH_INDEX_URL" \
        torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0
    python -m pip install --upgrade --force-reinstall openai==2.30.0
    python -m pip install --upgrade --force-reinstall --no-deps vllm==0.19.0
    python -m pip install --upgrade --force-reinstall \
        --index-url "$PYTORCH_INDEX_URL" \
        torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0
fi

echo "虚拟环境就绪: $VENV_DIR"
python -V
python -c "import openai, torch, vllm; print('vllm=', vllm.__version__); print('torch=', torch.__version__); print('torch.cuda=', torch.version.cuda); print('cuda_available=', torch.cuda.is_available()); print('openai=', openai.__version__)"
