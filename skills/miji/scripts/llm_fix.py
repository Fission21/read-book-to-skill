"""LLM context-based correction for ASR transcripts (Chinese homophone & term errors).

Usage:
    export LLM_API_BASE=http://localhost:3000/v1     # OpenAI-compatible endpoint
    export LLM_API_KEY=sk-xxx
    python3 llm_fix.py <input.txt> <output.txt> ["video topic hint"]

Fixes typical ASR errors like 粤语模型→越狱模型, 迷你Magaz→MiniMax,
进向加速→镜像加速, while preserving timestamps and segmentation.
"""
import json
import os
import sys
import time
import urllib.request

API = os.environ.get('LLM_API_BASE', 'http://127.0.0.1:3000/v1') + '/chat/completions'
KEY = os.environ.get('LLM_API_KEY', '')
MODEL = os.environ.get('LLM_MODEL', 'deepseek-v4-flash')

if not KEY:
    sys.exit('Set LLM_API_KEY first.')

inp, outp = sys.argv[1], sys.argv[2]
hint = sys.argv[3] if len(sys.argv) > 3 else 'tech tutorial video'

text = open(inp, encoding='utf-8').read()

system = """你是 ASR 转写校对员。给你一段从中文科技教程视频转写的文本（带时间戳），它有大量同音字错误和术语错误。

任务：修正明显的同音字/识别错误，还原正确的专业术语和人名。规则：
1. 只改明显错误的词（如"粤语模型"→"越狱模型"、"迷你Magaz"→"MiniMax"、"进向加速"→"镜像加速"）
2. 保持时间戳和分段结构完全不变
3. 不确定的地方保持原样，不要发挥、不要补写内容
4. 口语语气词可保留，删掉无意义的重复
5. 直接输出修正后的全文，不要任何解释或前后缀"""

user = f"""视频主题提示：{hint}

常见正确术语参考：<按视频主题替换成正确的品牌名/产品名/技术词>

转写文本：
{text}"""

body = json.dumps({
    'model': MODEL,
    'messages': [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ],
    'temperature': 0.1,
}).encode()

req = urllib.request.Request(API, data=body, headers={
    'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'})
t0 = time.time()
with urllib.request.urlopen(req, timeout=600) as r:
    resp = json.load(r)
fixed = resp['choices'][0]['message']['content']
open(outp, 'w', encoding='utf-8').write(fixed)
print(f'{MODEL} 纠错完成 | 耗时 {time.time()-t0:.0f}s | 输出 {len(fixed)} 字')
