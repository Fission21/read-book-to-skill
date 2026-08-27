# read-book-to-skill — 读书封装 Skill 流程

> **🌐 Language / 语言：** [中文](README.md) | [English](README_EN.md)

> 把一本书/一份 PDF 变成 AI Agent 可复用的 Skill 的完整流水线：
> **安装 MinerU（OCR 解析）→ 识别 PDF → 提炼方法论 → 封装成 Skill**
>
> 支持 PDF / 电子书 / **视频 / 播客**（yt-dlp 下载 → faster-whisper 转写 → 同一蒸馏流程）
>
> A complete pipeline that turns a book / PDF into a reusable AI Agent Skill:
> **Install MinerU (OCR) → Parse PDF → Distill methodology → Package as a Skill**
> Also supports **video / podcast** (yt-dlp download → faster-whisper transcript → same distillation flow)

这套流程由 CC（Hermes Agent）在 2026-08-27 实测跑通：将《Refactoring UI》（252 页 PDF）成功封装为 `refactoring-ui-principles` skill，并已在**另一台电脑上使用 opencode + GLM 5.3 Flash 做了效果对比验证**（见下方案例 Demo）。

## 📦 仓库结构

```
read-book-to-skill/
├── README.md                                    # 中文文档（本文件）
├── README_EN.md                                 # English version
├── skills/
│   ├── mineru-pdf-parser/SKILL.md               # 【前置依赖 1】MinerU PDF 解析（安装/下载/踩坑）
│   └── read-book-to-skill/SKILL.md              # 【主流程】读书 → 封装 Skill 的 6 步流水线
├── examples/
│   └── refactoring-ui-principles/               # 【案例 Demo】本流程产出的成品 skill
│       ├── SKILL.md                             #    《Refactoring UI》设计原则速查
│       └── references/refactoring-ui-full.md    #    全书全文存档（58 条原则）
└── docs/images/                                 # 案例对比截图（no-skill vs skill）
```

## 🔄 完整流程

```
┌─────────────────────────────────────────────────────────────┐
│  ① 安装 MinerU + 下载模型（国内网络优化）                      │
│     → mineru-pdf-parser skill（前置依赖 1）                    │
│  ①b 视频/播客：yt-dlp 下载 → ffmpeg 抽音频 → faster-whisper 转写 │
├─────────────────────────────────────────────────────────────┤
│  ② 解析 PDF → Markdown（或直接使用转写文本）                   │
│     mineru -p 输入.pdf -o 输出目录 -b pipeline                │
│     (252 页 ≈ 4-6 分钟，输出完整 md/json/span.pdf)            │
├─────────────────────────────────────────────────────────────┤
│  ③ 通读全书/转写稿（REPL 式分段读，先读目录定骨架）             │
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

## 🧪 案例 Demo：Refactoring UI → skill 实战对比

> 完整 demo skill 在本仓库 `examples/refactoring-ui-principles/`，可直接安装使用。
> The full demo skill lives in `examples/refactoring-ui-principles/` — install & use it directly.

### 测试方法

在**另一台电脑**（Windows）上，使用 **opencode + GLM 5.3 Flash 模型**，用**同一套关键词**（设计一个企业官网首页：顶部导航 / Hero / 6 个功能特性 / 数据成绩 / 3 条客户评价 / CTA / 页脚，单文件静态 HTML+CSS）分别生成两个版本：

- **`no-skill`**：纯提示词直接生成（不加载任何 skill）
- **`skill`**：加载本流程产出的 `refactoring-ui-principles` skill 后再生成

### 对比结果


**左侧无skill 右侧使用：**

![no-skill 顶部](docs/images/demo-noskill-top.png)
![no-skill 功能区](docs/images/demo-noskill-features.png)
![对比](docs/images/demo-compare-top.png)

**页面底部（CTA + 页脚）：**

![对比-底部](docs/images/demo-compare-bottom.png)


**H5：**

![skill 底部](docs/images/demo-skill-bottom.png)
### 效果差异

| 维度 | no-skill（无 skill） | skill（加载 refactoring-ui-principles） |
|------|---------------------|------------------------------------------|
| 标题文案 | 「让团队协作更高效」（通用） | 「让每一次协作都有迹可循」（有记忆点） |
| 视觉层级 | 渐变横幅 + 平铺卡片 | 品牌圆点 + 产品示意插画 + 更清晰的层级 |
| CTA 区 | 常规按钮 | 「免费开始试用 / 了解产品功能」+ 14 天体验说明 |
| 细节质感 | 模板感明显 | 间距/对比/深度符合设计原则 |

**结论**：加载了从书里蒸馏出的设计原则 skill 后，同一模型、同一关键词生成的页面在**文案记忆点、视觉层级、细节质感**上都有明显提升——这就是「读书封装 skill」的价值：**把一本书的方法论，变成每次生成都能自动生效的能力。**

## 🙏 依赖项目与致谢

本流程建立在这些优秀的开源项目之上，感谢它们的作者：

| 依赖 | GitHub 页面 | 用途 |
|------|-------------|------|
| **MinerU** | https://github.com/opendatalab/MinerU | PDF 解析引擎（OCR/版面/公式/表格），本流程的核心解析工具 |
| **PDF-Extract-Kit-1.0** | https://github.com/opendatalab/PDF-Extract-Kit | MinerU 的模型仓库（Layout/MFR/OCR/TabRec 等 7 个子模型）|
| **book-to-skill** | https://github.com/virgiliojr94/book-to-skill | 书→Skill 转换的启发来源（面向 Copilot/Amp/Claude Code 生态；本仓库是其 Hermes 专属的速查式变体）|
| **aria2** | https://github.com/aria2/aria2 | 多线程下载模型（modelscope 810MB 仅 20 秒）|
| **ModelScope** | https://github.com/modelscope/modelscope | 国内高速模型下载源 |
| **Refactoring UI** | https://refactoringui.com | 验证用例（Adam Wathan & Steve Schoger 的设计书）|

特别感谢：
- **OpenDataLab 团队**（MinerU / PDF-Extract-Kit）——让高质量文档解析变得人人可用
- **virgiliojr94**（book-to-skill）——"书变成 skill"这个想法的源头
- **Adam Wathan & Steve Schoger**——本流程的第一个实测对象《Refactoring UI》

## 📄 License

MIT
