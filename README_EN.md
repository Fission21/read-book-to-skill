# MiJi — Turn Books, Videos & Podcasts into Agent Skills

> **🌐 Language / 语言：** [中文](README.md) | [English](README_EN.md)

> Why "MiJi"? A triple pun in Chinese: **secret manual** (武林秘籍 — learn the skill the moment you hold it), **game cheat code**, and literally **honey-sweet skill (蜜技)** — brewed by CC for her Poet 🍯
>
> A complete pipeline that turns a book / PDF / video into a reusable AI Agent Skill:
> **Install MinerU (OCR) → Parse PDF → Distill methodology → Package as a Skill**
> Also supports **video / podcast** (yt-dlp download → faster-whisper transcript → same distillation flow)
>
> v1.3.0 adds: **multi-source fusion** (book + video + article → one combined skill) and a **knowledge-base mode** (skip the skill packaging, keep distilling into topic folders with a built-in AI reading protocol); plus **parallel parsing for big files** (measured 2.1×)
> **Runs fully local**: the OCR / layout-recognition models are installed on YOUR device — book contents never leave the machine (see "Privacy & Local-Only Processing" below)

This pipeline was proven end-to-end by **CC**, with three case studies:

1. ***Refactoring UI* (252-page PDF)** → packaged into the `refactoring-ui-principles` skill — validated on **another machine using opencode + GLM 5.3 Flash** with a controlled A/B test (see Demo 1 below)
2. **YouTube Chinese tech tutorial video (8:45)** → processed via video mode (yt-dlp → faster-whisper → LLM correction) into the `minimax-h3-local-deploy` skill (see Demo 2 below)
3. ***Précis de l'Art de la Guerre* (Jomini, 484-page scanned PDF)** → knowledge-base topic `military`; also validated **2.1× parallel parsing** (2026-09-01, see Demo 3 below)

## 📦 Repository Layout

```
MiJi/
├── README.md                                    # Chinese docs
├── README_EN.md                                 # English version (this file)
├── skills/
│   ├── mineru-pdf-parser/SKILL.md               # [Prerequisite 1] MinerU PDF parsing (install/download/pitfalls)
│   └── miji/SKILL.md                            # [Main flow] book/video → Skill pipeline
│       └── scripts/
│           ├── llm_fix.py                       # ASR transcript LLM correction script
│           ├── transcribe_prompt_gen.py         # auto-generate transcription hints from the video title
│           └── merge_sources.py                 # multi-source fusion draft (cross-topic anchors)
├── examples/
│   └── refactoring-ui-principles/               # [Demo 1] PDF-distilled skill
│       ├── SKILL.md                             #    Refactoring UI design-principles cheat sheet
│       └── references/refactoring-ui-full.md    #    Full book archive (58 principles)
│       (Demo 2: the video-distilled minimax-h3-local-deploy skill is published alongside)
├── tools/
│   ├── kb.py                                    # knowledge-base CLI (add/search/draft/export)
│   └── split_pdf.py                             # split a PDF by page ranges (for parallel parsing)
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
│     (252 pages ≈ 4-6 min; scanned books go through OCR and    │
│      are 3-4× slower: 484 pages > 20 min)                    │
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
| 4 parallel MinerU workers → MPS memory accumulation crash | Apple Silicon 32GB limit = 2 workers (2.1×, see "Parallel Parsing") |
| Dragging a PDF into a chat only delivers an icon PNG | That's a placeholder thumbnail — the file itself wasn't uploaded; pass a file path instead |
| Scanned book parsing feels "too slow" | Not stuck: scanned books run OCR and are 3-4× slower than text-layer PDFs (484 pages > 20 min), or go parallel for 2.1× |

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

**Conclusion**: the optimal path for Chinese video distillation is **small fast-transcribe + LLM refine** (2 minutes total), 20× faster than running a bigger model alone while producing higher quality. The correction script is open-sourced at `skills/miji/scripts/llm_fix.py`.

### 📚 Demo 3: 484-page scanned book → knowledge base (2026-09-01)

*Précis de l'Art de la Guerre* (Jomini, 484 pages, **scanned PDF without a text layer**):

```
484-page scanned PDF
  → MinerU local OCR (22.4 min single-process; or split in 2 + 2 workers → 10.7 min, 2.1×)
  → 6,278-line Markdown + 62 original illustrations → kb.py add military (sha1 dedup)
  → auto-generated chapter-anchor TOC (heading → line number: jump-read 180K tokens without blowing context)
  → CC reads the core chapters → distilled TOPIC.md cheat sheet (decisive-point doctrine / three-choice framework / lines of operations)
```

Two hard limits validated along the way: **2 workers = 2.1× speedup**; **4 workers crash 2/4** (MPS memory accumulation) — the sweet spot on Apple Silicon 32GB is exactly two parallel workers.

### ☁️ Demo 4: dual-engine head-to-head — local OCR vs cloud VLM (cost $2.51)

The same 484-page scanned book, parsed **in full by both engines**, then compared rigorously (2026-09-01):

| Engine | Setup | Time | Result | Cost |
|--------|-------|------|--------|------|
| 🖥 MinerU local (pipeline) | M1 Pro, single process | 22.4 min | 484/484 ✅ | electricity |
| ☁️ GPT-5.6-luna vision transcription | **6 concurrent API calls** | 46 min | **484/484 ✅, zero failures, zero retries** | **$2.51** (≈0.5¢/page) |

**Quality comparison (whole-book, not sampled)**:

| Dimension | Local MinerU | Cloud luna |
|-----------|--------------|------------|
| Character-level agreement | — | **~97%** (10-char sliding window 75.5% → back-computed; remainder is homophone/paraphrase-level drift) |
| Chinese chars | 276,727 | 294,230 (+6.3%: page numbers transcribed 479 lines + fuller footnotes + light polishing) |
| Illustrations | **36 battle diagrams extracted, searchable in the KB** | **0 (all lost)** |
| Footnote markers | 156 | 303 (it even caught in-text footnote marks the layout filter dropped → can backfill the local result) |
| Hallucination/meta-speak | none | only 2 pages say "图中" in reasonable context — **no fabrication observed** |

**Three takeaways**:
1. **Accuracy is a tie, with different strengths**: luna nails harder glyphs (「不与」 where local OCR misread 「不同」) but paraphrases a little — for faithful archival, local is safer
2. **The cloud's real edge is concurrency**: local is capped at 2 workers by MPS (2.1× ceiling); 20 cloud workers could squeeze 46 min into under 10 — for money
3. **Illustrated books belong to local**: luna produces zero images; all 36 battle diagrams came from MinerU

**Reproduce** (scripts in `tools/`, resumable; token limit ≥4000 or it truncates):

```bash
# cloud full transcription (6 concurrent workers)
mineru-venv/bin/python tools/luna_full_transcribe.py book.pdf outdir --workers 6
# dual-engine comparison (char agreement / hallucination scan / page-length distribution)
python3 tools/compare_deep.py
```

## 📚 Knowledge-Base Mode (v1.3.0)

MiJi doesn't have to produce one-shot skills — the same parse → distill pipeline can **keep distilling into topic folders**, building a personal knowledge base:

```bash
python3 tools/kb.py init                          # initialize
python3 tools/kb.py add <topic> <files...>        # ingest from any source (PDF / video transcript / article, sha1 dedup)
python3 tools/kb.py draft <topic>                 # multi-source fusion draft (cross-topic anchors)
python3 tools/kb.py search <keyword> [--topic X]  # full-text search (pure Python, CJK-path safe)
python3 tools/kb.py export <topic> --name <slug>  # promote a topic into a skill folder
```

Repository layout (all auto-generated / maintained):

```
knowledge-base/
├── AGENTS.md                # reading protocol for ANY AI (Claude/GPT/Codex/Cursor…)
├── llms.txt                 # llmstxt.org-style site map
├── INDEX.md                 # auto TOC (topic table + cross-topic anchors)
└── topics/<topic>/
    ├── TOPIC.md             # distilled cheat sheet (YAML frontmatter; works in Obsidian/Logseq as-is)
    ├── metadata.json        # machine-readable metadata (source list / sha1 / tokens)
    └── sources/             # full-text archive + images/ illustrations + *.toc.md chapter anchors
```

- **Interops with other AI tools**: plain markdown + YAML frontmatter — opens directly in Obsidian / VSCode / any renderer; agent tools just read `AGENTS.md` to understand the whole protocol
- **Long-document strategy**: sources at the 100K-token scale must **never be read whole** — `*.toc.md` gives heading → line-number anchors, paired with `kb.py search` for targeted jump-reading
- **skill vs knowledge base**: a skill = frequently-used operating rules; the knowledge base = low-frequency but searchable sediment. Both can coexist for the same topic, and any TOPIC.md can be `export`ed into a skill at any time

## ⚡ Parallel Parsing for Big Files (measured 2.1×)

A few-hundred-page scanned PDF takes 20+ minutes in a single process. Split it and go parallel:

```bash
# 1. split (pure CPU, seconds)
python3 tools/split_pdf.py input.pdf split-dir 2
# 2. launch one MinerU background process per part (each: unset PYTHONPATH + WINDOW_SIZE=32 + its own output dir)
# 3. merge in order: cat p1/*/auto/*.md p2/*/auto/*.md > merged.md (remember to strip PDF watermark lines)
```

| Approach | 484-page scanned book, measured |
|----------|--------------------------------|
| single process | 22.4 min |
| **split ×2, 2 workers** | **10.7 min (2.1×)** |
| split ×4, 4 workers | ❌ 2/4 crashed (MPS memory accumulation) |

- Quality is equivalent: merged output matches the serial run in line count, the split seam is seamless, only ~2% line-level OCR jitter
- **On Apple Silicon 32GB the safe ceiling is exactly 2 workers** (3 untested — don't push it)
- For scanned tomes only; text-layer PDFs already parse fast (252 pages in 4-6 min) and aren't worth splitting
- A crashed part can simply be re-run (independent output dirs, idempotent)

## 🔒 Privacy & Local-Only Processing (the OCR / vision models live on YOUR device)

This pipeline is **local by default** — suitable for copyrighted books and private material that must never leave the machine:

| Stage | Where it runs | Notes |
|-------|---------------|-------|
| **PDF layout & OCR** | **Your device** | MinerU pipeline mode: PP-DocLayoutV2 (layout), PaddleOCR (text recognition), unimernet (formulas), table models — ~1GB of weights installed locally, **runs offline** |
| Video transcription | Your device | faster-whisper runs locally (CPU is fine); audio is never uploaded |
| Image extraction | Your device | illustrations are cut out by local models and stored locally |
| LLM correction / prompt gen | **Optional cloud** | the only step that may touch the network; use local ollama for a fully offline run, or skip it (slightly lower quality) |
| Distillation itself | Your agent | skill / knowledge-base generation needs no external service |

> Demo 3's book (a publisher's scan of *Précis de l'Art de la Guerre*) was processed entirely on-machine — no page content ever left the computer.

Two notes:
- MinerU's `hybrid` / VLM engine would invoke a vision-language model (more VRAM / may use network) — **this pipeline always uses `-b pipeline`, the local engine**
- faster-whisper downloads its model from HuggingFace on first run (a few hundred MB, one-time), fully offline afterwards

## 🙏 Dependencies & Acknowledgements

This pipeline stands on these great open-source projects — thank you to their authors:

| Dependency | GitHub | Used for |
|------------|--------|----------|
| **MinerU** | https://github.com/opendatalab/MinerU | PDF parsing engine (OCR/layout/formula/table) — the core |
| **PDF-Extract-Kit-1.0** | https://github.com/opendatalab/PDF-Extract-Kit | MinerU's model repo (7 sub-models: Layout/MFR/OCR/TabRec…) |
| **book-to-skill** | https://github.com/virgiliojr94/book-to-skill | Inspiration for book→skill (Copilot/Amp/Claude Code ecosystem; this repo is the Hermes-flavored cheat-sheet variant) |
| **aria2** | https://github.com/aria2/aria2 | Multi-threaded model download (810MB from modelscope in ~20s) |
| **ModelScope** | https://github.com/modelscope/modelscope | High-speed model source inside China |
| **pypdfium2** | https://github.com/pypdfium2-team/pypdfium2 | PDF page splitting (prerequisite for parallel parsing) |
| **Refactoring UI** | https://refactoringui.com | Validation case (Adam Wathan & Steve Schoger) |

Special thanks:
- **OpenDataLab team** (MinerU / PDF-Extract-Kit) — making high-quality document parsing available to everyone
- **virgiliojr94** (book-to-skill) — the original idea of turning books into skills
- **Adam Wathan & Steve Schoger** — the first book this pipeline was tested on

## 📄 License

MIT
