#!/usr/bin/env python3
"""
MiJi 多源融合辅助 — merge_sources.py
把多个已解析源（PDF/视频转写/文章 md）合并成一个「主题树」草稿，
供 agent 通读后蒸馏成组合 skill。

用法:
  python3 merge_sources.py 输出目录 <source1.md> <source2.txt> ...

每个源需带 SOURCE 标记行（MiJi Step 1 产出自动包含）:
  source1.md 里:  <!-- miji:source {"name": "refactoring-ui", "type": "book"} -->
  source2.txt 里: <!-- miji:source {"name": "minimax-h3", "type": "video"} -->

没有标记的源自动按文件名推断 type（.txt→video, .md→book/article）。

输出: <输出目录>/merge_draft.md
  - 每源一节的摘要头（行数/词数/token 估算）
  - 交叉主题提示（keywords 共现分析，给 agent 蒸馏时的融合锚点）
"""
import sys, os, re, json, hashlib
from collections import Counter


STOPWORDS = set("""the a an and or of to in for with on is are was were be been
的 了 是 在 和 与 有 就 不 都 也 人 一个 我们 你们 他们 它 这 那 及 或 等 对
by as at from that this it its will can may should would could""".split())


def token_est(text: str) -> int:
    """粗略 token 估算：中文按 1.6 字/token，英文按 4 字符/token"""
    cn = len(re.findall(r'[\u4e00-\u9fff]', text))
    other = len(re.findall(r'[A-Za-z0-9]+', text))
    return int(cn / 1.6 + other * 1.3)


def parse_source_marker(text: str, path: str) -> dict:
    m = re.search(r'<!--\s*miji:source\s+({.*?})\s*-->', text[:5000])
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # 自动推断
    ext = os.path.splitext(path)[1].lower()
    t = 'video' if ext in ('.txt',) else 'book'
    name = os.path.splitext(os.path.basename(path))[0]
    return {'name': name, 'type': t}


# 高频功能词（书正文里大量出现的通用词，与主题无关）
_GENERIC = set("""you your like when but have make more don way need use there
using not just size look out all this they them their what how why who which
where while than then them once also only over under again each other some
design text color like start starting from into about get got page pages
section sections chapter chapters figure figures example examples note
image images thing things good bad better best new old first last
能 会 要 说 去 也 很 被 把 让 从 而 为 之 于 其 这 那 个 有 无 上 下""".split())


def keywords(text: str, top_n: int = 25):
    """中英混合关键词提取：英文词频 + 中文 2-4 字词切分（过滤通用功能词）"""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    en = re.findall(r'[A-Za-z][A-Za-z0-9_.-]{2,}', text)
    en = [w.strip('._-').lower() for w in en]
    en = [w for w in en if len(w) >= 3 and w not in STOPWORDS and w not in _GENERIC]
    cn_segments = re.findall(r'[\u4e00-\u9fff]{2,8}', text)
    cn_words = []
    for seg in cn_segments:
        for n in (2, 3, 4):
            cn_words += [seg[i:i+n] for i in range(len(seg) - n + 1)]
    en_counts = Counter(en)
    # 过滤只出现 1 次的中文切片噪声
    cn_counts = Counter(w for w, c in Counter(cn_words).items() if c >= 3)
    merged = Counter(en_counts)
    merged.update(cn_counts)
    # 大小源平衡：不只按绝对频次（大源会碾压），保留 top_n×3 供交叉分析
    return [w for w, _ in merged.most_common(top_n * 3)]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    out_dir = sys.argv[1]
    sources = sys.argv[2:]
    os.makedirs(out_dir, exist_ok=True)

    parsed = []
    for p in sources:
        if not os.path.isfile(p):
            print(f'⚠️ 跳过不存在的源: {p}', file=sys.stderr)
            continue
        raw = open(p, encoding='utf-8', errors='replace').read()
        meta = parse_source_marker(raw, p)
        clean = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', raw)  # 去图片占位
        clean = re.sub(r'\n{3,}', '\n\n', clean)
        parsed.append({
            'meta': meta,
            'path': p,
            'text': clean,
            'lines': clean.count('\n') + 1,
            'words': len(clean),
            'tokens': token_est(clean),
            'keywords': keywords(clean),
        })

    total_tokens = sum(s['tokens'] for s in parsed)
    lines = []
    lines.append('# MiJi 多源融合草稿\n')
    lines.append(f'> 源数量: {len(parsed)} | 合计约 {total_tokens:,} tokens')
    lines.append('> 用途: agent 通读此草稿 → 按「融合策略」蒸馏成组合 skill\n')

    lines.append('## 📊 源清单\n')
    lines.append('| # | 名称 | 类型 | 行数 | Tokens |')
    lines.append('|---|------|------|------|--------|')
    for i, s in enumerate(parsed, 1):
        lines.append(f"| {i} | {s['meta']['name']} | {s['meta']['type']} | {s['lines']} | ~{s['tokens']:,} |")
    lines.append('')

    # 交叉主题：出现在 ≥2 个源的关键词
    kw_sets = [set(s['keywords']) for s in parsed]
    cross = Counter()
    for kws in kw_sets:
        cross.update(kws)
    shared = [(w, c) for w, c in cross.most_common(40) if c >= 2]
    if shared:
        lines.append('## 🔗 交叉主题锚点（≥2 个源共同出现，蒸馏时优先用这些组织结构）\n')
        for w, c in shared:
            srcs = [s['meta']['name'] for s, ks in zip(parsed, kw_sets) if w in ks]
            lines.append(f'- **{w}** ({c} 源): {", ".join(srcs)}')
        lines.append('')

    lines.append('## 📚 各源内容\n')
    for i, s in enumerate(parsed, 1):
        lines.append(f"\n---\n\n## 源 {i}: {s['meta']['name']} ({s['meta']['type']})\n")
        lines.append(f"> 路径: `{s['path']}`\n")
        lines.append(s['text'])

    out_path = os.path.join(out_dir, 'merge_draft.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'✅ 融合草稿: {out_path}')
    print(f'   源: {len(parsed)} | 合计 ~{total_tokens:,} tokens | 交叉锚点: {len(shared)} 个')
    for w, c in shared[:10]:
        print(f'   🔗 {w} ({c})')


if __name__ == '__main__':
    main()
