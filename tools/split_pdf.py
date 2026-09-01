#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_pdf.py — 把 PDF 按页范围拆成 N 段（单文件并行解析实验用）
用法:
  python3 split_pdf.py 输入.pdf 输出目录 [份数=2]
产出: 输出目录/<原名>_part1ofN.pdf ...
依赖: pypdfium2（mineru venv 里有）
"""
import os, sys

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    src, out_dir = sys.argv[1], sys.argv[2]
    parts = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    import pypdfium2 as pdfium
    os.makedirs(out_dir, exist_ok=True)
    pdf = pdfium.PdfDocument(src)
    n = len(pdf)
    base = os.path.splitext(os.path.basename(src))[0]
    edges = [round(i * n / parts) for i in range(parts + 1)]
    for i in range(parts):
        lo, hi = edges[i], edges[i + 1]  # [lo, hi)
        dst = os.path.join(out_dir, f'{base}_part{i+1}of{parts}.pdf')
        out = pdfium.PdfDocument.new()
        out.removed_unused_resources = True
        for p in range(lo, hi):
            out.import_pages(pdf, [p])
        out.save(dst)
        print(f'✅ {dst}  (页 {lo+1}-{hi}, {hi-lo} 页)')
    print(f'共 {n} 页 → {parts} 段')

if __name__ == '__main__':
    main()
