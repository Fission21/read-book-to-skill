# read-book-to-skill — Turn Books into Agent Skills

> **🌐 Language / 语言：** [中文](README.md) | [English](README_EN.md)

> A complete pipeline that turns a book / PDF into a reusable AI Agent Skill:
> **Install MinerU (OCR) → Parse PDF → Distill methodology → Package as a Skill**
> Also supports **video / podcast** (yt-dlp download → faster-whisper transcript → same distillation flow)

This pipeline was proven end-to-end by CC (Hermes Agent) on 2026-08-27: a 252-page PDF of *Refactoring UI* was successfully packaged into the `refactoring-ui-principles` skill — and validated on **another machine using opencode + GLM 5.3 Flash** with a controlled A/B test (see Demo below).

## 📦 Repository Layout

```
read-book-to-skill/
├── README.md                                    # Chinese docs
├── README_EN.md                                 # English version (this file)
├── skills/
│   ├── mineru-pdf-parser/SKILL.md               # [Prerequisite 1] MinerU PDF parsing (install/download/pitfalls)
│   └── read-book-to-skill/SKILL.md              # [Main flow] 6-step pipeline: book → Skill
├── examples/
│   └── refactoring-ui-principles/               # [Demo] the skill produced by this pipeline
│       ├── SKILL.md                             #    Refactoring UI design-principles cheat sheet
│       └── references/refactoring-ui-full.md    #    Full book archive (58 principles)
└── docs/images/                                 # A/B comparison screenshots (no-skill vs skill)
```

## 🔄 The Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  ① Install MinerU + download models (China-network tuned)   │
│     → mineru-pdf-parser skill (prerequisite 1)               │
│  ①b Video/podcast: yt-dlp → ffmpeg audio → faster-whisper    │
├─────────────────────────────────────────────────────────────┤
│  ② Parse PDF → Markdown (or use transcript directly)        │
│     mineru -p input.pdf -o out -b pipeline                  │
│     (252 pages ≈ 4-6 min: md / json / span.pdf)             │
├─────────────────────────────────────────────────────────────┤
│  ③ Read the book/transcript (REPL-style, TOC first)         │
├─────────────────────────────────────────────────────────────┤
│  ④ Choose packaging form: cheat-sheet / step-guide / persona │
├─────────────────────────────────────────────────────────────┤
│  ⑤ Generate SKILL.md (distilled rules + concrete values)    │
│     + archive full text in references/                      │
│     → read-book-to-skill skill (main flow)                  │
├─────────────────────────────────────────────────────────────┤
│  ⑥ Verify (skill loads + real run) & deliver                │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites (two skills)

| Skill | Purpose | Dependency |
|-------|---------|------------|
| **`mineru-pdf-parser`** | MinerU setup, model download (China-network optimized), Apple Silicon tuning, pitfalls | Steps ①/② depend on it |
| **`read-book-to-skill`** | The full 6-step book→skill workflow | The main flow itself |

The main-flow skill **loads `mineru-pdf-parser` first** (Step 1) to get environment & pitfalls before parsing. Install both.

## 🚀 Quick Start

```bash
# 1. Install MinerU (Python 3.10+, use a dedicated venv)
python3 -m venv mineru-venv
mineru-venv/bin/pip install "mineru[core]"

# 2. Download models (~1GB — only 7 sub-paths, NOT the full 10GB repo)
#    China network: proxy to hf-mirror (6.2MB/s) or modelscope+aria2 (810MB in ~20s)
#    See mineru-pdf-parser/SKILL.md for the exact file list

# 3. Point ~/mineru.json models-dir.pipeline at your model directory

# 4. Parse a PDF
unset PYTHONPATH
export MINERU_PROCESSING_WINDOW_SIZE=32   # prevents MPS crash on long docs (Apple Silicon!)
mineru-venv/bin/mineru -p input.pdf -o out -b pipeline

# 5. Drop the two SKILL.md files into your agent's skills dir
#    (Hermes: ~/.hermes/skills/; other agents see compatibility notes inside)

# 6. Tell your agent: "package this book into a skill"
```

## ⚠️ Pitfalls Quick Reference (all tested in practice)

| Pitfall | Fix |
|---------|-----|
| `hf download` pulls the full 10GB+ repo | Only 7 sub-paths ≈ 1GB needed; use curl/aria2 on resolve URLs |
| hf-mirror direct = 0 bytes (blocked) | Go through a proxy (6.2MB/s) or modelscope (4.9MB/s) |
| hf CLI: `does not seem to be on huggingface.co` | Don't use hf CLI; curl/aria2 the resolve URL directly |
| MPS crash on batch 3-4 of long docs | `export MINERU_PROCESSING_WINDOW_SIZE=32` |
| PYTHONPATH pollutes the mineru venv | `unset PYTHONPATH` before running |
| Model sha256 verification | HEAD `?download=true` → `x-linked-etag` is the official hash |
| Skill description >60 chars rejected | Trigger-first, one sentence, ≤60 chars |

## 🧪 Case Demo: Refactoring UI → skill (A/B test)

> The complete demo skill is in `examples/refactoring-ui-principles/` — install & use directly.

### Test Setup

On **another machine (Windows)**, using **opencode + GLM 5.3 Flash**, we ran the **same prompt** (build a single-file static corporate homepage: top nav / hero / 6 feature cards / stats / 3 testimonials / CTA / footer, inline HTML+CSS, no external assets) twice:

- **`no-skill`**: raw prompt only (no skill loaded)
- **`skill`**: loaded the `refactoring-ui-principles` skill produced by this pipeline

### Side-by-Side

**Left = no-skill, right = with skill:**

![noskill-top](docs/images/demo-noskill-top.png)
![noskill-features](docs/images/demo-noskill-features.png)
![compare](docs/images/demo-compare-top.png)

**Page bottom (CTA + footer):**

![compare-bottom](docs/images/demo-compare-bottom.png)

**H5:**

![skill-bottom](docs/images/demo-skill-bottom.png)

### Key Differences

| Dimension | no-skill | with `refactoring-ui-principles` |
|-----------|----------|----------------------------------|
| Headline | "让团队协作更高效" (generic) | "让每一次协作都有迹可循" (memorable) |
| Visual hierarchy | gradient banner + flat cards | brand dot + product mockup + clearer hierarchy |
| CTA section | plain buttons | "免费开始试用 / 了解产品功能" + 14-day trial note |
| Polish | obvious template feel | spacing/contrast/depth follow the book's rules |

**Takeaway**: with the same model and the same prompt, loading a skill distilled from a book measurably improves the output — memorable copy, better visual hierarchy, and real polish. That's the value of this pipeline: **a book's methodology becomes capability that applies automatically on every generation.**

## 🙏 Dependencies & Acknowledgements

This pipeline stands on these great open-source projects — thank you to their authors:

| Dependency | GitHub | Used for |
|------------|--------|----------|
| **MinerU** | https://github.com/opendatalab/MinerU | PDF parsing engine (OCR/layout/formula/table) — the core |
| **PDF-Extract-Kit-1.0** | https://github.com/opendatalab/PDF-Extract-Kit | MinerU's model repo (7 sub-models: Layout/MFR/OCR/TabRec…) |
| **book-to-skill** | https://github.com/virgiliojr94/book-to-skill | Inspiration for book→skill (Copilot/Amp/Claude Code ecosystem; this repo is the Hermes-flavored cheat-sheet variant) |
| **aria2** | https://github.com/aria2/aria2 | Multi-threaded model download (810MB from modelscope in ~20s) |
| **ModelScope** | https://github.com/modelscope/modelscope | High-speed model source inside China |
| **Refactoring UI** | https://refactoringui.com | Validation case (Adam Wathan & Steve Schoger) |

Special thanks:
- **OpenDataLab team** (MinerU / PDF-Extract-Kit) — making high-quality document parsing available to everyone
- **virgiliojr94** (book-to-skill) — the original idea of turning books into skills
- **Adam Wathan & Steve Schoger** — the first book this pipeline was tested on

## 📄 License

MIT
