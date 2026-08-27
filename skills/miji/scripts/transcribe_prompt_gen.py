"""Auto-generate a Whisper initial_prompt from video title/description via LLM.

This removes the need to manually know the video's domain terms before transcription.
Verified workflow: feed the LLM only the title + key description line; it emits one
line of likely-spoken terms to bias Whisper's decoding.

Usage:
    export LLM_API_BASE=http://localhost:3000/v1      # any OpenAI-compatible endpoint
    export LLM_API_KEY=sk-xxx
    python3 transcribe_prompt_gen.py "<video title>" "<key description sentence>"

Output: a single-line prompt, e.g.
    下面是关于MiniMax H3越狱模型的教程。MiniMax H3, 越狱模型, 开源, 无审查, ...
"""
import json
import os
import sys
import urllib.request

API = os.environ.get('LLM_API_BASE', 'http://127.0.0.1:3000/v1') + '/chat/completions'
KEY = os.environ.get('LLM_API_KEY', '')
MODEL = os.environ.get('LLM_MODEL', 'deepseek-v4-flash')

if not KEY:
    sys.exit('Set LLM_API_KEY first (any OpenAI-compatible endpoint).')

title = sys.argv[1] if len(sys.argv) > 1 else sys.exit('Usage: transcribe_prompt_gen.py "<title>" ["desc"]')
desc = sys.argv[2] if len(sys.argv) > 2 else ''

body = json.dumps({
    'model': MODEL,
    'messages': [
        {'role': 'system', 'content': (
            '你在为语音识别(Whisper)准备 initial_prompt。根据视频标题和简介，输出一行纯文本：'
            '以「下面是关于XX的教程/视频。」开头，后接最可能出现在口播中的关键词'
            '（品牌名/产品名/技术词，逗号分隔），总数8-15个。只输出这一行文本，不要解释。')},
        {'role': 'user', 'content': f'标题：{title}\n简介关键句：{desc}'},
    ],
    'temperature': 0.3,
}).encode()
req = urllib.request.Request(API, data=body, headers={
    'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=120) as r:
    resp = json.load(r)
print(resp['choices'][0]['message']['content'].strip().strip('"'))
