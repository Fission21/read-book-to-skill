#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compare_deep.py — 严谨版：归一化包含率 + 图片页行为 + 幻觉扫描"""
import os, re, random

MINERU = '/tmp/jomini_clean.md'
LUNA_DIR = os.path.expanduser('~/demo/ingest/luna-full/text')

def norm(t):
    return re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]', '', t)

m = open(MINERU, encoding='utf-8').read()
m_norm = norm(m)
pages = [open(os.path.join(LUNA_DIR, 'p%03d.md' % i), encoding='utf-8').read()
         if os.path.isfile(os.path.join(LUNA_DIR, 'p%03d.md' % i)) else ''
         for i in range(1, 485)]

# 1) luna 去水印行后中文字数 vs MinerU
wm_re = re.compile(r'.*(fineprint|pdfFactory).*', re.I)
luna_clean = '\n'.join(l for l in luna_all if not wm_re.match(l)) if (luna_all := '\n'.join(pages)) else ''
cn = lambda t: len(re.findall(r'[\u4e00-\u9fff]', t))
print('① 中文量: MinerU=%s | luna去水印后=%s (差 %+d, %.1f%%)' % (
    format(cn(m), ','), format(cn(luna_clean), ','),
    cn(luna_clean) - cn(m), 100 * (cn(luna_clean) - cn(m)) / cn(m)))

# 2) 归一化包含率：luna 句子在 MinerU 全文中的命中情况
random.seed(42)
sample = random.sample(range(30, 460), 8) + [100, 357]  # 随机8页 + 之前测过的2页
tot_hit = tot_sent = 0
print('\n② 包含率检验（luna 句 → MinerU 全文归一化子串命中）:')
for pg in sample:
    sents = [norm(s) for s in re.split(r'[。；！？]', pages[pg - 1]) if len(norm(s)) >= 15]
    hits = sum(1 for s in sents if s in m_norm)
    tot_hit += hits; tot_sent += len(sents)
    misses = [s for s in sents if s not in m_norm][:2]
    show = ('  未命中例: ' + ' ┃ '.join(x[:40] for x in misses)) if misses else ''
    print('  页%03d: %d/%d = %d%%%s' % (pg, hits, len(sents), 100 * hits // max(len(sents), 1), show))
print('  合计: %d/%d = %.1f%%' % (tot_hit, tot_sent, 100 * tot_hit / max(tot_sent, 1)))

# 3) MinerU 有插图引用的页，luna 怎么处理了？
img_pages = []
for i, l in enumerate(m.split('\n')):
    if '![](' in l or '![' in l:
        # 无法直接映射行→页，用近似: MinerU 6277行/484页 ≈ 13行/页
        img_pages.append(min(484, max(1, i // 13 + 1)))
img_pages = sorted(set(img_pages))[:4]
print('\n③ 插图页(近似定位 %s) luna 的处理:' % img_pages)
for pg in img_pages:
    head = pages[pg - 1].strip().replace('\n', ' ')[:80]
    print('  页%03d: %s' % (pg, head))

# 4) 幻觉/元话语扫描
pats = ['以下是', '无法识别', '抱歉', '转写如下', '图片显示', '图中', '这一页包含', '页面显示']
print('\n④ 元话语/幻觉扫描（整本 484 页）:')
for p in pats:
    c = sum(1 for pg in pages if p in pg)
    if c:
        print('  "%s": %d 页' % (p, c))
print('（未列出 = 0 页出现）')
