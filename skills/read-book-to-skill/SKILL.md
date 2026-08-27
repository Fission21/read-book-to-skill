---
name: read-book-to-skill
description: 主人发 PDF/电子书/视频链接要封装成 skill 时用。MinerU 解析→通读→提炼速查 + 全文存档。
version: 1.1.0
author: CC
tags: [book, skill, 读书, pdf, video, 提炼, workflow]
---

# 读书封装 Skill 流程（Hermes 专属）

> 2026-08-27 实测跑通：主人发《Refactoring UI》PDF → 封装成 `refactoring-ui-principles` skill。
> 2026-08-27 新增**视频模式**：yt-dlp 下载 → ffmpeg 抽音频 → faster-whisper 转写 → 同一蒸馏流程。
> 本 skill 固化整条流程，后续「读书/看视频 → 封装 skill」照此执行。

## 触发条件

- 主人发来 PDF/EPUB/长文档，说「封装成 skill」「提炼成 skill」「读书」「做成 skill」
- 主人发来 B站/抖音/YouTube/小红书**视频链接**，说「把这个视频蒸馏成 skill」「提取视频内容」
- 主人要求把一本书/一段视频的方法论固化成可复用的 agent 技能

## 内容来源（两条路径）

| 来源 | 工具链 | 产出 |
|------|--------|------|
| **PDF/扫描件** | MinerU（见 mineru-pdf-parser）| 完整 markdown |
| **视频/播客** | yt-dlp + ffmpeg + faster-whisper（见下）| transcript.txt 转写文本 |

两条路径的产出都是**纯文本**，之后走同一条蒸馏流程（Step 2 起）。

## 完整流程（6 步）

### Step 1 — 解析文档为 Markdown

**PDF/扫描件**：用 MinerU（先加载 `mineru-pdf-parser` skill 看环境与坑）：

```bash
unset PYTHONPATH
export MINERU_PROCESSING_WINDOW_SIZE=32   # 长文档防 MPS 崩溃，关键！
~/demo/ai-tools/mineru-venv/bin/mineru -p "输入.pdf" -o 输出目录 -b pipeline
```

- 输出在 `输出目录/<文件名>/auto/*.md`（161KB 级别的完整 markdown）
- 252 页书约 4-6 分钟；跑完检查 `EXIT=0` 且 md 非空
- **已是 md/txt 的**：跳过 MinerU，直接读源文件

### Step 1b — 视频/播客 → 转写文本（视频模式）

**AI 能力清单（此步需要提前准备）**：

| 能力 | 用在哪 | 最低要求 | 无此能力时 |
|------|--------|---------|-----------|
| **LLM API**（OpenAI 兼容）| ① 从标题/简介自动生成转写提示词 ② 转写稿纠错 | 任一兼容端点+key（deepseek/glm/kimi/本地 ollama 均可）| 提示词需人工手写；跳过纠错（转写质量下降）|
| **语音识别** | 音频→文本 | faster-whisper（CPU 可跑）或 openai-whisper CLI | 无法处理无字幕视频 |
| **yt-dlp** | 平台视频下载 | 最新版（B站/YouTube/小红书通用）| 无法获取视频 |
| **ffmpeg** | 抽音频 | 系统自带或 brew/apt 安装 | — |

> 字幕优先级最高：`yt-dlp --write-subs --sub-langs "zh,en"` 拿到字幕就**完全不需要** ASR 和 LLM 纠错，直接 Step 2。

```bash
# 0. 准备：安装依赖（任选其一装 whisper）
pip install yt-dlp faster-whisper        # 推荐 faster-whisper（快4倍）
# 或 pip install yt-dlp openai-whisper
# ffmpeg: macOS `brew install ffmpeg` / Ubuntu `apt install ffmpeg`

# ① 下载音频
yt-dlp --proxy <代理地址,如有> -f "ba" -x --audio-format wav \
  -o "video.%(ext)s" "<视频链接>"         # 只要音频用 -f "ba"，比带视频快得多

# ② 【AI-1】让 LLM 从标题/简介自动生成 initial_prompt（无需人工懂视频内容）
#    实测有效：标题里的「MiniMax H3越狱」进 prompt 后转写命中从 0 → 4+
python3 transcribe_prompt_gen.py "<视频标题>" "<简介关键句>"
#   输出形如: 下面是关于MiniMax H3越狱模型的教程。MiniMax H3, 越狱模型, 开源, ...
#   没有 LLM 时: 自己看一眼标题，把专有名词手动列成一行也可

# ③ faster-whisper 转写（⚠️ 中文必须带 initial_prompt，实测同音字错误大幅减少）
python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
prompt = '<②生成的提示词>'
segments, info = model.transcribe('video.wav', language='zh', beam_size=5, initial_prompt=prompt)
open('transcript.txt','w').write('\n'.join(f'[{s.start:.1f}-{s.end:.1f}] {s.text.strip()}' for s in segments))
"

# ④ 【AI-2】LLM 二次纠错（修 ASR 层面无解的英文品牌名等，见下方数据表）
python3 llm_fix.py transcript.txt transcript_fixed.txt "<视频主题提示>"
```

- **平台支持**：B站/YouTube 直接 yt-dlp；抖音需 H5 路由（可先试 yt-dlp 兜底）；小红书同 yt-dlp
- **时长预估**：small 模型 ≈ 30 秒转写 3.5 分钟音频（CPU）；长视频用 `max_seconds` 分段或换 medium
- **中文质量**：small 可用（STT 已实测），追求高准确率用 medium；`--asr-prompt` 可喂领域关键词纠音
- **字幕优先**：B站/YouTube 有字幕时直接 `--write-subs --sub-langs "zh,en"` 更准更快，ASR 兜底
- 产出 `transcript.txt` 后走 Step 2 起同一蒸馏流程

#### LLM 纠错步骤（中文视频必做）

ASR 转写后**必须做二次纠错**，把带时间戳的转写稿 + 术语表喂给 LLM 修正。实测数据（8:45 中文教程视频）：

| 方案 | MiniMax | 越狱 | ComfyUI | 零度解说 | 转写耗时 |
|------|:---:|:---:|:---:|:---:|:---:|
| small 无提示词 | 0❌ | 0❌（写成"粤语"）| 0❌ | 0❌（"领度"）| 105s |
| **small+prompt → LLM纠错** ✅ | 9 | 9 | 3 | 4 | 105s+20s |
| medium+prompt 独走 | 4 | 2 | ❌仍为0 | 3 | ⏱2691s |

- **纠错提示词要点**：给 LLM 的 system 说明「只改明显同音字/术语错、时间戳与分段结构不变、不确定保持原样不发挥」；user 里附正确术语参考表（可让 LLM 先从标题自动生成，见 transcribe_prompt_gen.py）
- **安全校验**：纠错前后段数应一致，字数比 ≈1.00（超 ±5% 说明 LLM 在篡改内容，重跑降温重试）
- 任何 OpenAI 兼容 API 均可用（deepseek/glm/kimi/ollama 本地模型等），配置见 `llm_fix.py` 顶部环境变量说明
- **medium 模型别用来独走**：下载 1.5GB + CPU 转 8 分钟视频要 45 分钟，ComfyUI 这类英文术语照样抓不住——不如 small 快转 + LLM 精修

### Step 2 — 通读全书（REPL 式，别一次全读）

- 先 `wc -l` 看行数，`read_file` 分段读（每段 ≤850 行）
- **先读目录（Contents/TOC）**——书的结构就是 skill 的骨架
- 边读边在脑中标记：框架/原则/具体数值/CSS 写法/反模式
- 大书（>3000 行）分 4-6 段读完，不要跳章节

### Step 3 — 判断封装形态（先问主人或按内容自定）

| 书的内容 | 封装形态 |
|---------|---------|
| 方法论/原则类（如设计、写作、管理） | **速查式**：SKILL.md 精炼原则 + references/ 全文存档（今天《Refactoring UI》的做法）|
| 操作手册/工具书 | 步骤式：SKILL.md 命令流程 + scripts/ 模板 |
| 思维框架类（如各 perspective skill） | 人物式：核心心智模型 + 表达方式 + 素材来源 |

拿不准就问主人一句：「这本书想封装成速查式还是深度式？」

### Step 4 — 生成 SKILL.md（核心，质量全在这里）

**模板结构**（参考 `refactoring-ui-principles` 的实际效果）：

```markdown
---
name: <英文-slug>
description: <触发词前置的一句话，≤60 字符！>
version: 1.0.0
---
# <书名> <核心主题>
> 来源：<作者><书名>解析；用途：<何时用>
## 触发条件
## 核心心法（3 条以内，先记住的）
## <各主题章节>（把书的章节按主题重组）
   - 每条原则：结论 + 具体数值/CSS/写法 + 一句话为什么
## 审查/检查清单（如果是方法论类）
## 相关（关联的现有 skill）
```

**质量铁律**：
1. **description ≤60 字符**（57 字截断，触发词放最前）——今天 104 字符被拒过一次
2. **具体数值要落地**：书里的尺度/公式/CSS 直接写进 SKILL.md（如间距 4-128、字号 12-48、`box-shadow: 0 4px 6px hsla(...)`），不是"用合适的间距"
3. 原则写成可执行指令（"先给太多留白，再删"），不是书评
4. SKILL.md 控制在 7-10KB，细节放 references/

### Step 5 — 全文存档 references/

```markdown
references/<书名-slug>.md
```

- 把解析出的完整 md **清理后**存入（去图片占位行、去表格噪音、保留全部正文）
- 作用：SKILL.md 不够用时按需查阅原文细节
- 用 `skill_manage(action='write_file', name=..., file_path='references/xxx.md', file_content=...)`

### Step 6 — 验证 + 交付

1. `skill_view(name='<slug>')` 确认能正常加载、无 lint 报错
2. 有真实使用场景就**实跑一遍验证**（今天拿 252 页 PDF 全量跑通才交付）
3. 报告路径 + 给主人桌面快捷方式（可选）：
   ```bash
   ln -sfn ~/.hermes/skills/<category>/<slug> ~/Desktop/<名字>-skill
   ```

## ⚠️ 踩过的坑

| 坑 | 解法 |
|----|------|
| skill description 超 60 字符被拒 | 触发词放最前，一句话，≤60 |
| 全文 md 有图片占位 `![](images/...)` | 存档时删掉（图片在 PDF 里，路径已失效）|
| MinerU 默认窗口 64 长文档崩溃 | `MINERU_PROCESSING_WINDOW_SIZE=32` |
| PYTHONPATH 污染 mineru venv | 跑前 `unset PYTHONPATH` |
| yt-dlp 下载视频失败 | 需要代理时 `--proxy <代理地址>`（如 Clash: http://127.0.0.1:7897）；抖音 H5 路由优先 yt-dlp 兜底 |
| whisper 转写中文同音字错 | **三步走**：① 字幕优先（`--write-subs`）② initial_prompt 自动喂术语（从标题 LLM 生成，"粤语模型"→"越狱模型"实测有效）③ LLM 二次纠错（ComfyUI 等英文术语 small/medium 都抓不住，LLM 能修对）|
| medium 模型下载/转写超慢 | 1.5GB 模型 + CPU 转 8 分钟视频要 45 分钟；除非有 GPU 否则用 small+LLM纠错替代 |
| faster-whisper 首次下载模型卡住 | HF 下载需要网络畅通：有代理就 export HTTPS_PROXY，或设 HF_ENDPOINT=https://hf-mirror.com |
| 与 book-to-skill（第三方）混淆 | 那个面向 Copilot/Amp/Claude Code，输出 chapters/glossary 结构；本 skill 是 Hermes 专属速查式 |
| 主人找不到 skill 路径 | skill 根目录是隐藏目录，给桌面快捷方式或 Finder `Cmd+Shift+G` |

## 验证过的成品

- `refactoring-ui-principles`（creative/）——《Refactoring UI》设计原则速查 + 全书存档（2026-08-27）
- `mineru-pdf-parser`（devops/）——MinerU 部署与使用（本流程 Step 1 依赖它）
- 视频模式实测（2026-08-27）：B站 3.5 分钟视频 → yt-dlp 下载（12MB/s）→ ffmpeg 抽音频 → faster-whisper small 30 秒转写 69 段，歌词/语音准确

## 相关

- `mineru-pdf-parser`：Step 1 的解析工具与环境
- `book-to-skill`：第三方通用转换器（多 agent 生态用，非本流程）
- `skill-creator`：skill 编写的通用规范（若存在）
