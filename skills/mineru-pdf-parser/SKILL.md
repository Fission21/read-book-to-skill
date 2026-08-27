---
name: mineru-pdf-parser
description: 用 MinerU 解析 PDF 为 Markdown/JSON 时用。含国内模型下载、M1 内存调优、踩坑速查。
version: 1.0.0
author: CC
tags: [mineru, pdf, ocr, parsing, 文档解析]
---

# MinerU PDF 解析（Mac M1 部署 + 使用）

## 触发条件

- 需要把 PDF（含扫描件/图片型 PDF）解析成 Markdown、JSON、结构化文本
- 用户发来 PDF 要提取内容/做知识库
- MinerU 报模型缺失/下载失败

## 环境（2026-08-27 实测，macOS Apple Silicon）

- 位置：`<你的工作目录>/mineru-venv/`（独立 venv，mineru 3.4.5）
- 模型目录：`<你的工作目录>/mineru-models/`（15 个文件 1.0GB，sha256 全部验证过）
- 配置：`~/mineru.json` → `models-dir.pipeline: <你的工作目录>/mineru-models`
- 中文公式支持默认关（`MINERU_FORMULA_CH_SUPPORT` 未设时用 unimernet_small 而非 pp_formulanet）

## 基本用法

```bash
unset PYTHONPATH   # 必须！否则加载 Hermes venv 的包
<你的工作目录>/mineru-venv/bin/mineru \
  -p "输入.pdf" -o 输出目录 -b pipeline
```

- `-b pipeline`：本地模型解析（默认 hybrid-engine 需要 VLM 模型，别用）
- 输出：`输出目录/<文件名>/auto/` 下含 `*.md`、`*_model.json`、`*_span.pdf`、`images/`
- 252 页书全量解析约 4-6 分钟（M1 Pro）

## ⚠️ 关键坑（全部实测踩过）

### 1. 模型下载失败（国内网络）
- **根因 A**：`hf download opendatalab/PDF-Extract-Kit-1.0` 会拉**整个 repo 10GB+**，但 MinerU 3.4.5 pipeline **只需要 7 个子路径约 1GB**（Layout/PP-DocLayoutV2、MFR/unimernet_hf_small_2503、OCR/paddleocr_torch、TabRec/SlanetPlus、TabRec/UnetStructure、TabCls/paddle_table_cls；pp_formulanet 仅当开中文公式时才要）
- **根因 B**：hf-mirror **直连 = 0 字节**（被墙），必须**走代理**（6.2MB/s）；或直接 **modelscope + 代理**（4.9MB/s，aria2 -x8 下 810MB 仅 20 秒）
- **hf CLI 走 hf-mirror 会报 `does not seem to be on huggingface.co`**（域名校验）→ 别用 hf CLI，用 curl/aria2 直下 resolve URL

### 2. M1 Mac 内存崩溃
- 默认窗口 64 页/批，长文档跑 3-4 批后 **MPS 内存累积崩溃**（Layout Predict 中途报错，无 traceback，输出目录空）
- **解法：`export MINERU_PROCESSING_WINDOW_SIZE=32`**（32 页/批稳定跑完 252 页）
- 症状特征：前几批正常、最后批 Layout 阶段进程退出 + `resource_tracker: leaked semaphore objects`

### 3. PYTHONPATH 污染
- Hermes 会话注入的 PYTHONPATH 会污染 mineru venv → 跑前必须 `unset PYTHONPATH`

### 4. 下载验证
- 大文件 sha256 验证：HF resolve URL 的 `?download=true` HEAD 响应里 `x-linked-etag` 就是官方 sha256，`shasum -a 256` 对比
- aria2 从 modelscope 下的文件也要验（之前 hf-mirror 的 aria2 下载就损坏过一次：大小对但 sha 不对）

## 模型文件清单（验证过的完整列表）

```
models/Layout/PP-DocLayoutV2/{config.json, preprocessor_config.json, model.safetensors 214MB}
models/MFR/unimernet_hf_small_2503/{config.json, generation_config.json, special_tokens_map.json, tokenizer.json, tokenizer_config.json, README.md, model.safetensors 810MB}
models/OCR/paddleocr_torch/{ch_PP-OCRv6_small_det_infer.safetensors 9.9MB, ch_PP-OCRv6_small_rec_infer.safetensors 21.2MB}
models/TabRec/SlanetPlus/slanet-plus.onnx 7.7MB
models/TabRec/UnetStructure/unet.onnx 8.3MB
models/TabCls/paddle_table_cls/PP-LCNet_x1_0_table_cls.onnx 6.7MB
```

## 相关

- book-to-skill skill：把解析出的 Markdown 打包成可复用 skill
- 模型下载替代方案：modelscope `snapshot_download`（MinerU 官方支持 MINERU_MODEL_SOURCE=modelscope）
