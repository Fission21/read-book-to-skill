#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kb.py — CC 知识库管理 v2.0（MiJi 蒸馏管线的知识库形态）
========================================================
    ~/demo/knowledge-base/
    ├── AGENTS.md             # 外部 AI 读取指南（自动生成）
    ├── llms.txt              # LLM 站点地图（llmstxt.org 风格，自动生成）
    ├── INDEX.md              # 主目录（自动生成，含跨主题锚点）
    ├── exports/              # kb export 的 skill 成品
    └── topics/<主题>/
        ├── TOPIC.md          # 蒸馏条目（frontmatter 自动注入）
        ├── metadata.json     # 机器可读元数据（自动生成）
        ├── merge_draft.md    # 融合草稿
        └── sources/          # 全源存档（含 <源>.toc.md 章节锚点）

命令:
  kb init                          初始化
  kb add <主题> <文件...> [--type book|video|article] [--name xxx] [--force]
                                   添加源（sha1 指纹自动去重）+ 全量刷新
  kb draft <主题>                  生成融合草稿（之后 CC 通读写 TOPIC.md）
  kb list [主题] / kb stats        目录 / 统计
  kb search <关键词> [--topic 主题] [--limit N]
                                   纯 Python 全文检索（中文路径安全，不依赖 rg）
  kb reindex                       重建 INDEX/metadata/TOC/AGENTS.md/llms.txt
  kb export <主题> --name <slug> [--desc 一句话] [--out 目录]
                                   升格为 skill 目录

环境变量 KB_ROOT 可改库根目录（默认 ~/demo/knowledge-base）。
"""
import os, sys, re, json, shutil, hashlib, subprocess
from datetime import datetime
from collections import Counter

KB_ROOT = os.environ.get('KB_ROOT', os.path.expanduser('~/demo/knowledge-base'))


def _find_miji_scripts():
    """定位 MiJi 的 merge_sources.py：环境变量 > Hermes skill 目录 > 本仓库相对路径"""
    cands = [os.environ.get('MIJI_SCRIPTS'),
             os.path.expanduser('~/.hermes/skills/creative/miji/scripts'),
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '..', 'skills', 'miji', 'scripts')]
    for c in cands:
        if c and os.path.isfile(os.path.join(c, 'merge_sources.py')):
            return os.path.abspath(c)
    sys.stderr.write('⚠️ 找不到 MiJi scripts：设 MIJI_SCRIPTS 环境变量，或安装 MiJi skill，或在本仓库内使用\n')
    sys.exit(1)


MIJI_SCRIPTS = _find_miji_scripts()
sys.path.insert(0, MIJI_SCRIPTS)
try:
    from merge_sources import keywords as miji_keywords, token_est
except ImportError:
    sys.stderr.write('⚠️ 找不到 MiJi: %s/merge_sources.py\n' % MIJI_SCRIPTS)
    sys.exit(1)

MARKER_RE = re.compile(r'<!--\s*miji:source\s+({.*?})\s*-->')
INDEX_NAME = 'INDEX.md'
FPRINTS = os.path.join(KB_ROOT, '.fingerprints.json')


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(s)


def tdir(t): return os.path.join(KB_ROOT, 'topics', t)
def sdir(t): return os.path.join(tdir(t), 'sources')


def topic_names():
    root = os.path.join(KB_ROOT, 'topics')
    if not os.path.isdir(root):
        return []
    return sorted(n for n in os.listdir(root)
                  if os.path.isdir(os.path.join(root, n)) and not n.startswith('.'))


def strip_marker(text):
    return MARKER_RE.sub('', text, count=1)


def source_meta(text, fn):
    m = MARKER_RE.search(text[:5000])
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    return {'name': os.path.splitext(fn)[0],
            'type': 'video' if fn.lower().endswith('.txt') else 'article'}


def topic_stats(t):
    sources = []
    if os.path.isdir(sdir(t)):
        for fn in sorted(os.listdir(sdir(t))):
            p = os.path.join(sdir(t), fn)
            if not os.path.isfile(p) or fn.endswith('.toc.md'):
                continue
            text = read(p)
            meta = source_meta(text, fn)
            sources.append({'file': fn, 'name': meta.get('name', fn),
                            'type': meta.get('type', '?'),
                            'lines': text.count('\n') + 1,
                            'tokens': token_est(text),
                            'sha1': hashlib.sha1(strip_marker(text).strip().encode('utf-8')).hexdigest()[:16]})
    has_topic = os.path.isfile(os.path.join(tdir(t), 'TOPIC.md'))
    status = '✅ distilled' if has_topic else '⚪ sources-only'
    return {'topic': t, 'sources': sources,
            'tokens': sum(s['tokens'] for s in sources), 'status': status}


# ---------------- TOC（超长文本跳读锚点） ----------------
HEAD_RE = re.compile(r'^(#{1,4})\s+(.{3,80})\s*$')

def build_toc(t, src):
    """为单个源生成 .toc.md：标题 + 行号，供 REPL 式按行号跳读"""
    p = os.path.join(sdir(t), src['file'])
    entries = []
    for i, line in enumerate(read(p).splitlines(), 1):
        m = HEAD_RE.match(line.strip())
        if m and len(m.group(2)) > 2:
            entries.append((i, len(m.group(1)), m.group(2).strip()))
    if len(entries) < 3:
        return 0
    out = ['# TOC — %s（标题 → 行号，read_file(offset=行号) 跳读）\n' % src['name']]
    last = -1
    for ln, lv, title in entries:
        out.append('%s- L%d  %s' % ('  ' * (lv - 1), ln, title))
        last = ln
    write(os.path.join(sdir(t), src['file'] + '.toc.md'), '\n'.join(out) + '\n')
    return len(entries)


# ---------------- metadata.json + TOPIC frontmatter ----------------
SLUG_MAP = {'军事': 'military', '设计': 'design', '蒸馏': 'distillation'}

def ensure_metadata(t, s):
    md = {'topic': t, 'slug': SLUG_MAP.get(t, t),
          'status': 'distilled' if 'distilled' in s['status'] else 'sources-only',
          'tokens_est': s['tokens'],
          'updated': datetime.now().strftime('%Y-%m-%d'),
          'sources': s['sources']}
    write(os.path.join(tdir(t), 'metadata.json'),
          json.dumps(md, ensure_ascii=False, indent=2))
    # TOPIC.md frontmatter 注入（已有则跳过）
    tp = os.path.join(tdir(t), 'TOPIC.md')
    if os.path.isfile(tp):
        body = read(tp)
        if not body.startswith('---'):
            tags = [t, md['slug']] + [x['type'] for x in s['sources'][:3]]
            fm = ('---\ntopic: %s\nslug: %s\ntags: [%s]\nsources: [%s]\n'
                  'tokens_est: %d\nupdated: %s\n---\n\n'
                  % (t, md['slug'], ', '.join(tags),
                     ', '.join(x['name'] for x in s['sources']),
                     s['tokens'], md['updated']))
            write(tp, fm + body)


# ---------------- 指纹缓存（跨主题去重） ----------------
def load_fprints():
    if os.path.isfile(FPRINTS):
        try:
            return json.loads(read(FPRINTS))
        except Exception:
            pass
    fp = {}
    for t in topic_names():
        for src in topic_stats(t)['sources']:
            fp[src['sha1']] = '%s/%s' % (t, src['file'])
    return fp


def save_fprints(fp):
    write(FPRINTS, json.dumps(fp, ensure_ascii=False, indent=1))


# ---------------- AGENTS.md + llms.txt（外部 AI 读取规范） ----------------
def gen_external_docs(stats, anchors):
    rel = lambda t: 'topics/%s/TOPIC.md' % t
    A = ['# AGENTS.md — CC 知识库（AI 读取指南）', '',
         '> 本文件面向任何 AI/agent（Claude、GPT、Codex、其他 Hermes 实例）。',
         '> 读库顺序：本文件 → INDEX.md（总览）→ TOPIC.md（速查）→ sources/（全文）', '',
         '## 目录结构', '',
         '```', 'INDEX.md              # 自动生成的总目录（主题表+跨主题锚点）',
         'llms.txt              # LLM 站点地图（本文件的极简版）',
         'topics/<主题>/TOPIC.md   # 蒸馏速查条目：先读这个！frontmatter 含元数据',
         'topics/<主题>/metadata.json # 机器可读元数据（源清单/sha1/tokens/状态）',
         'topics/<主题>/sources/   # 解析后全文存档（带 miji:source 标记）',
         'topics/<主题>/sources/images/ # 解析出的原文插图（md 相对链接直接可达）',
         'topics/<主题>/sources/*.toc.md # 超长源的章节→行号锚点，按行号跳读',
         'exports/              # 已升格为 skill 的成品', '```', '',
         '## 读取协议', '',
         '1. **先读 INDEX.md** 决定哪个主题相关（别一上来就翻全文）',
         '2. **读该主题 TOPIC.md**（≤7KB 速查层）——大多数问题到此为止',
         '3. 需要细节时：读 `sources/<源>.toc.md` 找章节行号 → `read_file(offset=行号)` 跳读，**不要全量读 10 万 token 级的源**',
         '4. 引用内容时标注来源（源 name 在 TOPIC.md 的来源行 / metadata.json）',
         '5. 全文检索：`python3 ~/demo/scripts/kb.py search 关键词 [--topic 主题]`', '',
         '## 规范约定', '',
         '- 每源文件首行有 `<!-- miji:source {"name":..,"type":..} -->` 标记（机器可解析）',
         '- tokens 均为估算值（中文 ~1.6 字/token），以 ~ 前缀标识',
         '- TOPIC.md 内容标注来源（[书]/[视频]），冲突观点并列不裁决',
         '- 单源 >80K tokens 时 TOPIC.md 必须存在（速查层强制）',
         '- sources/images/ 存原文插图，md 相对链接直接可达（Obsidian/VSCode/GitHub 均可渲染）', '',
         '## 已知坑与对策', '',
         '| 坑 | 对策 |',
         '|----|------|',
         '| 中文路径下部分检索工具不可靠 | 用 kb.py search（纯 Python 实现）|',
         '| 超长源全量读撑爆上下文 | 走 *.toc.md 行号跳读 |',
         '| 重复入库同一内容 | add 自动 sha1 去重（--force 可越过）|',
         '| INDEX.md 手改被覆盖 | 别手改，它由 kb reindex 生成 |', '']
    write(os.path.join(KB_ROOT, 'AGENTS.md'), '\n'.join(A))

    L = ['# CC 知识库', '',
         '> MiJi 多源蒸馏知识库：PDF/视频/文章 → 解析 → 主题化速查 + 全文存档。供 LLM 检索读取。', '',
         '## Topics', '']
    for s in stats:
        desc = ''
        tp = os.path.join(tdir(s['topic']), 'TOPIC.md')
        if os.path.isfile(tp):
            for line in read(tp).splitlines():
                sl = line.strip()
                if sl.startswith('>') and '来源' in sl:
                    desc = sl.lstrip('> ').strip()[:80]
                    break
                if sl and not sl.startswith(('#', '>', '---')) and ':' not in sl[:12]:
                    desc = sl[:80]
                    break
        L.append('- [%s](%s): %s (~%s tok, %s)' % (s['topic'], rel(s['topic']),
                                                   desc, format(s['tokens'], ','), s['status']))
    if anchors:
        L += ['', '## Cross-topic anchors', '']
        L += ['- **%s** (%d): %s' % (w, c, ', '.join(ts)) for w, c, ts in anchors[:10]]
    write(os.path.join(KB_ROOT, 'llms.txt'), '\n'.join(L) + '\n')


# ---------------- reindex 核心 ----------------
def reindex():
    stats = [topic_stats(t) for t in topic_names()]
    kw_map = {}
    for s in stats:
        text = ''.join(read(os.path.join(sdir(s['topic']), src['file']))
                       for src in s['sources'])
        kw_map[s['topic']] = set(miji_keywords(text, 25)) if text else set()
    cnt = Counter()
    for ks in kw_map.values():
        cnt.update(ks)
    anchors = [(w, c, [t for t in kw_map if w in kw_map[t]])
               for w, c in cnt.most_common(60) if c >= 2]

    # 每主题：metadata + TOC + frontmatter
    for s in stats:
        ensure_metadata(s['topic'], s)
        for src in s['sources']:
            n = build_toc(s['topic'], src)
            src['toc_entries'] = n

    L = ['# 📚 CC 知识库', '',
         '> MiJi 蒸馏管线的知识库形态 · INDEX.md 自动生成于 %s（手改会被 reindex 覆盖）' %
         datetime.now().strftime('%Y-%m-%d %H:%M'),
         '> AI 读取规范见 AGENTS.md · 检索: `kb.py search 关键词`', '']
    L += ['## 🗂 主题目录', '', '| 主题 | 状态 | 源数 | ~tokens |', '|---|---|---|---|']
    for s in stats:
        L.append('| **%s** | %s | %d | ~%s |' % (s['topic'], s['status'],
                                                 len(s['sources']), format(s['tokens'], ',')))
    if not stats:
        L.append('| （空） | | | |')
    L.append('')
    if anchors:
        L += ['## 🔗 跨主题锚点（≥2 主题共同出现的关键词）', '']
        L += ['- **%s** (%d 主题): %s' % (w, c, ', '.join(ts)) for w, c, ts in anchors]
        L.append('')
    L += ['## 📖 主题详情', '']
    for s in stats:
        L.append('### %s  %s' % (s['topic'], s['status']))
        tp = os.path.join(tdir(s['topic']), 'TOPIC.md')
        if os.path.isfile(tp):
            heads = [l for l in read(tp).splitlines() if l.strip()][:1]
            if heads:
                L.append('> ' + heads[0].lstrip('# ').strip())
        L += ['', '| 源 | 类型 | 行数 | ~tokens | TOC |', '|---|---|---|---|---|']
        for src in s['sources']:
            L.append('| %s | %s | %d | ~%s | %s |' % (
                src['name'], src['type'], src['lines'], format(src['tokens'], ','),
                ('%d 条' % src['toc_entries']) if src.get('toc_entries') else '—'))
        L.append('')
    write(os.path.join(KB_ROOT, INDEX_NAME), '\n'.join(L) + '\n')
    gen_external_docs(stats, anchors)
    save_fprints(load_fprints())
    return stats, anchors


# ---------------- 命令 ----------------
def cmd_init(a):
    os.makedirs(os.path.join(KB_ROOT, 'topics'), exist_ok=True)
    os.makedirs(os.path.join(KB_ROOT, 'exports'), exist_ok=True)
    stats, _ = reindex()
    print('✅ 知识库就绪: %s | 主题 %d 个' % (KB_ROOT, len(stats)))


def cmd_add(a):
    if not a:
        return usage('add 需要 <主题> 和至少一个文件')
    topic = a.pop(0)
    typ = name = None
    force = False
    files, i = [], 0
    while i < len(a):
        if a[i] == '--type' and i + 1 < len(a):
            typ = a[i + 1]; i += 2
        elif a[i] == '--name' and i + 1 < len(a):
            name = a[i + 1]; i += 2
        elif a[i] == '--force':
            force = True; i += 1
        else:
            files.append(a[i]); i += 1
    if not files:
        return usage('add 需要至少一个文件')
    os.makedirs(sdir(topic), exist_ok=True)
    fp = load_fprints()
    for f in files:
        f = os.path.expanduser(f)
        if not os.path.isfile(f):
            print('⚠️ 跳过不存在: %s' % f)
            continue
        raw = read(f)
        h = hashlib.sha1(strip_marker(raw).strip().encode('utf-8')).hexdigest()[:16]
        if h in fp and not force:
            print('⏭️ 内容重复（%s 已在 %s），跳过: %s（--force 可强制）' % (h, fp[h], f))
            continue
        base = os.path.basename(f)
        dest = os.path.join(sdir(topic), base)
        if os.path.abspath(f) != os.path.abspath(dest):
            shutil.copy2(f, dest)
        text = read(dest)
        if not MARKER_RE.search(text[:5000]):
            meta = {'name': name or os.path.splitext(base)[0],
                    'type': typ or ('video' if base.lower().endswith('.txt') else 'article'),
                    'added': datetime.now().strftime('%Y-%m-%d')}
            write(dest, '<!-- miji:source %s -->\n\n' % json.dumps(meta, ensure_ascii=False) + text)
        fp[h] = '%s/%s' % (topic, base)
        print('📥 %s ← %s (sha1:%s)' % (topic, base, h))
    save_fprints(fp)
    stats, anchors = reindex()
    print('📌 全量刷新完成（主题 %d，锚点 %d，INDEX/metadata/TOC/AGENTS.md/llms.txt 已更新）'
          % (len(stats), len(anchors)))


def cmd_draft(a):
    if not a:
        return usage('draft 需要 <主题>')
    t = a[0]
    if not os.path.isdir(sdir(t)):
        return usage('主题 %s 还没有源，先 kb add' % t)
    files = [os.path.join(sdir(t), f) for f in sorted(os.listdir(sdir(t)))
             if os.path.isfile(os.path.join(sdir(t), f)) and not f.endswith('.toc.md')]
    r = subprocess.run([sys.executable, os.path.join(MIJI_SCRIPTS, 'merge_sources.py'), tdir(t)] + files,
                       capture_output=True, text=True)
    print((r.stdout or r.stderr).strip())
    print('→ 下一步: CC 通读 %s/merge_draft.md → 写 TOPIC.md' % tdir(t))


def cmd_search(a):
    kw = None
    topic = limit = None
    i = 0
    while i < len(a):
        if a[i] == '--topic' and i + 1 < len(a):
            topic = a[i + 1]; i += 2
        elif a[i] == '--limit' and i + 1 < len(a):
            limit = int(a[i + 1]); i += 2
        elif kw is None:
            kw = a[i]; i += 1
        else:
            i += 1
    if not kw:
        return usage('search 需要 <关键词>')
    kws = [k for k in re.split(r'[,，\s]+', kw) if k]
    topics = [topic] if topic else topic_names()
    hits, scanned = [], 0
    for t in topics:
        cands = [(os.path.join(tdir(t), 'TOPIC.md'), 'TOPIC')] if os.path.isfile(os.path.join(tdir(t), 'TOPIC.md')) else []
        if os.path.isdir(sdir(t)):
            cands += [(os.path.join(sdir(t), f), f)
                      for f in sorted(os.listdir(sdir(t)))
                      if os.path.isfile(os.path.join(sdir(t), f)) and not f.endswith('.toc.md')]
        for path, label in cands:
            scanned += 1
            for ln, line in enumerate(read(path).splitlines(), 1):
                low = line.lower()
                if all(k.lower() in low for k in kws):
                    hits.append((t, label, ln, line.strip()[:110]))
                    if len(hits) >= (limit or 30):
                        break
            if len(hits) >= (limit or 30):
                break
        if len(hits) >= (limit or 30):
            break
    print('🔎 "%s" → %d 条命中（扫描 %d 个文件）' % (kw, len(hits), scanned))
    for t, label, ln, line in hits:
        print('  [%s/%s] L%d: %s' % (t, label, ln, line))
    if not hits:
        print('  （试试减少关键词或换词）')


def cmd_list(a):
    if a and not a[0].startswith('-'):
        s = topic_stats(a[0])
        print('主题: %s  状态: %s  ~tokens: %s' % (s['topic'], s['status'], format(s['tokens'], ',')))
        for src in s['sources']:
            print('  · [%s] %s  (%s, ~%s tok%s)' % (src['type'], src['name'], src['file'],
                                                    format(src['tokens'], ','),
                                                    ', TOC %d 条' % src.get('toc_entries', 0) if src.get('toc_entries') else ''))
        print('  目录: %s' % tdir(s['topic']))
        return
    stats, _ = reindex()
    for s in stats:
        print('%-28s %-14s %d 源  ~%s tok' % (s['topic'], s['status'], len(s['sources']),
                                              format(s['tokens'], ',')))


def cmd_stats(a):
    stats, anchors = reindex()
    print('主题 %d | 源 %d | 已蒸馏 %d | ~%s tokens | 跨主题锚点 %d' %
          (len(stats), sum(len(s['sources']) for s in stats),
           sum(1 for s in stats if 'distilled' in s['status']),
           format(sum(s['tokens'] for s in stats), ','), len(anchors)))


def cmd_reindex(a):
    stats, anchors = reindex()
    print('✅ 全量刷新: %d 主题 / %d 锚点 / metadata+TOC+AGENTS.md+llms.txt 已同步'
          % (len(stats), len(anchors)))


def cmd_export(a):
    if not a:
        return usage('export 需要 <主题>')
    t = a.pop(0)
    name = desc = out = None
    i = 0
    while i < len(a):
        if a[i] == '--name' and i + 1 < len(a):
            name = a[i + 1]; i += 2
        elif a[i] == '--desc' and i + 1 < len(a):
            desc = a[i + 1]; i += 2
        elif a[i] == '--out' and i + 1 < len(a):
            out = a[i + 1]; i += 2
        else:
            i += 1
    tp = os.path.join(tdir(t), 'TOPIC.md')
    if not os.path.isfile(tp):
        return usage('主题 %s 还没蒸馏（先 kb draft + CC 写 TOPIC.md）' % t)
    slug = name or t
    out = out or os.path.join(KB_ROOT, 'exports', slug + '-skill')
    os.makedirs(os.path.join(out, 'references'), exist_ok=True)
    body = read(tp)
    if not desc:
        lines = [l.strip() for l in body.splitlines()
                 if l.strip() and not l.strip().startswith(('#', '>', '---'))
                 and ':' not in l[:12]]
        desc = (lines[0] if lines else t)[:60]
    write(os.path.join(out, 'SKILL.md'),
          '---\nname: %s\ndescription: %s\nversion: 1.0.0\nauthor: CC\n---\n\n%s' % (slug, desc, body))
    for fn in sorted(os.listdir(sdir(t))):
        if not fn.endswith('.toc.md'):
            shutil.copy2(os.path.join(sdir(t), fn), os.path.join(out, 'references', fn))
    print('📦 已导出 skill 目录: %s' % out)


def usage(msg=None):
    if msg:
        print('⚠️ ' + msg)
    print(__doc__)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        return usage()
    cmd, rest = sys.argv[1], sys.argv[2:]
    table = {'init': cmd_init, 'add': cmd_add, 'draft': cmd_draft, 'search': cmd_search,
             'list': cmd_list, 'ls': cmd_list, 'reindex': cmd_reindex,
             'stats': cmd_stats, 'export': cmd_export}
    fn = table.get(cmd)
    if not fn:
        return usage('未知命令: %s' % cmd)
    fn(rest)


if __name__ == '__main__':
    main()
