# Multimodal Eval TODO

目标：按最新推荐集合维护离线评测待办，优先覆盖端侧必测项；已下载并完成落地的旧数据集不再继续保留在主 TODO 中。

## 推荐基线

| Benchmark | 主要能力 | 是否建议端侧必测 | 说明 |
| --- | --- | ---: | --- |
| `MMMU-Pro` | 多模态图文理解 | 是 | 多模态主 benchmark |
| `OmniDocBench` | 文档理解 / OCR | 是 | 文档场景核心 |
| `LongBench v2` | 长文档理解 | 是 | 长内容问答 / 总结核心 |
| `IFEval` | 指令跟随 | 是 | 输出稳定性核心 |
| `Video-MME` | 视频理解 | 是 | 有视频场景时必测 |
| `BFCL-V4` | 工具调用 | 是 | Agent 基础能力核心 |
| `Tau2 (avg over 3)` | 多步任务完成 | 选测 | 更偏系统级 agent 完成度 |
| `MRCR v2` | 长上下文检索 | 选测 | 强调精准找点 |
| `MMMLU` | 多语言理解 | 选测 | 有国际化需求再加 |

## 当前待办

说明：这里只保留当前还需要推进的 benchmark；历史上已经下载落地的 `MMMU / MMBench / MMStar / MathVista / ScienceQA / ChartQA / OCRBench / DocVQA` 不再重复列为主待办。

## P0: 端侧必测

- [ ] `MMMU-Pro`
  - [ ] 明确与现有 `MMMU` 的差异，确认是否需要单独下载或单独评测脚本
  - [ ] 记录官方入口、版本、下载日期
  - [ ] 抽样确认本地可离线读取
- [ ] `OmniDocBench`
  - [ ] 确认 license、下载方式、样本组织形式
  - [ ] 标注文档理解、OCR、表格等子任务维度
  - [ ] 准备最小可跑样例
- [ ] `LongBench v2`
  - [ ] 确认任务子集是否覆盖长文问答、总结、检索
  - [ ] 明确是否需要长上下文文本输入而非视觉输入
  - [ ] 统一输出字段，方便接评测框架
- [ ] `IFEval`
  - [ ] 确认官方打分规则与 prompt 约束
  - [ ] 保留原始任务描述与 expected behavior
  - [ ] 准备稳定复现实验脚本
- [ ] `BFCL-V4`
  - [ ] 确认函数调用 / 工具调用 schema
  - [ ] 记录评测所需工具执行环境
  - [ ] 区分纯模型能力与 agent runtime 依赖
- [ ] `Video-MME`
  - [ ] 确认下载许可、体积、视频来源限制
  - [ ] 判断当前机器是否适合离线跑视频评测
  - [ ] 有视频场景再进入正式下载

## P1: 选测

- [ ] `Tau2 (avg over 3)`
  - [ ] 明确是否必须多次运行取平均
  - [ ] 确认任务是否依赖完整 agent runtime
- [ ] `MRCR v2`
  - [ ] 确认数据格式、上下文长度要求、打分方式
  - [ ] 评估是否与 `LongBench v2` 有明显重叠
- [ ] `MMMLU`
  - [ ] 有国际化需求时再补
  - [ ] 确认语言覆盖范围与评测成本

## 通用收尾项

- [ ] 记录到 `../Assets/datasets/README.md`
  - [ ] 数据集名称
  - [ ] 官方链接
  - [ ] 下载日期
  - [ ] 本地路径
  - [ ] 许可限制
  - [ ] 样本数
  - [ ] 任务类型
- [ ] 为每个数据集保留一份原始元数据，不直接改原文件
- [ ] 写一个最小校验脚本，确认
  - [ ] 样本总数正确
  - [ ] 图片路径可访问
  - [ ] 标注字段完整
  - [ ] 至少能随机取 10 条样本跑通
- [ ] 统一输出格式，方便后面接评测框架
  - [ ] `question`
  - [ ] `image` 或 `video`
  - [ ] `choices`
  - [ ] `answer`
  - [ ] `task_type`
  - [ ] `source_dataset`

## 推荐推进顺序

1. `MMMU-Pro`
2. `OmniDocBench`
3. `LongBench v2`
4. `IFEval`
5. `BFCL-V4`
6. `Video-MME`
7. `Tau2 (avg over 3)`
8. `MRCR v2`
9. `MMMLU`

## 备注

- `端侧主集合`：`MMMU-Pro + OmniDocBench + LongBench v2 + IFEval + BFCL-V4`
- `视频项按场景开启`：`Video-MME`
- `系统级与专项补充`：`Tau2 (avg over 3) + MRCR v2 + MMMLU`
- `已下载旧集不再占用主 TODO`：避免文档里长期保留已完成历史项

## 官方入口

### 端侧必测

- `MMMU-Pro`
  - 官方仓库: `https://github.com/MMMU-Benchmark/MMMU`
  - 官方数据集: `https://huggingface.co/datasets/MMMU/MMMU`
  - 说明: `MMMU-Pro` 与 `MMMU` 共用同一官方仓库，但需单独确认使用的子目录 / 配置
- `OmniDocBench`
  - 官方仓库: `https://github.com/opendatalab/OmniDocBench`
  - 官方数据集: `https://huggingface.co/datasets/opendatalab/OmniDocBench`
- `LongBench v2`
  - 官方主页: `https://longbench2.github.io/`
  - 官方数据集: `https://huggingface.co/datasets/THUDM/LongBench-v2`
  - 官方仓库: `https://github.com/THUDM/LongBench`
- `IFEval`
  - 数据集: `https://huggingface.co/datasets/google/IFEval`
  - 说明: 更偏文本指令跟随评测，通常不需要单独下载大规模多模态资源
- `Video-MME`
  - 官方仓库: `https://github.com/MME-Benchmarks/Video-MME`
  - 官方主页: `https://video-mme.github.io/`
  - 说明: 官方明确限制分发与商用，先看 license 再下
- `BFCL-V4`
  - 官方榜单 / 说明: `https://gorilla.cs.berkeley.edu/leaderboard.html`
  - 数据集入口: `https://huggingface.co/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard`
  - 说明: `v4` 包含 web search、memory、format sensitivity 等 agentic tool-use 评测

### 选测

- `Tau2 (avg over 3)`
  - 官方仓库: `https://github.com/sierra-research/tau2-bench`
  - 说明: 更像 agent 环境评测，通常不是单纯下载一个静态数据集就能跑
- `MRCR v2`
  - 数据集参考: `https://huggingface.co/datasets/openai/mrcr`
  - 说明: 文档里先按长上下文检索基准跟踪；`v2` 的具体评测封装需要后续再核对
- `MMMLU`
  - 官方数据集: `https://huggingface.co/datasets/openai/MMMLU`
  - 说明: 多语言通识评测，适合国际化需求场景

## 下载命令模板

### 先准备目录

```bash
mkdir -p ../Assets/datasets/{mmmu_pro,omnidocbench,longbench_v2,ifeval,video_mme,bfcl_v4,tau2,mrcr_v2,mmmlu}
```

### Hugging Face 数据集通用模板

适合 `MMMU-Pro`、`OmniDocBench`、`LongBench v2`、`IFEval`、`MRCR v2`、`MMMLU`

```bash
huggingface-cli download <repo_id> --repo-type dataset --local-dir ../Assets/datasets/<name>
```

示例

```bash
huggingface-cli download MMMU/MMMU --repo-type dataset --local-dir ../Assets/datasets/mmmu_pro
huggingface-cli download opendatalab/OmniDocBench --repo-type dataset --local-dir ../Assets/datasets/omnidocbench
huggingface-cli download THUDM/LongBench-v2 --repo-type dataset --local-dir ../Assets/datasets/longbench_v2
huggingface-cli download google/IFEval --repo-type dataset --local-dir ../Assets/datasets/ifeval
huggingface-cli download openai/mrcr --repo-type dataset --local-dir ../Assets/datasets/mrcr_v2
huggingface-cli download openai/MMMLU --repo-type dataset --local-dir ../Assets/datasets/mmmlu
```

如果你更习惯 `python`

```python
from huggingface_hub import snapshot_download

snapshot_download(repo_id="THUDM/LongBench-v2", repo_type="dataset", local_dir="../Assets/datasets/longbench_v2")
```

### GitHub 仓库型数据集模板

适合 `OmniDocBench` 评测代码、`Video-MME`、`Tau2`

```bash
git clone <repo_url> ../Assets/datasets/<name>_repo
```

示例

```bash
git clone https://github.com/opendatalab/OmniDocBench ../Assets/datasets/omnidocbench_repo
git clone https://github.com/MME-Benchmarks/Video-MME ../Assets/datasets/video_mme_repo
git clone https://github.com/sierra-research/tau2-bench ../Assets/datasets/tau2_repo
```

### 需要手工下载或先过协议的

- `Video-MME`
  - [ ] 先阅读官方 license
  - [ ] 再决定是否本地保存完整视频
- `BFCL-V4`
  - [ ] 先确认 `v4` 使用的数据集版本和评测代码版本
  - [ ] 再确定是否需要联网能力或外部搜索 API
- `Tau2 (avg over 3)`
  - [ ] 先确认运行依赖、环境模拟器和多次运行平均方式
- `MRCR v2`
  - [ ] 先确认当前采用 `openai/mrcr` 是否足够代表目标评测
  - [ ] 如需严格 `v2` 口径，再补充版本映射说明

## 本次文档更新备注

- 这次主文档已经切换到新的 benchmark 选择表
- 已下载完成的旧集保留为历史资产，但不再占用主 TODO
- `MRCR v2` 这里先记录为与 `openai/mrcr` 对齐的候选入口；如果后续要严格复现实验口径，需要再补充版本核对

## 每个数据集下载后的最小检查命令

### 看目录结构

```bash
find ../Assets/datasets/<name> -maxdepth 2 | sed -n '1,40p'
```

### 看文件体积

```bash
du -sh ../Assets/datasets/<name>
```

### 抽样列目录

```bash
ls ../Assets/datasets/<name> | sed -n '1,40p'
```

### 如果是 parquet 或 json，抽样检查字段

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("../Assets/datasets")
for p in path.rglob("*.json"):
    print("JSON:", p)
    with open(p, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if isinstance(obj, dict):
        print(list(obj.keys())[:20])
    break
PY
```

## 下载时的注意点

- `MMMU-Pro` 需要和现有 `MMMU` 明确区分评测入口，不要直接把旧脚本当成 `Pro` 结果
- `OmniDocBench` 同时覆盖文档解析、OCR、表格、公式等维度，接入前先定清楚只测哪一层能力
- `LongBench v2`、`IFEval`、`MRCR v2` 本质更偏长上下文 / 指令跟随文本评测，不一定需要多模态输入链路
- `BFCL-V4` 和 `Tau2` 更偏 agent / tool-use / system 级评测，通常比单数据集离线打分更复杂
- `Video-MME` 官方仓库声明仅限学术研究，且禁止未授权分发、发布、复制或修改
