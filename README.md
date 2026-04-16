# vLLM 本地推理框架

在本机 GPU 上运行大语言模型，提供 OpenAI 兼容接口，支持终端聊天和性能测试。

## 项目结构

```
vllm/
├── vllm_local.py          # 核心库：本地模型发现与解析
├── local_chat.py          # 终端聊天客户端
│
├── scripts/               # 运行脚本
│   ├── setup_vllm_env.sh  # 一键初始化 Python 虚拟环境
│   ├── start_vllm.sh      # 启动 vLLM OpenAI 兼容服务
│   └── benchmark_speed.py # 并发性能基准测试
│
├── tests/                 # 单元测试
│   ├── test_vllm_local.py # 测试模型发现/解析逻辑
│   └── test_local_chat.py # 测试聊天客户端核心逻辑
│
└── docs/                  # 设计文档与规格说明

../Assets/                 # 上级目录中的本地大体积资产（不纳入版本控制）
├── models/                # 本地模型目录
└── datasets/              # 多模态评测数据集
```

## 快速开始

### 1. 初始化环境

```bash
./scripts/setup_vllm_env.sh
```

安装 Python 3.12 虚拟环境（`.vllm/`），包含 vLLM 0.19.0、PyTorch 2.10.0+cu130、OpenAI SDK。

### 2. 启动推理服务

```bash
# 使用默认模型（Qwen3.5-0.8B）
./scripts/start_vllm.sh

# 指定模型
./scripts/start_vllm.sh --model Qwen3.5-4B

# 自定义端口
./scripts/start_vllm.sh --model Qwen3.5-9B --port 8001

# 查看可用模型列表
./scripts/start_vllm.sh --list-models
```

服务启动后监听 `http://0.0.0.0:8000`，提供 OpenAI 兼容接口。

### 3. 终端聊天

```bash
# 激活虚拟环境
source .vllm/bin/activate

# 启动聊天（自动连接本地服务）
python local_chat.py

# 显示思考过程
python local_chat.py --show-thinking

# 关闭 Qwen3.5 思考模式
python local_chat.py --no-thinking
```

输入 `exit` 或 `quit` 退出对话。

### 4. 性能基准测试

```bash
source .vllm/bin/activate

# 默认测试 2路、4路并发
python scripts/benchmark_speed.py

# 指定并发数和请求数
python scripts/benchmark_speed.py --concurrency 1 2 4 8 --num-requests 32

# 测试长上下文（目标 2048 输入 tokens）
python scripts/benchmark_speed.py --prompt-tokens 2048 --concurrency 4 8
```

## 本地模型

模型存放于 `../Assets/models/<模型名>/`，需包含 `config.json` 和权重文件（`.safetensors`）才会被识别。

```bash
# 列出所有可用模型
python vllm_local.py list

# 解析指定模型路径
python vllm_local.py resolve --model Qwen3.5-4B --field path
```

当前已有模型：

| 模型 | 系列 |
|------|------|
| Qwen3.5-0.8B | Qwen |
| Qwen3.5-2B | Qwen |
| Qwen3.5-4B | Qwen |
| Qwen3.5-9B | Qwen |
| Qwen3.5-27b-GPTQ-Int4 | Qwen (量化) |
| Qwen3.5-35B-A3B-GPTQ-Int4 | Qwen (量化 MoE) |
| Qwen3-Omni-30B-A3B-Instruct | Qwen Omni |
| Qwopus3.5-27B-v3 | Qwen |
| gemma-4-E2B-it | Gemma 4 |
| gemma-4-E4B-it | Gemma 4 |
| gemma-4-26B-A4B-it | Gemma 4 (MoE) |
| gemma-4-31B-it | Gemma 4 |
| Gemma-4-31B-JANG_4M-CRACK | Gemma 4 |

## 多模态评测数据集

数据集存放于 `../Assets/datasets/`，已下载：

| 数据集 | 类型 | 阶段 |
|--------|------|------|
| MMMU | 通用图文 | Phase 1 ✓ |
| MMBench | 通用图文 | Phase 1 ✓ |
| MMStar | 通用图文 | Phase 1 ✓ |
| MathVista | 数学视觉 | Phase 1 ✓ |
| ScienceQA | 科学问答 | Phase 1 ✓ |
| ChartQA | 图表理解 | Phase 2 ✓ |
| OCRBench | OCR | Phase 2 ✓ |
| DocVQA | 文档问答 | Phase 2 ✓ |

Phase 3（幻觉/诊断）和 Phase 4（视频）待补充，详见 [multimodal_eval_todolist.md](multimodal_eval_todolist.md)。

## 选型文档

- [../Assets/models 与 ../Assets/datasets 实验选型参考手册](docs/2026-04-10-models-datasets-selection-handbook.md)

## 运行测试

```bash
# 从项目根目录执行
python3 -m unittest tests.test_vllm_local tests.test_local_chat -v
```

## 环境说明

| 组件 | 版本 |
|------|------|
| Python | 3.12 |
| vLLM | 0.19.0 |
| PyTorch | 2.10.0+cu130 |
| OpenAI SDK | 2.30.0 |
| CUDA | 13.0 |

虚拟环境位于 `.vllm/`，不纳入版本控制。

## API 接口

服务启动后，所有标准 OpenAI API 均可用：

```bash
# 查看已加载模型
curl http://localhost:8000/v1/models

# 发起对话
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen3.5-0.8B", "messages": [{"role": "user", "content": "你好"}]}'
```
