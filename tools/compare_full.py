#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compare_full.py — 本地 MinerU vs 云端 luna 全本对比"""
import os, re, json, random, difflib

MINERU = '/tmp/jomini_clean.md'
LUNA_DIR = os.path.expanduser('~/demo/ingest/luna-full/text')

def stats(t, name):
    cn = len(re.findall(r'[\u4e00-\u9fff]', t))
    total = len(t)
    return {'name': name, 'chars': total, 'cn_chars': cn,
            'lines': t.count('\n') + 1,
            'para_blank': len(re.findall(r'\n\s*\n', t)),
            'headings': len(re.findall(r'^#{1,4} ', t, re.M)),
            'img_refs': len(re.findall(r'!\[', t)),
            'fn_marks': len(re.findall(r'[①②③④⑤⑥⑦⑧⑨⑩]', t)),
            'watermark': t.count('fineprint')}

m = open(MINERU, encoding='utf-8').read()
pages = []
for i in range(1, 485):
    p = os.path.join(LUNA_DIR, 'p%03d.md' % i)
    pages.append(open(p, encoding='utf-8').read() if os.path.isfile(p) else '')
luna = '\n\n<!-- page break -->\n\n'.join(pages)

sm, sl = stats(m, 'MinerU本地'), stats(luna, 'luna云端')
print('=== 量化对比 ===')
for k in ['chars', 'cn_chars', 'lines', 'headings', 'img_refs', 'fn_marks', 'watermark']:
    print('%-12s MinerU=%-8s luna=%-8s' % (k, format(sm[k], ','), format(sl[k], ',')))

# 抽样 5 页逐句精对（固定种子可复现）
random.seed(42)
sample = random.sample(range(30, 460), 5)
m_lines = [l for l in m.split('\n') if len(l.strip()) >= 20]
print('\n=== 抽样 5 页精对（luna句 → MinerU 最相似段）===')
for pg in sample:
    t = pages[pg - 1]
    # 取该页 3 个最长句（去标点干扰）
    sents = sorted(re.split(r'[。；]', t), key=len, reverse=True)[:3]
    sims = []
    for s in sents:
        s = s.strip()
        if len(s) < 20:
            continue
        best = max(difflib.SequenceMatcher(None, s, ml).ratio()
                   for ml in m_lines[::3])  # 步长3采样提速
        sims.append(round(best, 3))
    avg = round(sum(sims) / len(sims), 3) if sims else None
    print('页%03d: 平均相似度 %s  (%s)' % (pg, avg, sims))

# luna 每页字数分布（找异常页：空/超短/超长）
lens = [(i + 1, len(p)) for i, p in enumerate(pages)]
short = [x for x in lens if x[1] < 120]
long_ = [x for x in lens if x[1] > 3500]
print('\n=== luna 页长分布 ===')
print('页均 %d 字 | 最短页 %s | 最长页 %s' % (
    sum(l for _, l in lens) // 484, sorted(lens, key=lambda x: x[1])[:3],
    sorted(lens, key=lambda x: -x[1])[:2]))
print('超短页(<120字, 可能空页/图版页):', short[:10])
print('超长页(>3500字):', long_[:5])
