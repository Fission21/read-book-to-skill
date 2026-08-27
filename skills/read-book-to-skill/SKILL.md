---
name: read-book-to-skill
description: 主人发 PDF/电子书要封装成 skill 时用。MinerU 解析→通读→提炼速查 + 全文存档。
version: 1.0.0
author: Hermes Agent (CC)
tags: [book, skill, 读书, pdf, 提炼, workflow]
---

# 读书封装 Skill 流程（Hermes 专属）

> 2026-08-27 实测跑通：主人发《Refactoring UI》PDF → 封装成 `refactoring-ui-principles` skill。
> 本 skill 固化整条流程，后续「读书 → 封装 skill」照此执行。

## 触发条件

- 主人发来 PDF/EPUB/长文档，说「封装成 skill」「提炼成 skill」「读书」「做成 skill」
- 主人要求把一本书/一份资料的方法论固化成可复用的 agent 技能

## 完整流程（6 步）

### Step 1 — 解析文档为 Markdown

**PDF/扫描件**：用 MinerU（先加载 `mineru-pdf-parser` skill 看环境与坑）：

```bash
unset PYTHONPATH   # 必须！否则加载 Hermes venv 的包
export MINERU_PROCESSING_WINDOW_SIZE=32   # 长文档防 MPS 崩溃，关键！
<你的工作目录>/mineru-venv/bin/mineru -p "输入.pdf" -o 输出目录 -b pipeline
```

- 输出在 `输出目录/<文件名>/auto/*.md`（161KB 级别的完整 markdown）
- 252 页书约 4-6 分钟；跑完检查 `EXIT=0` 且 md 非空
- **已是 md/txt 的**：跳过 MinerU，直接读源文件

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
   ln -sfn <你的 skill 根目录>/skills/<category>/<slug> ~/Desktop/<名字>-skill
   ```

## ⚠️ 踩过的坑

| 坑 | 解法 |
|----|------|
| skill description 超 60 字符被拒 | 触发词放最前，一句话，≤60 |
| 全文 md 有图片占位 `![](images/...)` | 存档时删掉（图片在 PDF 里，路径已失效）|
| MinerU 默认窗口 64 长文档崩溃 | `MINERU_PROCESSING_WINDOW_SIZE=32` |
| PYTHONPATH 污染 mineru venv | 跑前 `unset PYTHONPATH` |
| 与 book-to-skill（第三方）混淆 | 那个面向 Copilot/Amp/Claude Code，输出 chapters/glossary 结构；本 skill 是 Hermes 专属速查式 |
| 主人找不到 skill 路径 | skill 根目录是隐藏目录，给桌面快捷方式或 Finder `Cmd+Shift+G` |

## 验证过的成品

- `refactoring-ui-principles`（creative/）——《Refactoring UI》设计原则速查 + 全书存档（2026-08-27）
- `mineru-pdf-parser`（devops/）——MinerU 部署与使用（本流程 Step 1 依赖它）

## 相关

- `mineru-pdf-parser`：Step 1 的解析工具与环境
- `book-to-skill`：第三方通用转换器（多 agent 生态用，非本流程）
- `skill-creator`：skill 编写的通用规范（若存在）
