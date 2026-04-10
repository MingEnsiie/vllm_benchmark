# Multimodal Offline Evaluation TODO

目标：分步骤下载一套主流多模态评测数据集，优先保证图文通用能力可离线测评，再补充 OCR、文档、幻觉、视频专项。

## Phase 1: 先把通用主集拉齐

- [x] 建立统一目录结构
  - [x] `datasets/mmmu`
  - [x] `datasets/mmbench`
  - [x] `datasets/mmstar`
  - [x] `datasets/mathvista`
  - [x] `datasets/scienceqa`
- [x] 下载 `MMMU`
  - [x] 记录来源、版本号、下载日期
  - [x] 检查是否包含图片和题目标注
  - [x] 抽样确认本地能正常读取
- [x] 下载 `MMBench`
  - [x] 优先确认使用中文、英文，还是全量版本
  - [x] 保存原始 TSV/JSON 与图片目录
  - [x] 记录评测字段含义
- [x] 下载 `MMStar`
  - [x] 确认图片文件和题目标注一一对应
  - [x] 抽查样本是否能离线加载
- [x] 下载 `MathVista`
  - [x] 确认答案字段、题型字段是否完整
  - [x] 统计可直接离线跑的样本数
- [x] 下载 `ScienceQA`
  - [x] 保留题目、图片、lecture、explanation
  - [x] 区分纯文本题和多模态题

## Phase 2: 补 OCR / 图表 / 文档能力

- [x] 建立专项目录
  - [x] `datasets/chartqa`
  - [x] `datasets/ocrbench`
  - [x] `datasets/docvqa`
- [x] 下载 `ChartQA`
  - [x] 检查图表图片是否完整
  - [x] 确认答案格式是自由文本还是数值
- [x] 下载 `OCRBench`
  - [x] 确认样本是否可直接离线使用
  - [x] 记录评测维度，后续方便分项打分
- [x] 下载 `DocVQA`
  - [x] 先确认是否需要注册账号和同意协议
  - [x] 下载后保存 license / terms 说明
  - [x] 校验图片与标注数量是否一致

## Phase 3: 补诊断型和幻觉专项

- [ ] 建立专项目录
  - [ ] `datasets/mme`
  - [ ] `datasets/hallusionbench`
  - [ ] `datasets/pope`
  - [ ] `datasets/mmvet`
- [ ] 下载 `MME`
  - [ ] 按 perception / cognition 分类整理
  - [ ] 确认官方打分方式
- [ ] 下载 `HallusionBench`
  - [ ] 记录是否有特殊 prompt 要求
  - [ ] 标记需要人工复核的题型
- [ ] 下载 `POPE`
  - [ ] 整理不同子集设置
  - [ ] 标注其主要用于 object hallucination
- [ ] 下载 `MM-Vet`
  - [ ] 记录样本量较小但难度较高
  - [ ] 确认答案匹配方式

## Phase 4: 视情况补视频评测

- [ ] 建立视频目录
  - [ ] `datasets/video_mme`
  - [ ] `datasets/seed_bench`
- [ ] 调研 `Video-MME`
  - [ ] 确认下载许可、体积、视频来源限制
  - [ ] 判断当前机器是否适合离线跑视频评测
- [ ] 调研 `SEED-Bench`
  - [ ] 确认图像部分和视频部分是否分开获取
  - [ ] 记录哪些内容需要从原始来源补齐
- [ ] 如果磁盘或时间有限，视频评测后置

## Phase 5: 每下载完一个数据集就做的事

- [ ] 记录到 `datasets/README.md`
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

## 推荐下载顺序

1. `MMMU`
2. `MMBench`
3. `MMStar`
4. `MathVista`
5. `ScienceQA`
6. `ChartQA`
7. `OCRBench`
8. `DocVQA`
9. `MME`
10. `HallusionBench`
11. `POPE`
12. `MM-Vet`
13. `Video-MME`
14. `SEED-Bench`

## 备注

- `优先级最高`：`MMMU + MMBench + MMStar + MathVista + ScienceQA`
- `文档/OCR 必补`：`ChartQA + OCRBench + DocVQA`
- `诊断能力建议补`：`MME + HallusionBench + POPE + MM-Vet`
- `视频评测最后做`：体积大、准备成本高、依赖更复杂

## 官方入口

### 通用图文

- `MMMU`
  - 官方数据集: `https://huggingface.co/datasets/MMMU/MMMU`
- `MMBench`
  - 官方仓库: `https://github.com/open-compass/MMBench`
  - 说明: 下载链接在仓库 README 的表格里
- `MMStar`
  - 官方数据集: `https://huggingface.co/datasets/Lin-Chen/MMStar`
- `MathVista`
  - 官方数据集: `https://huggingface.co/datasets/AI4Math/MathVista`
- `ScienceQA`
  - 常用 Hugging Face 镜像: `https://huggingface.co/datasets/TheMrguiller/ScienceQA`

### OCR / 图表 / 文档

- `ChartQA`
  - 常用 Hugging Face 镜像: `https://huggingface.co/datasets/HuggingFaceM4/ChartQA`
- `OCRBench`
  - 官方仓库: `https://github.com/Yuliang-Liu/MultimodalOCR`
  - 常用 Hugging Face 数据集: `https://huggingface.co/datasets/echo840/OCRBench`
- `DocVQA`
  - 官方数据页: `https://site.docvqa.org/datasets/docvqa`
  - 说明: 需要登录 RRC portal 并同意条款后下载

### 诊断 / 幻觉

- `MME`
  - 官方主页: `https://mme-benchmark.github.io/home_page.html`
- `HallusionBench`
  - 常用 Hugging Face 格式化版本: `https://huggingface.co/datasets/lmms-lab/HallusionBench`
- `POPE`
  - 官方仓库: `https://github.com/RUCAIBox/POPE`
- `MM-Vet`
  - 常用 Hugging Face 格式化版本: `https://huggingface.co/datasets/lmms-lab/MMVet`

### 视频

- `Video-MME`
  - 官方仓库: `https://github.com/MME-Benchmarks/Video-MME`
  - 官方主页: `https://video-mme.github.io/`
  - 说明: 官方明确限制分发与商用，先看 license 再下
- `SEED-Bench`
  - 官方仓库: `https://github.com/AILab-CVC/SEED-Bench`
  - 官方数据集: `https://huggingface.co/datasets/AILab-CVC/SEED-Bench`
  - 说明: 视频部分通常只给视频名，需要去原始来源下载

## 下载命令模板

### 先准备目录

```bash
mkdir -p datasets/{mmmu,mmbench,mmstar,mathvista,scienceqa,chartqa,ocrbench,docvqa,mme,hallusionbench,pope,mmvet,video_mme,seed_bench}
```

### Hugging Face 数据集通用模板

适合 `MMMU`、`MMStar`、`MathVista`、`ScienceQA`、`ChartQA`、`OCRBench`、`HallusionBench`、`MM-Vet`、`SEED-Bench`

```bash
huggingface-cli download <repo_id> --repo-type dataset --local-dir datasets/<name>
```

示例

```bash
huggingface-cli download MMMU/MMMU --repo-type dataset --local-dir datasets/mmmu
huggingface-cli download Lin-Chen/MMStar --repo-type dataset --local-dir datasets/mmstar
huggingface-cli download AI4Math/MathVista --repo-type dataset --local-dir datasets/mathvista
huggingface-cli download TheMrguiller/ScienceQA --repo-type dataset --local-dir datasets/scienceqa
huggingface-cli download HuggingFaceM4/ChartQA --repo-type dataset --local-dir datasets/chartqa
huggingface-cli download echo840/OCRBench --repo-type dataset --local-dir datasets/ocrbench
huggingface-cli download lmms-lab/HallusionBench --repo-type dataset --local-dir datasets/hallusionbench
huggingface-cli download lmms-lab/MMVet --repo-type dataset --local-dir datasets/mmvet
huggingface-cli download AILab-CVC/SEED-Bench --repo-type dataset --local-dir datasets/seed_bench
```

如果你更习惯 `python`

```python
from huggingface_hub import snapshot_download

snapshot_download(repo_id="MMMU/MMMU", repo_type="dataset", local_dir="datasets/mmmu")
```

### GitHub 仓库型数据集模板

适合 `MMBench`、`POPE`、`OCRBench` 官方仓库、`Video-MME`

```bash
git clone <repo_url> datasets/<name>_repo
```

示例

```bash
git clone https://github.com/open-compass/MMBench datasets/mmbench_repo
git clone https://github.com/RUCAIBox/POPE datasets/pope_repo
git clone https://github.com/Yuliang-Liu/MultimodalOCR datasets/ocrbench_repo
git clone https://github.com/MME-Benchmarks/Video-MME datasets/video_mme_repo
git clone https://github.com/AILab-CVC/SEED-Bench datasets/seed_bench_repo
```

### 需要手工下载或先过协议的

- `MMBench`
  - [ ] 打开官方仓库 README
  - [ ] 在表格里选择 `Legacy` 或 `VLMEvalKit` 版本
  - [ ] 下载后放到 `datasets/mmbench`
- `DocVQA`
  - [ ] 注册并登录 RRC portal
  - [ ] 阅读并接受下载条款
  - [ ] 下载后解压到 `datasets/docvqa`
- `Video-MME`
  - [ ] 先阅读官方 license
  - [ ] 再决定是否本地保存完整视频
- `SEED-Bench`
  - [ ] 图像部分可直接取
  - [ ] 视频部分按官方说明去原始来源补齐

## 本次实际下载备注

- `DocVQA` 本次落地使用的是公开镜像 `HuggingFaceM4/DocumentVQA`，目录为 `datasets/docvqa`
- `DocVQA` 官方站点仍然是需要登录并接受条款的受限入口

## 每个数据集下载后的最小检查命令

### 看目录结构

```bash
find datasets/mmmu -maxdepth 2 | sed -n '1,40p'
```

### 看文件体积

```bash
du -sh datasets/mmmu
```

### 抽样列目录

```bash
ls datasets/mmmu | sed -n '1,40p'
```

### 如果是 parquet 或 json，抽样检查字段

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("datasets")
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

- `MMMU` 数据卡在 `2026-02-12` 明确说明测试集答案已公开，可本地离线测评
- `MMBench` 官方仓库同时提供 `VLMEvalKit` 和 `Legacy` 两种下载格式，离线自定义评测通常优先看 `Legacy`
- `DocVQA` 官方站点要求登录后下载
- `Video-MME` 官方仓库声明仅限学术研究，且禁止未授权分发、发布、复制或修改
- `SEED-Bench` 的视频数据不是完整打包直给，通常需要从原始来源补齐
