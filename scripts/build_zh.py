#!/usr/bin/env python3
"""Build the Chinese tool pages from the English ones.

    python3 scripts/build_zh.py && python3 scripts/seo_sync.py

/zh/<tool>/ is /<tool>/ with the same code and translated text. Every English string in a table below must
still be on the English page: if the English copy changes, the script stops and names the string to update,
so a Chinese page never silently falls behind. After building, the script lists any English text left on a
Chinese page. It also keeps the language links in step: hreflang and the 中文/EN switch on both versions,
and the Chinese navigation and footer on every Chinese page.

The Chinese converter (/zh/converter/) and home page (/zh/) are maintained by hand; only their navigation,
footer and tool links are updated here.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://audiotools.dev'
ZH_PAGES = ['converter', 'volume-booster', 'text-to-speech', 'audio-joiner', 'audio-compressor']   # tools with a Chinese page
BUILT = ['volume-booster', 'text-to-speech', 'audio-joiner', 'audio-compressor']                   # built by this script

ZH_HREF = lambda tool: f'/zh/{tool}/' if tool in ZH_PAGES else f'/{tool}/'


def zh_nav(current, en_href):
    items = [('converter', '转换器'), ('volume-booster', '音量增强'), ('text-to-speech', '文字转语音'), ('voice-to-text', '语音转文字')]
    links = [f'<a href="{ZH_HREF(t)}"{" aria-current=\"page\"" if t == current else ""}>{name}</a>' for t, name in items]
    links.append(f'<a href="/zh/"{" aria-current=\"page\"" if current == "home" else ""}>全部工具</a>')
    links.append(f'<a href="{en_href}" class="at-lang" hreflang="en" lang="en">EN</a>')
    return '<div class="at-nav-links">\n' + ''.join(f'                {l}\n' for l in links) + '            </div>'


def zh_footer(current):
    items = [('converter', '转换器'), ('voice-to-text', '语音转文字'), ('text-to-speech', '文字转语音'), ('audio-trimmer', '剪辑'),
             ('audio-speed-changer', '变速'), ('volume-booster', '音量增强'), ('audio-joiner', '合并'), ('audio-compressor', '压缩')]
    tools = ''.join(f'<a href="{ZH_HREF(t)}"{" aria-current=\"page\"" if t == current else ""}>{name}</a>' for t, name in items)
    return f'''<footer class="at-footer">
        <div class="at-footer-inner">
            <nav class="at-footer-tools" aria-label="全部工具">{tools}</nav>
            <p><a href="/zh/">AudioTools.dev</a> — 在浏览器中运行的免费开源音频工具。由 <a href="https://github.com/formeo" rel="noopener">Roman Gordienko</a> 开发。</p>
            <p class="at-footer-meta"><a href="/about/">关于</a><a href="/changelog/">更新日志</a><a href="/privacy/">隐私政策</a><a href="/terms/">使用条款</a><a href="https://github.com/formeo" rel="noopener">GitHub</a><a href="https://www.devtoolkit.site/" rel="noopener">DevToolKit.site</a></p>
            <p><a class="at-support" href="https://boosty.to/formeo" rel="noopener">在 Boosty 上支持本项目</a></p>
        </div>
    </footer>'''


def alternates(tool):
    return (f'    <link rel="alternate" hreflang="en" href="{SITE}/{tool}/">\n'
            f'    <link rel="alternate" hreflang="zh" href="{SITE}/zh/{tool}/">\n'
            f'    <link rel="alternate" hreflang="x-default" href="{SITE}/{tool}/">\n')


ALT_RE = re.compile(r'    <link rel="alternate" hreflang="[^"]+" href="[^"]+">\n')
NAV_RE = re.compile(r'<div class="at-nav-links">.*?</div>', re.S)
FOOTER_RE = re.compile(r'<footer class="at-footer">.*?</footer>', re.S)
TOOL_HREF_RE = re.compile(r'href="/(' + '|'.join(ZH_PAGES) + r')/"')


def english_page(tool):
    """Add hreflang and the 中文 switch to the English page (idempotent); return its HTML."""
    path = ROOT / tool / 'index.html'
    s = path.read_text(encoding='utf-8')
    s = ALT_RE.sub('', s)
    s = re.sub(r'(<link rel="canonical" href="[^"]+">\n)', lambda m: m.group(1) + alternates(tool), s, count=1)
    s = re.sub(r'\s*<a href="/zh/[^"]*" class="at-lang"[^>]*>中文</a>', '', s)
    s = NAV_RE.sub(lambda m: m.group(0)[:-len('</div>')].rstrip() + f'\n                <a href="/zh/{tool}/" class="at-lang" hreflang="zh" lang="zh">中文</a>\n            </div>', s, count=1)
    path.write_text(s, encoding='utf-8')
    return s


def build(tool, table):
    s = english_page(tool)
    missing = [en for en, _ in table if en not in s]
    if missing:
        sys.exit(f'{tool}: the English page no longer contains:\n  ' + '\n  '.join(missing))
    table = table + [(en, zh) for en, zh in COMMON if en in s]   # shared strings, where the page has them
    for en, zh in sorted(table, key=lambda p: -len(p[0])):   # longer strings first, so parts don't break them
        s = s.replace(en, zh)
    s = s.replace('<html lang="en">', '<html lang="zh-CN">', 1)
    s = s.replace('aria-label="Main"', 'aria-label="主导航"', 1)
    s = s.replace('<meta property="og:locale" content="en_US">', '<meta property="og:locale" content="zh_CN">')
    s = s.replace(f'{SITE}/og/{tool}.png', f'{SITE}/og/zh-{tool}.png')
    s = ALT_RE.sub('', s)
    s = s.replace(f'{SITE}/{tool}/', f'{SITE}/zh/{tool}/')               # canonical, og:url, JSON-LD url
    s = re.sub(r'(<link rel="canonical" href="[^"]+">\n)', lambda m: m.group(1) + alternates(tool), s, count=1)
    s = re.sub(r'("@type":\s*"WebApplication",)(\s*)', lambda m: m.group(1) + m.group(2) + '"inLanguage": "zh-CN",' + (m.group(2) or ''), s, count=1)
    s = TOOL_HREF_RE.sub(lambda m: f'href="/zh/{m.group(1)}/"', s)       # links to tools that have a Chinese page
    s = s.replace('href="/"', 'href="/zh/"')
    s = NAV_RE.sub(lambda m: zh_nav(tool, f'/{tool}/'), s, count=1)
    s = FOOTER_RE.sub(lambda m: zh_footer(tool), s, count=1)
    out = ROOT / 'zh' / tool / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(s, encoding='utf-8')
    leftovers(out, s)


ALLOWED = {'AudioTools.dev', 'AudioTools', 'GitHub', 'DevToolKit.site', 'Boosty', 'Roman Gordienko', 'MP3', 'WAV', 'FLAC', 'OGG',
           'M4A', 'AAC', 'WebM', 'ZIP', 'Web Audio API', 'Web Speech Synthesis API', 'Speech Synthesis API', 'dBFS', 'kbps', 'TTS', 'EN', 'Google', 'Chrome', 'Safari', 'Edge', 'Windows', 'macOS', 'Android', 'LAME', 'WebAssembly', 'PCM'}


def leftovers(path, s):
    """English words left in visible text, attributes and UI strings of a Chinese page."""
    body = re.sub(r'<svg.*?</svg>', '', s[s.index('<body'):], flags=re.S)
    code = ''.join(re.findall(r'<script>(.*?)</script>', body, re.S))
    text = re.sub(r'<[^>]+>', '\n', re.sub(r'<script.*?</script>', '', body, flags=re.S))
    text += '\n'.join(re.findall(r'(?:title|placeholder|aria-label|alt)="([^"]*)"', body))
    strings = [t for t in re.findall(r"'([^'\n]*)'", code) if re.search(r'[A-Za-z]{3}', t) and ' ' in t.strip() and not re.search(r'[<>={}()#]', t)]
    words = set()
    for chunk in list(text.split('\n')) + strings:
        for w in re.findall(r'[A-Za-z][A-Za-z\-’\']{3,}', chunk):
            if not any(w in a for a in ALLOWED):
                words.add(w)
    print(f'{path.relative_to(ROOT)}: built' + (f'; English left: {" ".join(sorted(words))}' if words else ''))


def update_hand_made(path, current, en_href):
    """Chinese navigation, footer and tool links on the hand-maintained Chinese pages."""
    s = path.read_text(encoding='utf-8')
    body_start = s.index('<body')
    head, body = s[:body_start], s[body_start:]
    body = TOOL_HREF_RE.sub(lambda m: f'href="/zh/{m.group(1)}/"', body)
    body = NAV_RE.sub(lambda m: zh_nav(current, en_href), body, count=1)
    body = FOOTER_RE.sub(lambda m: zh_footer(current), body, count=1)
    path.write_text(head + body, encoding='utf-8')


# ------------------------------------------------------------------ translations
COMMON = [
    ('<p><strong>Drop audio file here</strong> or click to browse</p>', '<p><strong>将音频文件拖放到此处</strong>，或点击选择</p>'),
    ('<p>MP3, WAV, FLAC, OGG, M4A — processed locally, never uploaded</p>', '<p>MP3、WAV、FLAC、OGG、M4A — 在本地处理，绝不上传</p>'),
    ('title="Remove"', 'title="移除"'),
    ('>Reset</button>', '>重置</button>'),
    ('<label class="out-format">Format <select', '<label class="out-format">格式 <select'),
    ('>MP3 · 192 kbps</option>', '>MP3 · 192 kbps</option>'),
    ('>WAV · lossless</option>', '>WAV · 无损</option>'),
    ('<div class="feature-title">100% Private</div>', '<div class="feature-title">100% 私密</div>'),
    ('<h2>Frequently Asked Questions</h2>', '<h2>常见问题</h2>'),
    ('<h3>How It Works</h3>', '<h3>工作原理</h3>'),
    ('<h3>Common Use Cases</h3>', '<h3>常见用途</h3>'),
    ("alert('Could not decode this audio file. Try a different format (MP3, WAV, FLAC, OGG, M4A).');", "alert('无法解码此音频文件，请换一种格式（MP3、WAV、FLAC、OGG、M4A）。');"),
]

TABLES = {
'volume-booster': [
    ('<title>Volume Booster — Increase Audio Volume Free | AudioTools.dev</title>', '<title>音量增强器 — 免费在线提高音频音量 | AudioTools.dev</title>'),
    ('Boost audio volume online for free. Increase or normalize MP3, WAV volume in your browser. No upload, no sign-up required.',
     '免费在线提高音频音量：在浏览器中放大或标准化 MP3、WAV 的音量。无需上传，无需注册。'),
    ('volume booster online, increase audio volume, boost mp3 volume, audio normalizer, audio volume increase, loud audio online, normalize audio free',
     '音量增强, 提高音频音量, MP3音量放大, 音频标准化, 声音太小, 在线放大音量, 免费音量增强器'),
    ('Volume Booster — Increase Audio Volume Free | AudioTools', '音量增强器 — 免费在线提高音频音量 | AudioTools'),
    ('"name":"Volume Booster — AudioTools.dev"', '"name":"音量增强器 — AudioTools.dev"'),
    ('<h1>Volume Booster</h1>', '<h1>音量增强器</h1>'),
    ('<p>Increase, decrease, or normalize audio volume — with a visual level meter, no upload</p>', '<p>提高、降低或标准化音频音量——带可视化电平表，无需上传</p>'),
    ('data-mode="normalize">Normalize<small>auto to −1 dBFS, no clipping</small>', 'data-mode="normalize">标准化<small>自动调到 −1 dBFS，不削波</small>'),
    ('data-mode="boost">Manual Boost<small>0–500% with limiter</small>', 'data-mode="boost">手动放大<small>0–500%，带限幅器</small>'),
    ('Normalize scales the file so its loudest peak reaches <b>−1 dBFS</b> — maximum loudness with zero distortion.', '标准化会缩放整个文件，使最响的峰值达到 <b>−1 dBFS</b>——响度最大且零失真。'),
    ('<span class="meter-label">Before</span>', '<span class="meter-label">处理前</span>'),
    ('<span class="meter-label">After</span>', '<span class="meter-label">处理后</span>'),
    ('Peaks limited to prevent clipping', '已限制峰值以防止削波'),
    ('>Apply &amp; Process</button>', '>应用并处理</button>'),
    ("'Apply & Process'", "'应用并处理'"),
    ("'Processing…'", "'处理中…'"),
    ("'Normalized (' + ", "'已标准化（' + "),
    (" + ' dB)';", " + ' dB）';"),
    ("'% boost'", "'% 放大'"),
    ("'  ·  peak '", "'  ·  峰值 '"),
    ('<p class="result-title">Result — <span', '<p class="result-title">结果 — <span'),
    ('id="downloadBtn" style="width:100%;">Download</button>', 'id="downloadBtn" style="width:100%;">下载</button>'),
    ('<div class="feature-title">Boost up to 500%</div><div class="feature-desc">Increase volume by up to 5x with a simple slider.</div>',
     '<div class="feature-title">最高放大 500%</div><div class="feature-desc">拖动滑块即可把音量提高到 5 倍。</div>'),
    ('<div class="feature-title">Normalize Audio</div><div class="feature-desc">Auto-detect peak and normalize to −1 dBFS, no clipping.</div>',
     '<div class="feature-title">音频标准化</div><div class="feature-desc">自动检测峰值并标准化到 −1 dBFS，不削波。</div>'),
    ('<div class="feature-title">Visual Level Meter</div><div class="feature-desc">See the waveform and peak levels before and after.</div>',
     '<div class="feature-title">可视化电平表</div><div class="feature-desc">查看处理前后的波形和峰值电平。</div>'),
    ('<div class="feature-desc">All processing in your browser. Files never leave your device.</div>', '<div class="feature-desc">所有处理都在浏览器中完成，文件不会离开您的设备。</div>'),
    ('<h2>Free Online Volume Booster &amp; Audio Normalizer</h2>', '<h2>免费在线音量增强与音频标准化</h2>'),
    ('<p>Volume Booster lets you increase the volume of quiet audio files or normalize audio to a consistent level. Drop a quiet recording, boost the volume or normalize it, and download the result — all in your browser without any server.</p>',
     '<p>音量增强器可以提高小声音频文件的音量，或把音频标准化到统一的电平。拖入一段小声的录音，放大或标准化后下载结果——全部在浏览器中完成，不经过任何服务器。</p>'),
    ('<h3>Volume Boost vs Normalization</h3>', '<h3>音量放大与标准化的区别</h3>'),
    ('<p>Volume boost increases the entire signal by a fixed amount (for example +6 dB or 200%). Normalization analyzes the peak level and scales the volume so the loudest part reaches a target level (−1 dBFS here). Normalization is smarter — it prevents clipping while maximizing perceived loudness. When you boost manually past the ceiling, a soft limiter rounds off the peaks so the result stays clean instead of crackling.</p>',
     '<p>音量放大会把整个信号按固定幅度提高（例如 +6 dB 或 200%）。标准化则会分析峰值电平，并缩放音量，使最响的部分达到目标电平（这里是 −1 dBFS）。标准化更聪明：在尽量提高响度的同时避免削波。手动放大超过上限时，软限幅器会把峰值圆滑处理，结果依然干净，不会爆音。</p>'),
    ('<p>Drop or select your file, pick Normalize or Manual Boost, and click "Apply &amp; Process". The audio is decoded with the Web Audio API, gain is applied sample-by-sample directly in your browser, and the result is offered for download as MP3 or WAV. Nothing is uploaded.</p>',
     '<p>拖放或选择文件，选择“标准化”或“手动放大”，然后点击“应用并处理”。音频由 Web Audio API 解码，增益在浏览器中逐个采样地应用，结果可下载为 MP3 或 WAV。不上传任何内容。</p>'),
    ('<p>Boosting quiet voice recordings from phone or laptop microphones. Normalizing podcast episodes to a consistent volume. Matching volume levels across multiple tracks. Making quiet audiobook chapters louder.</p>',
     '<p>放大手机或笔记本麦克风录下的小声语音；把各期播客标准化到统一音量；让多条音轨的音量保持一致；让声音太小的有声书章节更响亮。</p>'),
    ('<p>Need other edits? Try our <a href="/audio-trimmer/">Audio Trimmer</a>, <a href="/audio-speed-changer/">Speed Changer</a>, <a href="/converter/">Audio Converter</a>, or <a href="/text-to-speech/">Text to Speech</a>.</p>',
     '<p>还需要其他处理？试试<a href="/audio-trimmer/">音频剪辑</a>、<a href="/audio-speed-changer/">音频变速</a>、<a href="/converter/">音频转换器</a>或<a href="/text-to-speech/">文字转语音</a>。</p>'),
    ('<div class="faq-q">How much can I boost audio volume?</div><div class="faq-a">Up to 500% (5x). For best results use Normalize, which finds the optimal level without clipping.</div>',
     '<div class="faq-q">音量最多能放大多少？</div><div class="faq-a">最高 500%（5 倍）。想要最佳效果，请使用“标准化”，它会找到不削波的最佳电平。</div>'),
    ('<div class="faq-q">What is audio normalization?</div><div class="faq-a">It analyzes the peak volume and scales the file so the loudest part reaches a target level (−1 dBFS), maximizing loudness without distortion.</div>',
     '<div class="faq-q">什么是音频标准化？</div><div class="faq-a">它会分析峰值音量并缩放整个文件，使最响的部分达到目标电平（−1 dBFS），在不失真的前提下让响度最大。</div>'),
    ('<div class="faq-q">Is my audio uploaded?</div><div class="faq-a">No. Everything happens in your browser using the Web Audio API.</div>',
     '<div class="faq-q">我的音频会被上传吗？</div><div class="faq-a">不会。所有处理都通过 Web Audio API 在您的浏览器中完成。</div>'),
],
'audio-joiner': [
    ('<title>Audio Joiner — Merge MP3, WAV Files Free | AudioTools.dev</title>', '<title>音频合并 — 免费在线合并 MP3、WAV 文件 | AudioTools.dev</title>'),
    ('Free online audio joiner. Merge and combine MP3, WAV, FLAC files in your browser. No upload, no sign-up. Add crossfade between tracks.',
     '免费在线音频合并工具：在浏览器中合并、拼接 MP3、WAV、FLAC 文件。无需上传，无需注册，可在音轨之间添加淡入淡出。'),
    ('Free online audio joiner. Merge and combine MP3, WAV, FLAC files in your browser. No upload, add crossfade between tracks.',
     '免费在线音频合并工具：在浏览器中合并 MP3、WAV、FLAC 文件。无需上传，可添加淡入淡出。'),
    ('audio joiner, merge audio online, combine mp3, join audio files, audio merger, concatenate audio, merge wav files free',
     '音频合并, 在线合并音频, MP3合并, 拼接音频文件, 音频拼接, 合并WAV, 免费音频合并'),
    ('Audio Joiner — Merge MP3, WAV Files Free | AudioTools', '音频合并 — 免费在线合并 MP3、WAV 文件 | AudioTools'),
    ('"name":"Audio Joiner — AudioTools.dev"', '"name":"音频合并 — AudioTools.dev"'),
    ('<h1>Audio Joiner</h1>', '<h1>音频合并</h1>'),
    ('<p>Merge and combine multiple audio files into one — reorder tracks, add crossfade, no upload</p>', '<p>把多个音频文件合并为一个——可调整顺序、添加淡入淡出，无需上传</p>'),
    ('<p><strong>Drop audio files here</strong> or click to browse</p>', '<p><strong>将音频文件拖放到此处</strong>，或点击选择</p>'),
    ('<p>Add several files — MP3, WAV, FLAC, OGG, M4A. Processed locally, never uploaded.</p>', '<p>可添加多个文件——MP3、WAV、FLAC、OGG、M4A。在本地处理，绝不上传。</p>'),
    ('>＋ Add more files</button>', '>＋ 添加更多文件</button>'),
    ('<label>Crossfade:</label>', '<label>淡入淡出：</label>'),
    ('<div class="total-line">Tracks: <b id="trackCount">0</b> · Total length: <b id="totalDur">0:00</b></div>', '<div class="total-line">音轨：<b id="trackCount">0</b> · 总时长：<b id="totalDur">0:00</b></div>'),
    ('>Merge &amp; Download</button>', '>合并并下载</button>'),
    ('>Clear</button>', '>清空</button>'),
    ('<div class="progress-text" id="progressText">Merging…</div>', '<div class="progress-text" id="progressText">合并中…</div>'),
    ("progressText.textContent='Merging…';", "progressText.textContent='合并中…';"),
    ("progressText.textContent='Encoding…';", "progressText.textContent='编码中…';"),
    ('<p class="result-title">Merged — <span', '<p class="result-title">合并完成 — <span'),
    ('id="downloadBtn" style="width:100%;">Download</button>', 'id="downloadBtn" style="width:100%;">下载</button>'),
    ("alert('Could not decode \"' + file.name + '\". Skipping. Try MP3, WAV, FLAC, OGG or M4A.');", "alert('无法解码“' + file.name + '”，已跳过。请使用 MP3、WAV、FLAC、OGG 或 M4A。');"),
    ('title="Move up"', 'title="上移"'),
    ('title="Move down"', 'title="下移"'),
    ("resultInfo.textContent = tracks.length + ' tracks · '", "resultInfo.textContent = tracks.length + ' 条音轨 · '"),
    ('<div class="feature-title">Multiple Files</div><div class="feature-desc">Add any number of audio files and reorder them freely.</div>',
     '<div class="feature-title">多个文件</div><div class="feature-desc">可添加任意数量的音频文件，并自由调整顺序。</div>'),
    ('<div class="feature-title">Crossfade Transitions</div><div class="feature-desc">Add a smooth crossfade between tracks for seamless joins.</div>',
     '<div class="feature-title">淡入淡出过渡</div><div class="feature-desc">在音轨之间添加平滑的淡入淡出，衔接自然。</div>'),
    ('<div class="feature-title">Mix Formats</div><div class="feature-desc">Combine MP3, WAV, FLAC, OGG in any combination.</div>',
     '<div class="feature-title">混合格式</div><div class="feature-desc">MP3、WAV、FLAC、OGG 可任意组合。</div>'),
    ('<div class="feature-desc">All merging in your browser. Files never leave your device.</div>', '<div class="feature-desc">所有合并都在浏览器中完成，文件不会离开您的设备。</div>'),
    ('<h2>Free Online Audio Joiner &amp; Merger</h2>', '<h2>免费在线音频合并与拼接</h2>'),
    ('<p>Audio Joiner combines multiple audio files into a single track directly in your browser. Whether you need to merge podcast segments, combine music tracks, or join voice recordings, this tool handles it without uploading your files to any server.</p>',
     '<p>音频合并工具直接在浏览器中把多个音频文件合成一条音轨。无论是合并播客片段、拼接音乐，还是连接语音录音，都不需要把文件上传到任何服务器。</p>'),
    ('<p>The tool uses the Web Audio API to decode each file into raw PCM, concatenates the buffers in the order you set, applies an optional crossfade between consecutive tracks, and encodes the result as MP3 or WAV. All processing happens in your browser — no server involved.</p>',
     '<p>工具使用 Web Audio API 把每个文件解码为原始 PCM，按您设定的顺序拼接，可选在相邻音轨之间添加淡入淡出，再编码为 MP3 或 WAV。所有处理都在浏览器中完成，不涉及服务器。</p>'),
    ('<h3>Reorder and Crossfade</h3>', '<h3>调整顺序与淡入淡出</h3>'),
    ('<p>Drag tracks to reorder them, or use the up/down arrows. Set a crossfade of up to 3 seconds to smoothly blend the end of one track into the start of the next — useful for music mixes and seamless podcast edits. Set crossfade to 0 for a clean back-to-back join.</p>',
     '<p>拖动音轨即可调整顺序，也可以使用上下箭头。淡入淡出最长可设为 3 秒，让上一条音轨的结尾平滑过渡到下一条的开头，适合音乐串烧和无缝的播客剪辑。设为 0 则直接首尾相接。</p>'),
    ('<p>Merging podcast intro, segments, and outro. Combining multiple music tracks into one mix. Joining split voice recordings or audiobook chapters. Assembling sound effects into a single file.</p>',
     '<p>合并播客的片头、正片和片尾；把多首音乐拼成一个串烧；连接分段的语音录音或有声书章节；把多个音效合成一个文件。</p>'),
    ('<p>Need other edits? Try our <a href="/audio-trimmer/">Audio Trimmer</a>, <a href="/audio-speed-changer/">Speed Changer</a>, <a href="/volume-booster/">Volume Booster</a>, or <a href="/converter/">Audio Converter</a>.</p>',
     '<p>还需要其他处理？试试<a href="/audio-trimmer/">音频剪辑</a>、<a href="/audio-speed-changer/">音频变速</a>、<a href="/volume-booster/">音量增强器</a>或<a href="/converter/">音频转换器</a>。</p>'),
    ('<div class="faq-q">How do I merge audio files online?</div><div class="faq-a">Add your files, arrange them in order, optionally add crossfade, then click Merge &amp; Download to get a single combined file.</div>',
     '<div class="faq-q">如何在线合并音频文件？</div><div class="faq-a">添加文件，排好顺序，可选添加淡入淡出，然后点击“合并并下载”，即可得到一个合并后的文件。</div>'),
    ('<div class="faq-q">Can I merge different formats?</div><div class="faq-a">Yes. Mix MP3, WAV, FLAC, OGG. The browser decodes each file and the merged result is saved as MP3 or WAV.</div>',
     '<div class="faq-q">可以合并不同格式的文件吗？</div><div class="faq-a">可以。MP3、WAV、FLAC、OGG 可混合使用。浏览器会分别解码每个文件，合并结果保存为 MP3 或 WAV。</div>'),
    ('<div class="faq-q">Is my audio uploaded?</div><div class="faq-a">No. All merging happens in your browser using the Web Audio API.</div>',
     '<div class="faq-q">我的音频会被上传吗？</div><div class="faq-a">不会。所有合并都通过 Web Audio API 在您的浏览器中完成。</div>'),
],
'audio-compressor': [
    ('<title>Audio Compressor — Reduce File Size Free | AudioTools.dev</title>', '<title>音频压缩 — 免费在线减小音频文件大小 | AudioTools.dev</title>'),
    ('Compress audio files online for free. Reduce MP3, WAV file size by adjusting bitrate and sample rate. No upload, runs in your browser.',
     '免费在线压缩音频：调整码率和采样率，减小 MP3、WAV 文件体积。无需上传，在浏览器中运行。'),
    ('audio compressor, reduce audio file size, compress mp3 online, shrink audio file, audio bitrate reducer, compress wav free',
     '音频压缩, 减小音频文件大小, 在线压缩MP3, 音频变小, 降低码率, 压缩WAV, 免费音频压缩'),
    ('Audio Compressor — Reduce File Size Free | AudioTools', '音频压缩 — 免费在线减小音频文件大小 | AudioTools'),
    ('"name":"Audio Compressor — AudioTools.dev"', '"name":"音频压缩 — AudioTools.dev"'),
    ('<h1>Audio Compressor</h1>', '<h1>音频压缩</h1>'),
    ('<p>Reduce audio file size by adjusting bitrate and sample rate — output as MP3, no upload</p>', '<p>通过调整码率和采样率减小音频文件体积——输出 MP3，无需上传</p>'),
    ('<p><strong>Drop audio files here</strong>, one or several, or click to browse</p>', '<p><strong>将一个或多个音频文件拖放到此处</strong>，或点击选择</p>'),
    ('<label class="ctrl-label">Bitrate — lower means smaller file</label>', '<label class="ctrl-label">码率——越低文件越小</label>'),
    ('>64 kbps — voice / podcast (smallest)</option>', '>64 kbps — 语音 / 播客（最小）</option>'),
    ('>128 kbps — general purpose (recommended)</option>', '>128 kbps — 通用（推荐）</option>'),
    ('>192 kbps — high quality music</option>', '>192 kbps — 高品质音乐</option>'),
    ('>256 kbps — very high quality</option>', '>256 kbps — 极高品质</option>'),
    ('>320 kbps — maximum quality</option>', '>320 kbps — 最高品质</option>'),
    ('<label class="ctrl-label">Sample rate</label>', '<label class="ctrl-label">采样率</label>'),
    ('>Keep original</option>', '>保持原样</option>'),
    ('>44100 Hz — CD quality</option>', '>44100 Hz — CD 音质</option>'),
    ('>22050 Hz — smaller, fine for voice</option>', '>22050 Hz — 更小，适合语音</option>'),
    ('>16000 Hz — smallest, speech only</option>', '>16000 Hz — 最小，仅限语音</option>'),
    ('<div class="lbl">Original</div>', '<div class="lbl">原始</div>'),
    ('<div class="lbl">Estimated</div>', '<div class="lbl">预计</div>'),
    ('>Compress &amp; Download</button>', '>压缩并下载</button>'),
    ('<div class="progress-text" id="progressText">Compressing…</div>', '<div class="progress-text" id="progressText">压缩中…</div>'),
    ("progressText.textContent = 'Encoding MP3…';", "progressText.textContent = '正在编码 MP3…';"),
    ("progressText.textContent = 'Preparing…';", "progressText.textContent = '准备中…';"),
    ('<p class="result-title">Compressed — <span', '<p class="result-title">压缩完成 — <span'),
    ('id="downloadBtn" style="width:100%;">Download MP3</button>', 'id="downloadBtn" style="width:100%;">下载 MP3</button>'),
    ("'% (larger)'", "'%（变大）'"),
    ("'% vs original'", "'%（相比原文件）'"),
    ("alert(err.message || 'Compression failed. Please try again.');", "alert(err.message || '压缩失败，请重试。');"),
    ("const B = { files: (n) => n + ' files', compress: (n) => 'Compress ' + n + ' files', zip: 'Download all (ZIP)',\n            done: (ok, n) => (ok === n ? n + ' files' : ok + ' of ' + n + ' files') };",
     "const B = { files: (n) => n + ' 个文件', compress: (n) => '压缩 ' + n + ' 个文件', zip: '全部下载（ZIP）',\n            done: (ok, n) => (ok === n ? n + ' 个文件' : n + ' 个中的 ' + ok + ' 个') };"),
    ('<div class="feature-title">Bitrate Control</div><div class="feature-desc">Choose from 64 to 320 kbps for the right size vs quality.</div>',
     '<div class="feature-title">码率控制</div><div class="feature-desc">在 64 到 320 kbps 之间选择，平衡体积与音质。</div>'),
    ('<div class="feature-title">Sample Rate Options</div><div class="feature-desc">Downsample to 22 kHz or 16 kHz for even smaller files.</div>',
     '<div class="feature-title">采样率选项</div><div class="feature-desc">降到 22 kHz 或 16 kHz，文件更小。</div>'),
    ('<div class="feature-title">Size Preview</div><div class="feature-desc">See the estimated output size before you compress.</div>',
     '<div class="feature-title">大小预览</div><div class="feature-desc">压缩前即可看到预计的输出大小。</div>'),
    ('<div class="feature-desc">All compression in your browser. Files never leave your device.</div>', '<div class="feature-desc">所有压缩都在浏览器中完成，文件不会离开您的设备。</div>'),
    ('<h2>Free Online Audio Compressor</h2>', '<h2>免费在线音频压缩</h2>'),
    ('<p>Audio Compressor reduces the file size of your audio by re-encoding it to MP3 at a bitrate and sample rate you choose. Perfect for fitting audio into email attachments, messaging apps, or storage limits.</p>',
     '<p>音频压缩工具按您选择的码率和采样率把音频重新编码为 MP3，从而减小文件体积。非常适合发送邮件附件、通过聊天软件分享，或节省存储空间。</p>'),
    ('<p>Lossy MP3 compression removes inaudible data to shrink the file. A 44 MB WAV can become a 4 MB MP3 at 128 kbps — roughly a 10x reduction with minimal quality loss for most uses. Higher bitrates (256–320 kbps) preserve more detail for music. Everything runs in your browser, with the LAME MP3 encoder compiled to WebAssembly — nothing is uploaded.</p>',
     '<p>有损 MP3 压缩会去掉人耳听不到的数据来缩小文件。一个 44 MB 的 WAV 以 128 kbps 编码后约为 4 MB，体积缩小约 10 倍，对大多数用途来说音质损失很小。更高的码率（256–320 kbps）能为音乐保留更多细节。一切都在浏览器中运行，使用编译为 WebAssembly 的 LAME MP3 编码器，不上传任何内容。</p>'),
    ('<h3>Choosing the Right Bitrate</h3>', '<h3>如何选择码率</h3>'),
    ('<p>64 kbps — voice recordings and podcasts (smallest files). 128 kbps — general purpose, good quality for most uses. 192 kbps — high quality for music. 320 kbps — maximum quality, indistinguishable from uncompressed for most listeners. Lowering the sample rate to 22 kHz or 16 kHz shrinks speech files further.</p>',
     '<p>64 kbps：语音录音和播客（文件最小）。128 kbps：通用，适合大多数用途。192 kbps：高品质音乐。320 kbps：最高品质，大多数听众分辨不出与无损的区别。把采样率降到 22 kHz 或 16 kHz，可以让语音文件更小。</p>'),
    ('<p>Need other edits? Try our <a href="/converter/">Audio Converter</a>, <a href="/audio-trimmer/">Audio Trimmer</a>, <a href="/audio-joiner/">Audio Joiner</a>, or <a href="/volume-booster/">Volume Booster</a>.</p>',
     '<p>还需要其他处理？试试<a href="/converter/">音频转换器</a>、<a href="/audio-trimmer/">音频剪辑</a>、<a href="/audio-joiner/">音频合并</a>或<a href="/volume-booster/">音量增强器</a>。</p>'),
    ('<div class="faq-q">How much can I reduce file size?</div><div class="faq-a">Depending on the source, you can reduce WAV files by 5–20x by converting to MP3. A 50 MB WAV becomes ~5 MB at 128 kbps.</div>',
     '<div class="faq-q">文件能缩小多少？</div><div class="faq-a">视原文件而定，WAV 转为 MP3 后通常可缩小 5–20 倍。一个 50 MB 的 WAV 以 128 kbps 编码约为 5 MB。</div>'),
    ('<div class="faq-q">Does compression affect quality?</div><div class="faq-a">Lossy compression removes some data. At 192 kbps or higher, most listeners cannot tell the difference from the original.</div>',
     '<div class="faq-q">压缩会影响音质吗？</div><div class="faq-a">有损压缩会去掉一部分数据。在 192 kbps 及以上，大多数听众听不出与原文件的区别。</div>'),
    ('<div class="faq-q">Can I compress several files at once?</div><div class="faq-a">Yes. Drop several files: all of them are compressed with the same settings, and you can download each one or all of them as a ZIP.</div>',
     '<div class="faq-q">可以一次压缩多个文件吗？</div><div class="faq-a">可以。拖入多个文件，它们会使用相同的设置压缩，可以单独下载，也可以打包成 ZIP 一次下载。</div>'),
    ('<div class="faq-q">Is my audio uploaded?</div><div class="faq-a">No. All compression happens in your browser using the Web Audio API.</div>',
     '<div class="faq-q">我的音频会被上传吗？</div><div class="faq-a">不会。所有压缩都在您的浏览器中完成。</div>'),
],
'text-to-speech': [
    ('<title>Text to Speech — Free Online TTS | AudioTools.dev</title>', '<title>文字转语音 — 免费在线 TTS 朗读 | AudioTools.dev</title>'),
    ('Free text-to-speech online. Convert text to natural speech in 50+ languages. No sign-up, no limits. Works in your browser with Web Speech API.',
     '免费在线文字转语音：用 50 多种语言把文字朗读出来。无需注册，没有限制，通过 Web Speech API 在浏览器中运行。'),
    ('text to speech online, tts free, text to speech converter, read text aloud, text to audio, free tts, browser text to speech, speech synthesis',
     '文字转语音, 在线TTS, 免费文字转语音, 朗读文字, 文本转语音, 语音合成, 在线朗读, 浏览器文字转语音'),
    ('Text to Speech — Free Online TTS Converter', '文字转语音 — 免费在线 TTS'),
    ('Convert text to natural speech in 50+ languages. Free, no sign-up, runs in your browser.', '用 50 多种语言把文字转为自然的语音。免费，无需注册，在浏览器中运行。'),
    ('"name": "Text to Speech — AudioTools.dev"', '"name": "文字转语音 — AudioTools.dev"'),
    ('"description": "Free online text-to-speech tool supporting 50+ languages. Uses the browser\'s Speech Synthesis API; AudioTools.dev has no server."',
     '"description": "支持 50 多种语言的免费在线文字转语音工具。使用浏览器的 Speech Synthesis API；AudioTools.dev 没有服务器。"'),
    ('<h1>Text to Speech</h1>', '<h1>文字转语音</h1>'),
    ('<p>Convert text to natural speech in 50+ languages — free, no sign-up, runs in your browser</p>', '<p>用 50 多种语言把文字转为自然的语音——免费，无需注册，在浏览器中运行</p>'),
    ('placeholder="Type or paste your text here..."', 'placeholder="在此输入或粘贴文字…"'),
    ('maxlength="10000">AudioTools is a free, open-source collection of audio processing tools that run entirely in your browser. No uploads, no accounts, complete privacy.</textarea>',
     'maxlength="10000">AudioTools 是一套完全在浏览器中运行的免费开源音频工具。无需上传，无需账号，完全私密。</textarea>'),
    ('</span> / 10,000 characters</div>', '</span> / 10,000 字符</div>'),
    ('<label>Voice</label>', '<label>声音</label>'),
    ('<option>Loading voices...</option>', '<option>正在加载声音…</option>'),
    ('<label>Language</label>', '<label>语言</label>'),
    ('<option value="">All Languages</option>', '<option value="">全部语言</option>'),
    ('<label>Speed</label>', '<label>语速</label>'),
    ('<label>Pitch</label>', '<label>音调</label>'),
    ('<label>Volume</label>', '<label>音量</label>'),
    ('onclick="speak()">Speak</button>', 'onclick="speak()">朗读</button>'),
    ('style="display:none;">Pause</button>', 'style="display:none;">暂停</button>'),
    ('style="display:none;">Stop</button>', 'style="display:none;">停止</button>'),
    ("pauseBtn.textContent = 'Pause';", "pauseBtn.textContent = '暂停';"),
    ("pauseBtn.textContent = 'Resume';", "pauseBtn.textContent = '继续';"),
    ("setStatus('Speaking…', 'speaking');", "setStatus('正在朗读…', 'speaking');"),
    ("setStatus('Paused', 'speaking');", "setStatus('已暂停', 'speaking');"),
    ("setStatus('Error: ' + e.error, 'error');", "setStatus('出错：' + e.error, 'error');"),
    ("setStatus('Your browser does not support Speech Synthesis. Try Chrome, Edge, or Safari.', 'error');", "setStatus('您的浏览器不支持语音合成，请使用 Chrome、Edge 或 Safari。', 'error');"),
    ('<h2>Free Online Text to Speech Converter</h2>', '<h2>免费在线文字转语音</h2>'),
    ("<p>AudioTools Text to Speech converts any written text into natural-sounding speech directly in your browser. It uses the <strong>Web Speech Synthesis API</strong> — a built-in browser technology that provides voices in dozens of languages. AudioTools.dev itself has no server: your text goes only to your browser's speech engine.</p>",
     '<p>AudioTools 文字转语音直接在浏览器中把任意文字转为自然的语音。它使用 <strong>Web Speech Synthesis API</strong>——浏览器内置的技术，提供数十种语言的声音。AudioTools.dev 本身没有服务器：您的文字只会交给浏览器的语音引擎。</p>'),
    ('<h3>How It Works</h3>', '<h3>工作原理</h3>'),
    ("<p>Type or paste your text, select a voice and language, adjust speed and pitch, then click \"Speak\". The browser's speech engine processes your text locally and plays it through your speakers. Your text is never sent to AudioTools.dev. Most voices run on your device; voices marked “online” in the list (for example Chrome's “Google” voices) are processed by the browser vendor.</p>",
     '<p>输入或粘贴文字，选择声音和语言，调整语速和音调，然后点击“朗读”。浏览器的语音引擎会处理文字并通过扬声器播放。您的文字不会发送给 AudioTools.dev。大多数声音在您的设备上运行；列表中标有“在线”的声音（例如 Chrome 的“Google”声音）由浏览器厂商处理。</p>'),
    ('<h3>Supported Languages</h3>', '<h3>支持的语言</h3>'),
    ('<p>Available voices depend on your browser and operating system. Most modern browsers provide 50+ voices covering major world languages including English (US, UK, Australian), Spanish, French, German, Italian, Portuguese, Russian, Japanese, Chinese (Mandarin, Cantonese), Korean, Hindi, Arabic, and many more.</p>',
     '<p>可用的声音取决于您的浏览器和操作系统。大多数现代浏览器提供 50 多种声音，覆盖世界主要语言，包括中文（普通话、粤语）、英语（美国、英国、澳大利亚）、西班牙语、法语、德语、意大利语、葡萄牙语、俄语、日语、韩语、印地语、阿拉伯语等。</p>'),
    ('<h3>Use Cases</h3>', '<h3>使用场景</h3>'),
    ('<li>Proofreading — hear your writing to catch errors your eyes miss</li>', '<li>校对——听一遍自己的文字，发现眼睛容易漏掉的错误</li>'),
    ('<li>Language learning — listen to proper pronunciation in any language</li>', '<li>语言学习——听各种语言的标准发音</li>'),
    ('<li>Accessibility — convert articles and documents to audio</li>', '<li>无障碍——把文章和文档变成可以听的内容</li>'),
    ('<li>Content creation — preview voiceover scripts before recording</li>', '<li>内容创作——录音前先试听配音稿</li>'),
    ('<li>Multitasking — listen to text while doing other work</li>', '<li>多任务——一边做别的事一边听文字</li>'),
    ('<h3>Privacy & Security</h3>', '<h3>隐私与安全</h3>'),
    ('<p>All text-to-speech processing happens in your browser using the Web Speech Synthesis API. Your text is never sent to AudioTools.dev servers — there is no backend and nothing is stored. This is the same technology your browser uses for its built-in read-aloud features.</p>',
     '<p>文字转语音通过 Web Speech Synthesis API 在您的浏览器中完成。您的文字不会发送到 AudioTools.dev——我们没有后端，也不存储任何内容。这与浏览器自带的朗读功能使用的是同一项技术。</p>'),
    ('<p>Looking for the reverse? Try our <a href="/voice-to-text/">Voice to Text</a> tool for speech-to-text transcription, or <a href="/converter/">Audio Converter</a> for format conversion.</p>',
     '<p>需要反过来操作？试试<a href="/voice-to-text/">语音转文字</a>，或用<a href="/converter/">音频转换器</a>转换格式。</p>'),
    ('<div class="faq-q">Is this text-to-speech tool free?</div>', '<div class="faq-q">这个文字转语音工具免费吗？</div>'),
    ("<div class=\"faq-a\">Yes, completely free with no limits. It uses your browser's built-in Speech Synthesis API, so there are no server costs and no restrictions on usage.</div>",
     '<div class="faq-a">是的，完全免费，没有限制。它使用浏览器内置的 Speech Synthesis API，没有服务器成本，也没有使用限制。</div>'),
    ('<div class="faq-q">Can I download the speech as an audio file?</div>', '<div class="faq-q">可以把语音下载为音频文件吗？</div>'),
    ('<div class="faq-a">The Web Speech Synthesis API plays audio directly through your speakers. For downloadable audio, you can use screen recording software to capture the output. We may add a download feature in a future update.</div>',
     '<div class="faq-a">Web Speech Synthesis API 会直接通过扬声器播放声音。如需音频文件，可以用录屏或录音软件录下输出。我们可能会在以后的更新中加入下载功能。</div>'),
    ('<div class="faq-q">Which voices and languages are available?</div>', '<div class="faq-q">有哪些声音和语言？</div>'),
    ('<div class="faq-a">Available voices depend on your browser and operating system. Chrome typically offers the most voices (50+), followed by Safari and Edge. Windows, macOS, and Android each provide their own set of system voices.</div>',
     '<div class="faq-a">可用的声音取决于您的浏览器和操作系统。Chrome 通常提供最多的声音（50 多种），其次是 Safari 和 Edge。Windows、macOS 和 Android 也各自提供系统声音。</div>'),
    ('<div class="faq-q">Is my text sent to a server?</div>', '<div class="faq-q">我的文字会被发送到服务器吗？</div>'),
    ("<div class=\"faq-a\">Not to us: AudioTools.dev has no backend. System voices run on your device; voices marked “online”, such as Chrome's “Google” voices, are processed by the browser vendor, so pick a system voice for full privacy.</div>",
     '<div class="faq-a">不会发送给我们：AudioTools.dev 没有后端。系统声音在您的设备上运行；标有“在线”的声音（例如 Chrome 的“Google”声音）由浏览器厂商处理，如需完全私密，请选择系统声音。</div>'),
],
}


def main():
    for tool in BUILT:
        build(tool, TABLES[tool])
    english_page('converter')
    update_hand_made(ROOT / 'zh' / 'converter' / 'index.html', 'converter', '/converter/')
    update_hand_made(ROOT / 'zh' / 'index.html', 'home', '/')


if __name__ == '__main__':
    main()
