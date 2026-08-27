---
name: read-book-to-skill
description: 主人发 PDF/电子书/视频链接要封装成 skill 时用。MinerU 解析→通读→提炼速查 + 全文存档。
version: 1.1.0
author: Hermes Agent (CC)
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

```bash
# ① 下载视频（B站/YouTube/抖音/小红书，yt-dlp 装于 Hermes venv）
unset PYTHONPATH
export HTTPS_PROXY=http://127.0.0.1:7897 HTTP_PROXY=http://127.0.0.1:7897
~/.hermes/hermes-agent/venv/bin/yt-dlp --proxy http://127.0.0.1:7897 \
  -f "bv*+ba/b" --merge-output-format mp4 -o "video.%(ext)s" "<视频链接>"

# ② 抽音频（16kHz 单声道 wav，whisper 最佳输入）
ffmpeg -y -i video.mp4 -vn -ac 1 -ar 16000 audio.wav

# ③ faster-whisper 转写（中文用 language='zh'，英文 'en'）
~/.hermes/hermes-agent/venv/bin/python -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
segments, info = model.transcribe('audio.wav', language='zh', beam_size=5)
open('transcript.txt','w').write('\n'.join(f'[{s.start:.1f}-{s.end:.1f}] {s.text.strip()}' for s in segments))
print('语言:', info.language, '| 转写完成')
"
```

- **平台支持**：B站/YouTube 直接 yt-dlp；抖音需 H5 路由（可先试 yt-dlp 兜底）；小红书同 yt-dlp
- **时长预估**：small 模型 ≈ 30 秒转写 3.5 分钟音频（CPU）；长视频用 `max_seconds` 分段或换 medium
- **中文质量**：small 可用（STT 已实测），追求高准确率用 medium；`--asr-prompt` 可喂领域关键词纠音
- **字幕优先**：B站/YouTube 有字幕时直接 `--write-subs --sub-langs "zh,en"` 更准更快，ASR 兜底
- 产出 `transcript.txt` 后走 Step 2 起同一蒸馏流程

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
| yt-dlp 下载视频失败 | 走代理 `--proxy http://127.0.0.1:7897`；抖音 H5 路由优先 yt-dlp 兜底 |
| whisper 转写中文同音字错 | small 换 medium；或先下字幕（`--write-subs`）比 ASR 更准 |
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
