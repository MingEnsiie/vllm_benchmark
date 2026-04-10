#!/bin/bash
# 启动本地 vLLM OpenAI 兼容服务。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV="$PROJECT_DIR/.vllm"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
MODEL_NAME="${MODEL_NAME:-Qwen3.5-0.8B}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"
TORCH_LIB_DIR="$VENV/lib/python3.12/site-packages/torch/lib"
CUDA_RUNTIME_DIR="${CUDA_RUNTIME_DIR:-/usr/local/lib/ollama/cuda_v12}"
EXTRA_ARGS=()

usage() {
    cat <<'EOF'
用法:
  ./scripts/start_vllm.sh [--model MODEL_NAME] [--host HOST] [--port PORT] [--max-model-len N] [--list-models] [--help] [额外 vLLM 参数]

示例:
  ./scripts/start_vllm.sh
  ./scripts/start_vllm.sh --model Qwen3.5-4B --port 8001
  ./scripts/start_vllm.sh --list-models
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)
            MODEL_NAME="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --max-model-len)
            MAX_MODEL_LEN="$2"
            shift 2
            ;;
        --list-models)
            "$PYTHON_BIN" "$PROJECT_DIR/vllm_local.py" list
            exit 0
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        --)
            shift
            EXTRA_ARGS+=("$@")
            break
            ;;
        *)
            EXTRA_ARGS+=("$1")
            shift
            ;;
    esac
done

if [[ ! -x "$VENV/bin/python" ]]; then
    echo "错误: 未找到虚拟环境 $VENV/bin/python"
    echo "请先运行 ./scripts/setup_vllm_env.sh"
    exit 1
fi

MODEL_PATH="$("$PYTHON_BIN" "$PROJECT_DIR/vllm_local.py" resolve --model "$MODEL_NAME" --field path)"
SERVED_MODEL_NAME="$("$PYTHON_BIN" "$PROJECT_DIR/vllm_local.py" resolve --model "$MODEL_NAME" --field served-name)"

source "$VENV/bin/activate"
export LD_LIBRARY_PATH="$TORCH_LIB_DIR:$CUDA_RUNTIME_DIR:${LD_LIBRARY_PATH:-}"

echo "启动 vLLM 服务..."
echo "模型名: $MODEL_NAME"
echo "模型目录: $MODEL_PATH"
echo "服务模型名: $SERVED_MODEL_NAME"
echo "地址: $HOST:$PORT"
echo "LD_LIBRARY_PATH: $TORCH_LIB_DIR:$CUDA_RUNTIME_DIR"
echo ""

python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "$SERVED_MODEL_NAME" \
    --host "$HOST" \
    --port "$PORT" \
    --max-model-len "$MAX_MODEL_LEN" \
    --dtype auto \
    --trust-remote-code \
    "${EXTRA_ARGS[@]}"
