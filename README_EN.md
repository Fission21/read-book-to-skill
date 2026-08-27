# MiJi — Turn Books, Videos & Podcasts into Agent Skills

> **🌐 Language / 语言：** [中文](README.md) | [English](README_EN.md)

> Why "MiJi"? A triple pun in Chinese: **secret manual** (武林秘籍 — learn the skill the moment you hold it), **game cheat code**, and literally **honey-sweet skill (蜜技)** — brewed by CC for her Poet 🍯
>
> A complete pipeline that turns a book / PDF / video into a reusable AI Agent Skill:
> **Install MinerU (OCR) → Parse PDF → Distill methodology → Package as a Skill**
> Also supports **video / podcast** (yt-dlp download → faster-whisper transcript → same distillation flow)

This pipeline was proven end-to-end by **CC** on 2026-08-27, with two case studies:

1. ***Refactoring UI* (252-page PDF)** → packaged into the `refactoring-ui-principles` skill — validated on **another machine using opencode + GLM 5.3 Flash** with a controlled A/B test (see Demo 1 below)
2. **YouTube Chinese tech tutorial video (8:45)** → processed via video mode (yt-dlp → faster-whisper → LLM correction) into the `minimax-h3-local-deploy` skill (see Demo 2 below)

## 📦 Repository Layout

```
MiJi/
├── README.md                                    # Chinese docs
├── README_EN.md                                 # English version (this file)
├── skills/
│   ├── mineru-pdf-parser/SKILL.md               # [Prerequisite 1] MinerU PDF parsing (install/download/pitfalls)
│   └── MiJi/SKILL.md              # [Main flow] book/video → Skill pipeline
│       └── scripts/llm_fix.py                   # ASR transcript LLM correction script
├── examples/
│   └── refactoring-ui-principles/               # [Demo 1] PDF-distilled skill
│       ├── SKILL.md                             #    Refactoring UI design-principles cheat sheet
│       └── references/refactoring-ui-full.md    #    Full book archive (58 principles)
│       (Demo 2: the video-distilled minimax-h3-local-deploy skill is published alongside)
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
│     → MiJi skill (main flow)                  │
├─────────────────────────────────────────────────────────────┤
│  ⑥ Verify (skill loads + real run) & deliver                │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites (two skills)

| Skill | Purpose | Dependency |
|-------|---------|------------|
| **`mineru-pdf-parser`** | MinerU setup, model download (China-network optimized), Apple Silicon tuning, pitfalls | Steps ①/② depend on it |
| **`MiJi`** | The full 6-step book→skill workflow | The main flow itself |

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

### 🎬 Demo 2: Video Distillation in Action (Chinese tutorial → skill)

**Test video**: a YouTube Chinese tech tutorial (8:45) packed with technical terms (MiniMax H3, ComfyUI, jailbroken model, text encoder…), **no subtitles available** — pure ASR path only, a stress test for transcription quality.

**Pipeline**:

> ⚠️ **Prerequisites to replicate (AI capability checklist)**: ① any OpenAI-compatible LLM API + key (for auto-generating the transcription prompt and post-correction; deepseek/glm/kimi/local ollama all work) ② faster-whisper (`pip install faster-whisper`, runs on CPU) ③ yt-dlp ④ ffmpeg. If subtitles exist, just `--write-subs` and skip ①②.

```
YouTube link
  → yt-dlp audio download (199MB, ~50s)
  → [AI-1] LLM auto-generates initial_prompt from title alone
  → faster-whisper small + that prompt (105s)
  → [AI-2] deepseek-v4-flash LLM post-correction (20s)
  → read all 93 segments → classify as step-guide → package as skill
```

**Three-way benchmark** (same video):

| Approach | MiniMax | 越狱(jailbreak) | ComfyUI | Channel name | Total time |
|----------|:---:|:---:|:---:|:---:|:---:|
| small, no hints | ❌0 | ❌ misheard | ❌0 | ❌ misheard | 2min |
| medium model alone | ⚠️4 | ⚠️2 | ❌ still 0 | ✅3 | ⏱48min |
| **small + hints + LLM fix** 🏆 | ✅9 | ✅9 | ✅3 | ✅4 | **2min20s** |

**Key findings**:
1. `initial_prompt` with domain terms fixes Chinese homophone errors ("粤语模型" → "越狱模型") — and the prompt can be **auto-generated by LLM from the video title alone** (no manual knowledge needed, see `scripts/transcribe_prompt_gen.py`)
2. English brand names like ComfyUI are unfixable at the ASR layer — medium spent 48 minutes and still missed them
3. **LLM correction nails it in one pass**: it has world knowledge about ComfyUI and correctly infers "CONVIO的DESTOB的文件夹" should be "COMFYUI的DESKTOP文件夹" — something no ASR model can do
4. Safety verified: segment count unchanged, character ratio 1.00, timestamps preserved

**Conclusion**: the optimal path for Chinese video distillation is **small fast-transcribe + LLM refine** (2 minutes total), 20× faster than running a bigger model alone while producing higher quality. The correction script is open-sourced at `skills/MiJi/scripts/llm_fix.py`.

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
