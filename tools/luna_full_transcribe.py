#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
luna_full_transcribe.py — 用 gpt-5.6-luna 并发转写整本 PDF（云端视觉识别全文实验）
用法: python3 luna_full_transcribe.py <输入.pdf> <输出目录> [--scale 2.5] [--workers 6]
产出: <输出目录>/pages/pNNN.jpg       # 渲染页
      <输出目录>/text/pNNN.md        # 每页转写
      <输出目录>/summary.json        # 每页耗时/字数/失败清单
"""
import os, sys, json, time, base64, argparse, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

PDF_URL = os.environ.get('VISION_BASE', 'http://127.0.0.1:3000').rstrip('/') + '/v1/responses'
MODEL = os.environ.get('VISION_MODEL', 'opencode-go/gpt-5.6-luna')
PROMPT = ('逐行完整转写这一页的全部文字（含页眉、页码、脚注和脚注分隔线），'
          '从页面第一行到最后一行，绝对不要省略或提前停止。输出纯 Markdown 正文。')


def get_key():
    env_key = os.environ.get('VISION_KEY')
    if env_key:
        return env_key
    env = os.path.expanduser('~/.hermes/.env')
    if os.path.isfile(env):
        for line in open(env, encoding='utf-8', errors='replace'):
            if line.startswith('CO1WBOY_API_KEY='):
                return line.strip().split('=', 1)[1]
    return os.environ.get('CO1WBOY_API_KEY', '')


def render_all(pdf_path, pages_dir, scale):
    os.makedirs(pages_dir, exist_ok=True)
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(pdf_path)
    n = len(pdf)
    for i in range(n):
        out = os.path.join(pages_dir, 'p%03d.jpg' % (i + 1))
        if os.path.isfile(out):
            continue
        pdf[i].render(scale=scale).to_pil().convert('RGB').save(out, 'JPEG', quality=85)
        if (i + 1) % 50 == 0:
            print('render %d/%d' % (i + 1, n), flush=True)
    return n


def call_luna(img_path, key, attempt_log):
    b64 = base64.b64encode(open(img_path, 'rb').read()).decode()
    payload = {
        'model': MODEL,
        'input': [{'type': 'message', 'role': 'user', 'content': [
            {'type': 'input_text', 'text': PROMPT},
            {'type': 'input_image', 'image_url': 'data:image/jpeg;base64,' + b64}]}],
        'max_output_tokens': 8000}
    last_err = None
    for attempt in range(1, 5):
        t0 = time.time()
        try:
            req = urllib.request.Request(PDF_URL, data=json.dumps(payload).encode(),
                                         headers={'Authorization': 'Bearer ' + key,
                                                  'Content-Type': 'application/json'})
            r = json.loads(urllib.request.urlopen(req, timeout=300).read())
            txt = ''.join(c.get('text', '') for item in r.get('output', [])
                          for c in item.get('content', []) if isinstance(c, dict))
            if txt.strip():
                return txt, time.time() - t0, None
            last_err = 'empty text (status=%s)' % r.get('status')
        except Exception as e:
            last_err = '%s: %s' % (type(e).__name__, str(e)[:120])
        attempt_log.append('retry%d %s' % (attempt, last_err))
        time.sleep(5 * attempt)
    return '', time.time() - t0, last_err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('outdir')
    ap.add_argument('--scale', type=float, default=2.5)
    ap.add_argument('--workers', type=int, default=6)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    text_dir = os.path.join(a.outdir, 'text')
    os.makedirs(text_dir, exist_ok=True)
    key = get_key()
    assert key, 'no CO1WBOY_API_KEY'

    t0 = time.time()
    n = render_all(a.pdf, os.path.join(a.outdir, 'pages'), a.scale)
    print('RENDER DONE %d pages in %.1fs' % (n, time.time() - t0), flush=True)

    results, fails = {}, {}
    t1 = time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {}
        for i in range(1, n + 1):
            out = os.path.join(text_dir, 'p%03d.md' % i)
            if os.path.isfile(out) and os.path.getsize(out) > 50:
                continue  # 断点续跑：已有结果跳过
            futs[ex.submit(call_luna, os.path.join(a.outdir, 'pages', 'p%03d.jpg' % i), key, [])] = i
        done = 0
        for f in as_completed(futs):
            i = futs[f]
            txt, dt, err = f.result()
            done += 1
            if txt:
                with open(os.path.join(text_dir, 'p%03d.md' % i), 'w', encoding='utf-8') as fp:
                    fp.write(txt)
                results[i] = {'secs': round(dt, 1), 'chars': len(txt)}
            else:
                fails[i] = err or 'unknown'
            if done % 10 == 0 or done == n:
                ok = len(results)
                print('progress %d/%d ok=%d fail=%d elapsed=%.0fs' %
                      (done, n, ok, len(fails), time.time() - t1), flush=True)

    total_chars = sum(r['chars'] for r in results.values())
    secs = [r['secs'] for r in results.values()]
    summary = {'pages': n, 'ok': len(results), 'failed': len(fails),
               'total_chars': total_chars,
               'wall_secs': round(time.time() - t1, 1),
               'mean_page_secs': round(sum(secs) / len(secs), 1) if secs else None,
               'fails': {str(k): v for k, v in sorted(fails.items())}}
    json.dump(summary, open(os.path.join(a.outdir, 'summary.json'), 'w'),
              ensure_ascii=False, indent=1)
    print('SUMMARY %s' % json.dumps({k: v for k, v in summary.items() if k != 'fails'},
                                    ensure_ascii=False), flush=True)
    if fails:
        print('FAILED PAGES: %s' % summary['fails'], flush=True)


if __name__ == '__main__':
    main()
