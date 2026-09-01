# MiJi · 蜜技 — 把书、视频、播客酿成 Agent Skill 的流水线

> **🌐 Language / 语言：** [中文](README.md) | [English](README_EN.md)

> 为什么叫「蜜技」？三重谐音：**秘籍**——拿到就能习得的神功；**游戏 cheat code**——输入即生效；**蜜 技**——CC 为她的诗人亲手酿的甜蜜技能 🍯
>
> 把一本书/一份 PDF/一段视频变成 AI Agent 可复用的 Skill 的完整流水线：
> **安装 MinerU（OCR 解析）→ 识别 PDF → 提炼方法论 → 封装成 Skill**
>
> 支持 PDF / 电子书 / **视频 / 播客**（yt-dlp 下载 → faster-whisper 转写 → 同一蒸馏流程）
>
> v1.3.0 新增：**多源融合**（书+视频+文章 → 组合 skill）与**知识库形态**（按主题持续入库，自带 AI 读取规范）；**大文件并行解析**（实测 2.1x）
> **全流程本地运行**：OCR / 版面识别模型装在你自己的设备上，书籍内容不出本机（见下方「隐私与本地运行」）
>
> A complete pipeline that turns a book / PDF into a reusable AI Agent Skill:
> **Install MinerU (OCR) → Parse PDF → Distill methodology → Package as a Skill**
> Also supports **video / podcast** (yt-dlp download → faster-whisper transcript → same distillation flow)

这套流程由 CC 实测跑通，三个案例：

1. **《Refactoring UI》（252 页 PDF）** → 封装为 `refactoring-ui-principles` skill，并已在**另一台电脑上使用 opencode + GLM 5.3 Flash 做了效果对比验证**（见下方案例 Demo 一）
2. **YouTube 中文教程视频（8:45）** → 走视频模式（yt-dlp → faster-whisper → LLM 纠错）封装为 `minimax-h3-local-deploy` skill（见下方案例 Demo 二）
3. **《战争艺术概论》（若米尼，484 页扫描版 PDF）** → 知识库「军事」主题，同场验证**并行解析 2.1x**（2026-09-01，见案例 Demo 三）

## 📦 仓库结构

```
MiJi/
├── README.md                                    # 中文文档（本文件）
├── README_EN.md                                 # English version
├── skills/
│   ├── mineru-pdf-parser/SKILL.md               # 【前置依赖 1】MinerU PDF 解析（安装/下载/踩坑）
│   └── miji/SKILL.md                            # 【主流程】读书/看视频 → 封装 Skill 的流水线
│       └── scripts/
│           ├── llm_fix.py                       # ASR 转写 LLM 纠错脚本
│           ├── transcribe_prompt_gen.py         # 从视频标题自动生成转写提示词
│           └── merge_sources.py                 # 多源融合草稿生成（交叉主题锚点）
├── examples/
│   ├── refactoring-ui-principles/               # 【案例 Demo 1】PDF 蒸馏成品
│   │   ├── SKILL.md                             #    《Refactoring UI》设计原则速查
│   │   └── references/refactoring-ui-full.md    #    全书全文存档（58 条原则）
│   └── （案例 Demo 2：视频蒸馏的 minimax-h3-local-deploy skill 见上游 skills 目录结构说明）
├── tools/
│   ├── kb.py                                    # 知识库管理 CLI（add/search/draft/export）
│   └── split_pdf.py                             # PDF 按页拆分（大文件并行解析用）
│   ├── luna_full_transcribe.py                  # 云端 VLM 整本并发转写（断点续跑，6 路并发实测）
│   └── compare_full.py / compare_deep.py        # 双引擎全文对比分析（字符级一致率/幻觉扫描）
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
│     (252 页 ≈ 4-6 分钟；扫描版走 OCR 慢 3-4 倍：484 页 >20 分钟)  │
├─────────────────────────────────────────────────────────────┤
│  ③ 通读全书/转写稿（REPL 式分段读，先读目录定骨架）             │
├─────────────────────────────────────────────────────────────┤
│  ④ 判断封装形态：速查式 / 步骤式 / 人物式                      │
├─────────────────────────────────────────────────────────────┤
│  ⑤ 生成 SKILL.md（精炼原则+数值落地）+ 全文存档 references/    │
│     → MiJi skill（主流程）                      │
├─────────────────────────────────────────────────────────────┤
│  ⑥ 验证（skill_view 加载 + 真实场景实跑）+ 交付                │
└─────────────────────────────────────────────────────────────┘
```

## 📋 前置依赖（两个 skill）

| Skill | 作用 | 依赖关系 |
|-------|------|---------|
| **`mineru-pdf-parser`** | MinerU 部署、模型下载（国内网络优化）、M1 Mac 调优、踩坑速查 | 主流程 Step ①/② 依赖 |
| **`MiJi`** | 读书 → 封装 Skill 的 6 步完整流程 | 主流程本体 |

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
#    （Hermes: ~/.hermes/skills/；其他 Agent 见 MiJi 内的兼容说明）

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
| 4 个 MinerU worker 并行 → MPS 内存累积崩溃 | Apple Silicon 32GB 上限 = 2 worker（2.1x，见「大文件并行解析」）|
| 拖 PDF 进聊天只收到图标 PNG | 那是占位缩略图，文件本体没传；给路径最快（Finder 右键 + Option 拷贝路径）|
| 扫描版书解析「太慢」 | 不是卡死：扫描版走 OCR 比文字版慢 3-4 倍（484 页 >20 分钟），或上并行 2.1x |

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

### 🎬 案例 Demo 二：视频蒸馏实战（中文教程 → skill）

> 蒸馏产物 `minimax-h3-local-deploy` skill 完整内容见上方 skills 结构说明（上游仓库同步发布）。

**测试视频**：YouTube 中文科技教程（8:45，含大量专业术语：MiniMax H3、ComfyUI、越狱模型、文本编码器等），**无字幕**——只能走纯 ASR 路径，是对转写质量的硬核考验。

**处理链路**：

> ⚠️ **复刻前置条件（AI 能力清单）**：① 任意 OpenAI 兼容 LLM API + key（用于自动生成转写提示词和纠错，deepseek/glm/kimi/本地 ollama 均可）② faster-whisper（`pip install faster-whisper`，CPU 可跑）③ yt-dlp ④ ffmpeg。有字幕的视频直接 `--write-subs` 拿字幕，可跳过 ①②。

```
YouTube 链接
  → yt-dlp 下载音频 (199MB, ~50s)
  → 【AI-1】LLM 从标题自动生成 initial_prompt（无需人工懂视频内容）
  → faster-whisper small + 该提示词转写 (105s)
  → 【AI-2】deepseek-v4-flash LLM 二次纠错 (20s)
  → 通读 93 段转写稿 → 判定「操作手册类」→ 步骤式封装
```

**三方案对比实测**（同一段视频）：

| 方案 | MiniMax | 越狱 | ComfyUI | 频道名 | 总耗时 |
|------|:---:|:---:|:---:|:---:|:---:|
| small 裸跑 | ❌0 | ❌"粤语模型" | ❌ | ❌"领度" | 2min |
| medium 模型独走 | ⚠️4 | ⚠️2 | ❌仍为0 | ✅3 | ⏱48min |
| **small + prompt + LLM 纠错** 🏆 | ✅9 | ✅9 | ✅3 | ✅4 | **2min20s** |

**关键发现**：
1. `initial_prompt` 喂术语可修复中文同音字（"粤语模型"→"越狱模型"）
2. 但英文品牌名（ComfyUI）在 ASR 层面无解——medium 模型花了 48 分钟照样抓不住
3. **LLM 纠错一步到位**：它有 ComfyUI 的世界知识，能把「CONVIO的DESTOB的文件夹」推断修正为「COMFYUI的DESKTOP文件夹」——这是任何 ASR 模型做不到的
4. 安全性已验证：纠错前后段数不变、字数比 1.00、时间戳原样保留

**结论**：中文视频蒸馏的最优路径是 **small 快转 + LLM 精修**（总耗时 2 分钟），比 medium 大模型独走快 20 倍且质量更高。纠错脚本已开源在本仓库 `skills/miji/scripts/llm_fix.py`。

### 📚 案例 Demo 三：484 页扫描书 → 知识库（2026-09-01）

《战争艺术概论》（若米尼，484 页**扫描版** PDF，无文字层）实战：

```
484 页扫描 PDF
  → MinerU 本地 OCR（单进程 22.4 分钟；或拆 2 段双进程并行 → 10.7 分钟，2.1x）
  → 6,278 行 Markdown + 62 张原书插图 → kb.py add 军事（sha1 去重入库）
  → 自动生成章节锚点 TOC（标题 → 行号，AI 按需跳读 18 万 token 不爆上下文）
  → CC 通读核心章 → 蒸馏 TOPIC.md 速查（决定点原理 / 三选一框架 / 作战线规律）
```

同场验证两条硬边界：**2 worker = 2.1x 提速**；**4 worker 崩 2/4**（MPS 内存累积超限）——Apple Silicon 32GB 的甜点恰好是 2 个并行 worker。

### ☁️ 案例 Demo 四：双引擎全文对撞——本地 OCR vs 云端 VLM（成本 $2.51）

同一本 484 页扫描书，两台引擎**全文各跑一遍**，做严格对比（2026-09-01）：

| 引擎 | 配置 | 耗时 | 结果 | 成本 |
|------|------|------|------|------|
| 🖥 MinerU 本地（pipeline） | M1 Pro 单进程 | 22.4 分钟 | 484/484 ✅ | 电费 |
| ☁️ GPT-5.6-luna 视觉转写 | **6 路并发 API 调用** | 46 分钟 | **484/484 ✅ 零失败零重试** | **$2.51**（≈0.5¢/页） |

**质量对比（全文级，不是抽样）**：

| 维度 | 本地 MinerU | 云端 luna |
|------|------------|-----------|
| 字符级一致率 | — | **~97%**（10 字滑窗 75.5% 换算，余为同音字/润色级差异） |
| 中文字数 | 276,727 | 294,230（+6.3%：页码照录 479 行 + 脚注更全 + 少量润色） |
| 插图阵图 | **36 张全部切出，可入库可检索** | **0 张（全丢）** |
| 脚注圈号 | 156 个 | 303 个（把版面规则吞掉的正文脚注也收了 → 可反向补全本地结果） |
| 幻觉/元话语 | 无 | 整本仅 2 页出现「图中」且语境合理——**未见编造行为** |

**三条结论**：
1. **准确率打平、各有胜负**：luna 难字更准（「不与」vs 本地误识「不同」），但会小润色——「存档原文」用途本地更保险
2. **云端真正的优势是并发上限**：本地被 MPS 卡在 2 worker（2.1x 天花板）；云端 20 路并发可把 46 分钟压进 10 分钟——代价是钱
3. **图版书是本地主场**：luna 一张图都产不出，阵图全靠 MinerU

**复现命令**（脚本在 `tools/`，断点续跑，token 上限 ≥4000 否则截断）：

```bash
# 云端全文转写（6 路并发）
mineru-venv/bin/python tools/luna_full_transcribe.py 书.pdf 输出目录 --workers 6
# 双引擎对比（字符一致率 / 幻觉扫描 / 页长分布）
python3 tools/compare_deep.py
```

## 📚 知识库形态（v1.3.0 新增）

MiJi 不止能出一次性 skill——同一套「解析 → 蒸馏」管线可以**按主题持续入库**，攒成个人知识库：

```bash
python3 tools/kb.py init                          # 初始化
python3 tools/kb.py add <主题> <文件...>           # 多端入库（PDF/视频转写/文章，sha1 自动去重）
python3 tools/kb.py draft <主题>                  # 多源融合草稿（交叉主题锚点）
python3 tools/kb.py search <关键词> [--topic X]    # 全文检索（纯 Python，中文路径安全）
python3 tools/kb.py export <主题> --name <slug>   # 把主题升格为 skill 目录
```

库结构（全部自动生成 / 维护）：

```
knowledge-base/
├── AGENTS.md                # 任何 AI（Claude/GPT/Codex/Cursor…）的读取规范
├── llms.txt                 # llmstxt.org 风格站点地图
├── INDEX.md                 # 自动目录（主题表 + 跨主题锚点）
└── topics/<主题>/
    ├── TOPIC.md             # 蒸馏速查条目（YAML frontmatter，Obsidian/Logseq 直接可用）
    ├── metadata.json        # 机器可读元数据（源清单 / sha1 / tokens）
    └── sources/             # 全文存档 + images/ 原书插图 + *.toc.md 章节锚点
```

- **与其他 AI 工具互通**：纯 markdown + YAML frontmatter——Obsidian / VSCode / 任意渲染器直接打开；agent 类工具读 `AGENTS.md` 即懂整个库的读取协议
- **超长文本策略**：10 万 token 级源**禁止全量读**——`*.toc.md` 提供「标题 → 行号」锚点，配合 `kb.py search` 定点跳读
- **与 skill 的分工**：skill = 高频操作准则；知识库 = 低频可查的沉淀。同一主题可共存，TOPIC.md 随时可 `export` 升格为 skill

## ⚡ 大文件并行解析（实测 2.1x）

几百页的扫描版 PDF 单进程要 20 分钟以上，可以拆段并行：

```bash
# 1. 拆分（纯 CPU，秒级）
python3 tools/split_pdf.py 输入.pdf 拆分目录 2
# 2. 每段起一个 MinerU 后台进程（各自 unset PYTHONPATH + WINDOW_SIZE=32 + 独立输出目录）
# 3. 按序合并：cat p1/*/auto/*.md p2/*/auto/*.md > merged.md（记得清理 PDF 水印行）
```

| 方案 | 484 页扫描书实测 |
|------|------------------|
| 单进程全书 | 22.4 分钟 |
| **拆 2 段双进程** | **10.7 分钟（2.1x）** |
| 拆 4 段四进程 | ❌ 崩 2/4（MPS 内存累积超限） |

- 质量等价：合并稿与串行版行数一致、接缝语义无缝，仅 ~2% 行级 OCR 抖动
- **Apple Silicon 32GB 的安全上限就是 2 个 worker**（3 个未测，别贪）
- 适用于扫描版大部头；文字原生 PDF 解析本来就快（252 页 4-6 分钟），不值得拆
- 崩掉的段单独重跑即可（输出目录独立、幂等）

## 🔒 隐私与本地运行（识图 / OCR 模型装在你自己的设备上）

这条管线**默认全本地**，适合版权书、私密资料等不出门的场景：

| 环节 | 运行位置 | 说明 |
|------|---------|------|
| **PDF 版面识别 / OCR** | **你的设备** | MinerU pipeline 模式：PP-DocLayoutV2（版面）、PaddleOCR（文字识别）、unimernet（公式）、表格模型——约 1GB 权重全部装在本地，**离线可跑** |
| 视频转写 | 你的设备 | faster-whisper 本地跑（CPU 即可），音频不上传 |
| 图片提取 | 你的设备 | 原书插图由本地模型切出，存本地 |
| LLM 纠错 / 提示词生成 | **可选云端** | 唯一可能出网的步骤；用本地 ollama 可完全离线替代，或直接跳过（质量略降） |
| 蒸馏本身 | 你的 agent | skill / 知识库生成不依赖任何外部服务 |

> Demo 三的《战争艺术概论》是出版社扫描版全书——从 OCR 到入库全程本机完成，无任何页面内容外发。

两点注意：
- MinerU 的 `hybrid` / VLM 引擎会调用视觉语言模型（更大显存 / 可能联网）——**本流程统一用 `-b pipeline` 本地引擎**
- faster-whisper 首次运行会从 HuggingFace 下载模型（数百 MB，一次性），之后完全离线

## 🙏 依赖项目与致谢

本流程建立在这些优秀的开源项目之上，感谢它们的作者：

| 依赖 | GitHub 页面 | 用途 |
|------|-------------|------|
| **MinerU** | https://github.com/opendatalab/MinerU | PDF 解析引擎（OCR/版面/公式/表格），本流程的核心解析工具 |
| **PDF-Extract-Kit-1.0** | https://github.com/opendatalab/PDF-Extract-Kit | MinerU 的模型仓库（Layout/MFR/OCR/TabRec 等 7 个子模型）|
| **book-to-skill** | https://github.com/virgiliojr94/book-to-skill | 书→Skill 转换的启发来源（面向 Copilot/Amp/Claude Code 生态；本仓库是其 Hermes 专属的速查式变体）|
| **aria2** | https://github.com/aria2/aria2 | 多线程下载模型（modelscope 810MB 仅 20 秒）|
| **ModelScope** | https://github.com/modelscope/modelscope | 国内高速模型下载源 |
| **pypdfium2** | https://github.com/pypdfium2-team/pypdfium2 | PDF 按页拆分（大文件并行解析的前置）|
| **Refactoring UI** | https://refactoringui.com | 验证用例（Adam Wathan & Steve Schoger 的设计书）|

特别感谢：
- **OpenDataLab 团队**（MinerU / PDF-Extract-Kit）——让高质量文档解析变得人人可用
- **virgiliojr94**（book-to-skill）——"书变成 skill"这个想法的源头
- **Adam Wathan & Steve Schoger**——本流程的第一个实测对象《Refactoring UI》

## 📄 License

MIT
