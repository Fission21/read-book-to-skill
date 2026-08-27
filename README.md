# read-book-to-skill — 读书封装 Skill 流程

> 把一本书/一份 PDF 变成 AI Agent 可复用的 Skill 的完整流水线：
> **安装 MinerU（OCR 解析）→ 识别 PDF → 提炼方法论 → 封装成 Skill**

这套流程由 CC（Hermes Agent）在 2026-08-27 实测跑通：将《Refactoring UI》（252 页 PDF）成功封装为 `refactoring-ui-principles` skill。

## 📦 仓库结构

```
read-book-to-skill/
├── README.md                                    # 本文件：流程总览 + 依赖说明
└── skills/
    ├── mineru-pdf-parser/SKILL.md               # 【前置依赖 1】MinerU PDF 解析（安装/下载/踩坑）
    └── read-book-to-skill/SKILL.md              # 【主流程】读书 → 封装 Skill 的 6 步流水线
```

## 🔄 完整流程

```
┌─────────────────────────────────────────────────────────────┐
│  ① 安装 MinerU + 下载模型（国内网络优化）                      │
│     → mineru-pdf-parser skill（前置依赖 1）                    │
├─────────────────────────────────────────────────────────────┤
│  ② 解析 PDF → Markdown                                       │
│     mineru -p 输入.pdf -o 输出目录 -b pipeline                │
│     (252 页 ≈ 4-6 分钟，输出完整 md/json/span.pdf)            │
├─────────────────────────────────────────────────────────────┤
│  ③ 通读全书（REPL 式分段读，先读目录定骨架）                   │
├─────────────────────────────────────────────────────────────┤
│  ④ 判断封装形态：速查式 / 步骤式 / 人物式                      │
├─────────────────────────────────────────────────────────────┤
│  ⑤ 生成 SKILL.md（精炼原则+数值落地）+ 全文存档 references/    │
│     → read-book-to-skill skill（主流程）                      │
├─────────────────────────────────────────────────────────────┤
│  ⑥ 验证（skill_view 加载 + 真实场景实跑）+ 交付                │
└─────────────────────────────────────────────────────────────┘
```

## 📋 前置依赖（两个 skill）

| Skill | 作用 | 依赖关系 |
|-------|------|---------|
| **`mineru-pdf-parser`** | MinerU 部署、模型下载（国内网络优化）、M1 Mac 调优、踩坑速查 | 主流程 Step ①/② 依赖 |
| **`read-book-to-skill`** | 读书 → 封装 Skill 的 6 步完整流程 | 主流程本体 |

主流程 skill 在 Step 1 会**先加载 `mineru-pdf-parser`** 获取环境与坑，再执行解析。两者必须一起安装。

## 🚀 快速开始

```bash
# 1. 安装 MinerU（Python 3.10+，建议独立 venv）
python3 -m venv mineru-venv
mineru-venv/bin/pip install "mineru[core]"

# 2. 下载模型（约 1GB，只需 7 个子路径，别拉全量 10GB repo）
#    国内网络：走代理访问 hf-mirror（6.2MB/s）或 modelscope+aria2（20 秒下 810MB）
#    详见 mineru-pdf-parser/SKILL.md 的模型文件清单

# 3. 配置 ~/mineru.json 的 models-dir.pipeline 指向模型目录

# 4. 解析 PDF
unset PYTHONPATH
export MINERU_PROCESSING_WINDOW_SIZE=32   # 长文档防 MPS 崩溃（Apple Silicon 关键！）
mineru-venv/bin/mineru -p 输入.pdf -o 输出目录 -b pipeline

# 5. 把生成的两个 SKILL.md 放入你的 Agent 的 skills 目录
#    （Hermes: ~/.hermes/skills/；其他 Agent 见 read-book-to-skill 内的兼容说明）

# 6. 对你的 Agent 说："把这本书封装成 skill"
```

## ⚠️ 关键坑速查（全部实测）

| 坑 | 解法 |
|----|------|
| `hf download` 拉全量 repo（10GB+） | 只需 7 个子路径约 1GB，用 curl/aria2 直下 resolve URL |
| hf-mirror 直连 0 字节（被墙） | 走代理（6.2MB/s）或 modelscope（4.9MB/s） |
| hf CLI 报 `does not seem to be on huggingface.co` | 别用 hf CLI，用 curl/aria2 直下 |
| 长文档第 3-4 批 MPS 崩溃 | `export MINERU_PROCESSING_WINDOW_SIZE=32` |
| PYTHONPATH 污染 mineru venv | 跑前 `unset PYTHONPATH` |
| 模型 sha256 验证 | resolve URL `?download=true` HEAD 的 `x-linked-etag` 即官方哈希 |
| Skill description 超 60 字符被拒 | 触发词前置，一句话 ≤60 字符 |

## 🧪 验证过的成品

- **refactoring-ui-principles**：由本流程生成的示例 skill（《Refactoring UI》设计原则速查 + 全书存档）
- 252 页 PDF 全量解析：EXIT=0，输出 181MB（md + model.json + span.pdf + images）

## 📄 License

MIT
