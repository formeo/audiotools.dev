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
           'M4A', 'AAC', 'WebM', 'ZIP', 'Web Audio API', 'Web Speech Synthesis API', 'Speech Synthesis API', 'dBFS', 'kbps', 'TTS', 'EN', 'Google', 'Chrome', 'Safari', 'Edge', 'Windows', 'macOS', 'Android', 'LAME', 'WebAssembly', 'PCM', 'Firefox', 'Opus', 'opus', 'Telegram', 'WhatsApp', 'iPhone'}


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
    ('"name":"Audio Joiner — AudioTools.dev"',
     '"name":"音频合并 — AudioTools.dev"'),
    ('<p><strong>Drop audio files here</strong> or click to browse</p>',
     '<p><strong>将音频文件拖放到此处</strong>，或点击选择</p>'),
    ('<p>Add several files — MP3, WAV, FLAC, OGG, M4A. Processed locally, never uploaded.</p>',
     '<p>可添加多个文件——MP3、WAV、FLAC、OGG、M4A。在本地处理，绝不上传。</p>'),
    ('>＋ Add more files</button>',
     '>＋ 添加更多文件</button>'),
    ('<label>Crossfade:</label>',
     '<label>淡入淡出：</label>'),
    ('<div class="total-line">Tracks: <b id="trackCount">0</b> · Total length: <b id="totalDur">0:00</b></div>',
     '<div class="total-line">音轨：<b id="trackCount">0</b> · 总时长：<b id="totalDur">0:00</b></div>'),
    ('>Merge &amp; Download</button>',
     '>合并并下载</button>'),
    ('>Clear</button>',
     '>清空</button>'),
    ('<div class="progress-text" id="progressText">Merging…</div>',
     '<div class="progress-text" id="progressText">合并中…</div>'),
    ("progressText.textContent='Merging…';",
     "progressText.textContent='合并中…';"),
    ("progressText.textContent='Encoding…';",
     "progressText.textContent='编码中…';"),
    ('<p class="result-title">Merged — <span',
     '<p class="result-title">合并完成 — <span'),
    ('id="downloadBtn" style="width:100%;">Download</button>',
     'id="downloadBtn" style="width:100%;">下载</button>'),
    ('alert(\'Could not decode "\' + file.name + \'". Skipping. Try MP3, WAV, FLAC, OGG or M4A.\');',
     "alert('无法解码“' + file.name + '”，已跳过。请使用 MP3、WAV、FLAC、OGG 或 M4A。');"),
    ('title="Move up"',
     'title="上移"'),
    ('title="Move down"',
     'title="下移"'),
    ("resultInfo.textContent = tracks.length + ' tracks · '",
     "resultInfo.textContent = tracks.length + ' 条音轨 · '"),
    ('<div class="feature-title">Multiple Files</div><div class="feature-desc">Add any number of audio files and reorder them freely.</div>',
     '<div class="feature-title">多个文件</div><div class="feature-desc">可添加任意数量的音频文件，并自由调整顺序。</div>'),
    ('<div class="feature-title">Crossfade Transitions</div><div class="feature-desc">Add a smooth crossfade between tracks for seamless joins.</div>',
     '<div class="feature-title">淡入淡出过渡</div><div class="feature-desc">在音轨之间添加平滑的淡入淡出，衔接自然。</div>'),
    ('<div class="feature-title">Mix Formats</div><div class="feature-desc">Combine MP3, WAV, FLAC, OGG in any combination.</div>',
     '<div class="feature-title">混合格式</div><div class="feature-desc">MP3、WAV、FLAC、OGG 可任意组合。</div>'),
    ('<div class="feature-desc">All merging in your browser. Files never leave your device.</div>',
     '<div class="feature-desc">所有合并都在浏览器中完成，文件不会离开您的设备。</div>'),
    ('<div class="faq-q">Is my audio uploaded?</div><div class="faq-a">No. All merging happens in your browser using the Web Audio API.</div>',
     '<div class="faq-q">我的音频会被上传吗？</div><div class="faq-a">不会。所有合并都通过 Web Audio API 在您的浏览器中完成。</div>'),
    ('<title>Audio Joiner — Merge MP3 Files Online, Free | AudioTools.dev</title>',
     '<title>音频合并 — 免费在线合并 MP3 文件 | AudioTools.dev</title>'),
    ('Merge MP3, WAV, M4A and voice messages into one file in your browser. Reorder tracks, add a crossfade, save as MP3 or WAV. Free, no upload, no sign-up.',
     '在浏览器中把 MP3、WAV、M4A 和语音消息合并为一个文件。可调整顺序、添加淡入淡出，保存为 MP3 或 WAV。免费，无需上传，无需注册。'),
    ('Audio Joiner — Merge MP3 Files Online, Free',
     '音频合并 — 免费在线合并 MP3 文件'),
    ('merge mp3 files, audio joiner, combine audio files, join mp3 online, merge audio online, merge voice messages, mp3 merger, combine mp3 free',
     'MP3合并, 音频合并, 合并音频文件, 在线合并MP3, 拼接音频, 合并语音消息, 音频拼接工具, 免费合并MP3'),
    ('<h1>Merge Audio Files</h1>',
     '<h1>音频合并</h1>'),
    ('<p>Join MP3s, voice messages and other audio into one track — reorder, crossfade, no upload</p>',
     '<p>把 MP3、语音消息等音频合并成一条音轨——可调整顺序、淡入淡出，无需上传</p>'),
    ('<h2>Merge MP3 and other audio files online</h2>',
     '<h2>在线合并 MP3 等音频文件</h2>'),
    ('<p>Add your files, put them in order and download one file. Audio Joiner runs entirely in your browser: the files are decoded, joined and encoded on your device, so nothing is uploaded, and there is no size quota and no waiting in line.</p>',
     '<p>添加文件、排好顺序，下载一个文件即可。音频合并完全在浏览器中运行：文件在您的设备上解码、拼接和编码，因此不上传任何内容，没有大小配额，也不用排队等待。</p>'),
    ('<h3>How to merge audio files</h3>',
     '<h3>如何合并音频文件</h3>'),
    ('<li>Drop your files on the box above, or click to choose them. You can add more later with “Add more files”.</li>',
     '<li>把文件拖放到上方的框中，或点击选择。之后还可以用“添加更多文件”继续添加。</li>'),
    ('<li>Drag the tracks into the order you want, or use the arrows.</li>',
     '<li>拖动音轨排出想要的顺序，或使用箭头调整。</li>'),
    ('<li>Optionally set a crossfade of up to 3 seconds for a smooth transition. Leave it at 0 for a straight cut.</li>',
     '<li>可选：设置最长 3 秒的淡入淡出，让过渡更平滑。保持 0 则直接衔接。</li>'),
    ('<li>Click “Merge &amp; Download” and save the result as MP3 (192 kbps) or WAV.</li>',
     '<li>点击“合并并下载”，将结果保存为 MP3（192 kbps）或 WAV。</li>'),
    ('<h3>What you can merge</h3>',
     '<h3>可以合并哪些文件</h3>'),
    ('<p>MP3, WAV, M4A/AAC, FLAC, OGG and Opus files, mixed in any order: anything your browser can play. Voice messages saved from WhatsApp or Telegram (.opus, .ogg) work in browsers that play Opus, such as Chrome, Edge and Firefox. Mono and stereo files can be mixed, and files with different sample rates are brought to one rate automatically.</p>',
     '<p>MP3、WAV、M4A/AAC、FLAC、OGG 和 Opus 文件可按任意顺序混合，只要浏览器能播放即可。从 WhatsApp 或 Telegram 保存的语音消息（.opus、.ogg）在支持 Opus 的浏览器中可用，例如 Chrome、Edge 和 Firefox。单声道和立体声可以混合，不同采样率的文件会自动统一。</p>'),
    ('<h3>Common uses</h3>',
     '<h3>常见用途</h3>'),
    ('<li>A podcast episode with its intro and outro</li>',
     '<li>给一期播客接上片头和片尾</li>'),
    ('<li>Several voice messages as one recording</li>',
     '<li>把几条语音消息合成一段录音</li>'),
    ('<li>Audiobook chapters as a single file</li>',
     '<li>把有声书的各章合成一个文件</li>'),
    ('<li>Songs into a mix, with a crossfade between them</li>',
     '<li>把多首歌曲做成串烧，中间加淡入淡出</li>'),
    ('<li>Sound effects or ringtone parts in sequence</li>',
     '<li>按顺序拼接音效或铃声片段</li>'),
    ('<h3>On iPhone and Android</h3>',
     '<h3>在 iPhone 和 Android 上使用</h3>'),
    ('<p>There is nothing to install: open this page in Safari on an iPhone or Chrome on Android, add the files from your phone and download the merged file.</p>',
     '<p>无需安装任何应用：在 iPhone 的 Safari 或 Android 的 Chrome 中打开本页，从手机添加文件，下载合并后的文件即可。</p>'),
    ('<h3>Limits</h3>',
     '<h3>限制</h3>'),
    ("<p>The joiner keeps all tracks in your device's memory while it works. An hour or two of audio is fine on most computers; on a phone, very long merges can run out of memory, so join them in a few parts.</p>",
     '<p>合并过程中，所有音轨都保存在设备内存里。大多数电脑处理一两个小时的音频没有问题；在手机上，过长的合并可能内存不足，可以分几次合并。</p>'),
    ('<p>To make the merged file smaller, use the <a href="/audio-compressor/">audio compressor</a>; to cut a part out first, the <a href="/audio-trimmer/">audio trimmer</a>; for M4A or FLAC, the <a href="/converter/">audio converter</a>; and if one recording is quieter than the rest, the <a href="/volume-booster/">volume booster</a>.</p>',
     '<p>想让合并后的文件更小，用<a href="/audio-compressor/">音频压缩</a>；想先剪掉一部分，用<a href="/audio-trimmer/">音频剪辑</a>；需要 M4A 或 FLAC，用<a href="/converter/">音频转换器</a>；某段录音比其他的小声，用<a href="/volume-booster/">音量增强器</a>。</p>'),
    ('<div class="faq-q">How do I merge MP3 files into one?</div><div class="faq-a">Add the MP3 files, arrange them in order, optionally set a crossfade, then click Merge &amp; Download. You get one MP3 or WAV file, made in your browser.</div>',
     '<div class="faq-q">如何把多个 MP3 合并成一个？</div><div class="faq-a">添加 MP3 文件，排好顺序，可选设置淡入淡出，然后点击“合并并下载”。您会得到一个在浏览器中生成的 MP3 或 WAV 文件。</div>'),
    ('<div class="faq-q">Can I merge different formats?</div><div class="faq-a">Yes. MP3, WAV, M4A, FLAC, OGG and Opus can be mixed in one merge. Each file is decoded by your browser and the result is saved as MP3 or WAV.</div>',
     '<div class="faq-q">可以合并不同格式的文件吗？</div><div class="faq-a">可以。MP3、WAV、M4A、FLAC、OGG 和 Opus 可以在一次合并中混用。每个文件由浏览器解码，结果保存为 MP3 或 WAV。</div>'),
    ('<div class="faq-q">Can I combine WhatsApp or Telegram voice messages?</div><div class="faq-a">Yes. Save the voice messages from the chat (they are .opus or .ogg files) and add them here. Chrome, Edge and Firefox play these files; some older Safari versions do not.</div>',
     '<div class="faq-q">可以合并 WhatsApp 或 Telegram 的语音消息吗？</div><div class="faq-a">可以。从聊天中保存语音消息（.opus 或 .ogg 文件），然后添加到这里。Chrome、Edge 和 Firefox 可以播放这类文件，部分旧版 Safari 不行。</div>'),
    ('<div class="faq-q">Does merging reduce audio quality?</div><div class="faq-a">Saving as WAV keeps the decoded audio unchanged. Saving as MP3 re-encodes it at 192 kbps, which sounds the same as the original for speech and most music.</div>',
     '<div class="faq-q">合并会降低音质吗？</div><div class="faq-a">保存为 WAV 时，解码后的音频保持不变。保存为 MP3 时会以 192 kbps 重新编码，对语音和大多数音乐来说听起来与原文件相同。</div>'),
    ('<div class="faq-q">Is there a limit on the number of files?</div><div class="faq-a">No fixed limit. The only limit is your device\'s memory, since all tracks are held in it while merging.</div>',
     '<div class="faq-q">文件数量有限制吗？</div><div class="faq-a">没有固定限制。唯一的限制是设备内存，因为合并时所有音轨都保存在内存中。</div>'),
],
'audio-compressor': [
    ('"name":"Audio Compressor — AudioTools.dev"',
     '"name":"音频压缩 — AudioTools.dev"'),
    ('<p><strong>Drop audio files here</strong>, one or several, or click to browse</p>',
     '<p><strong>将一个或多个音频文件拖放到此处</strong>，或点击选择</p>'),
    ('<label class="ctrl-label">Bitrate — lower means smaller file</label>',
     '<label class="ctrl-label">码率——越低文件越小</label>'),
    ('>64 kbps — voice / podcast (smallest)</option>',
     '>64 kbps — 语音 / 播客（最小）</option>'),
    ('>128 kbps — general purpose (recommended)</option>',
     '>128 kbps — 通用（推荐）</option>'),
    ('>192 kbps — high quality music</option>',
     '>192 kbps — 高品质音乐</option>'),
    ('>256 kbps — very high quality</option>',
     '>256 kbps — 极高品质</option>'),
    ('>320 kbps — maximum quality</option>',
     '>320 kbps — 最高品质</option>'),
    ('<label class="ctrl-label">Sample rate</label>',
     '<label class="ctrl-label">采样率</label>'),
    ('>Keep original</option>',
     '>保持原样</option>'),
    ('>44100 Hz — CD quality</option>',
     '>44100 Hz — CD 音质</option>'),
    ('>22050 Hz — smaller, fine for voice</option>',
     '>22050 Hz — 更小，适合语音</option>'),
    ('>16000 Hz — smallest, speech only</option>',
     '>16000 Hz — 最小，仅限语音</option>'),
    ('<div class="lbl">Original</div>',
     '<div class="lbl">原始</div>'),
    ('<div class="lbl">Estimated</div>',
     '<div class="lbl">预计</div>'),
    ('>Compress &amp; Download</button>',
     '>压缩并下载</button>'),
    ('<div class="progress-text" id="progressText">Compressing…</div>',
     '<div class="progress-text" id="progressText">压缩中…</div>'),
    ("progressText.textContent = 'Encoding MP3…';",
     "progressText.textContent = '正在编码 MP3…';"),
    ("progressText.textContent = 'Preparing…';",
     "progressText.textContent = '准备中…';"),
    ('<p class="result-title">Compressed — <span',
     '<p class="result-title">压缩完成 — <span'),
    ('id="downloadBtn" style="width:100%;">Download MP3</button>',
     'id="downloadBtn" style="width:100%;">下载 MP3</button>'),
    ("'% (larger)'",
     "'%（变大）'"),
    ("'% vs original'",
     "'%（相比原文件）'"),
    ("alert(err.message || 'Compression failed. Please try again.');",
     "alert(err.message || '压缩失败，请重试。');"),
    ("const B = { files: (n) => n + ' files', compress: (n) => 'Compress ' + n + ' files', zip: 'Download all (ZIP)',\n            done: (ok, n) => (ok === n ? n + ' files' : ok + ' of ' + n + ' files') };",
     "const B = { files: (n) => n + ' 个文件', compress: (n) => '压缩 ' + n + ' 个文件', zip: '全部下载（ZIP）',\n            done: (ok, n) => (ok === n ? n + ' 个文件' : n + ' 个中的 ' + ok + ' 个') };"),
    ('<div class="feature-title">Bitrate Control</div><div class="feature-desc">Choose from 64 to 320 kbps for the right size vs quality.</div>',
     '<div class="feature-title">码率控制</div><div class="feature-desc">在 64 到 320 kbps 之间选择，平衡体积与音质。</div>'),
    ('<div class="feature-title">Sample Rate Options</div><div class="feature-desc">Downsample to 22 kHz or 16 kHz for even smaller files.</div>',
     '<div class="feature-title">采样率选项</div><div class="feature-desc">降到 22 kHz 或 16 kHz，文件更小。</div>'),
    ('<div class="feature-title">Size Preview</div><div class="feature-desc">See the estimated output size before you compress.</div>',
     '<div class="feature-title">大小预览</div><div class="feature-desc">压缩前即可看到预计的输出大小。</div>'),
    ('<div class="feature-desc">All compression in your browser. Files never leave your device.</div>',
     '<div class="feature-desc">所有压缩都在浏览器中完成，文件不会离开您的设备。</div>'),
    ('<div class="faq-q">Can I compress several files at once?</div><div class="faq-a">Yes. Drop several files: all of them are compressed with the same settings, and you can download each one or all of them as a ZIP.</div>',
     '<div class="faq-q">可以一次压缩多个文件吗？</div><div class="faq-a">可以。拖入多个文件，它们会使用相同的设置压缩，可以单独下载，也可以打包成 ZIP 一次下载。</div>'),
    ('<title>Compress MP3 &amp; Audio Files Online, Free | AudioTools.dev</title>',
     '<title>在线压缩 MP3 和音频文件，免费 | AudioTools.dev</title>'),
    ('Make audio files smaller for email or chat. Pick a bitrate, see the new size first, compress one file or a batch. Free, no upload, runs in your browser.',
     '让音频文件更小，方便邮件或聊天发送。选择码率，开始前先看新大小，可压缩单个文件或一批文件。免费，无需上传，在浏览器中运行。'),
    ('Compress MP3 &amp; Audio Files Online, Free',
     '在线压缩 MP3 和音频文件，免费'),
    ('compress mp3, reduce audio file size, audio compressor, make audio file smaller, compress audio for email, mp3 compressor online, compress wav to mp3',
     'MP3压缩, 减小音频文件大小, 音频压缩, 音频变小, 邮件发送音频, 在线MP3压缩, WAV转MP3压缩'),
    ('<h1>Compress Audio Files</h1>',
     '<h1>音频压缩</h1>'),
    ('<p>Make MP3, WAV and other audio files smaller — choose the bitrate, see the size first, no upload</p>',
     '<p>让 MP3、WAV 等音频文件变小——选择码率，先看大小，无需上传</p>'),
    ('<h2>Compress MP3 and other audio files online</h2>',
     '<h2>在线压缩 MP3 等音频文件</h2>'),
    ('<p>Audio Compressor makes audio files smaller by re-encoding them to MP3 at the bitrate and sample rate you choose. It shows the expected size before you start, handles one file or a whole batch, and runs in your browser with the LAME MP3 encoder compiled to WebAssembly, so nothing is uploaded.</p>',
     '<p>音频压缩会按您选择的码率和采样率把音频重新编码为 MP3，从而让文件变小。开始前就能看到预计大小，可以处理单个文件或整批文件，并使用编译为 WebAssembly 的 LAME MP3 编码器在浏览器中运行，不上传任何内容。</p>'),
    ('<h3>How to compress an audio file</h3>',
     '<h3>如何压缩音频文件</h3>'),
    ('<li>Drop one or several files on the box above (MP3, WAV, M4A, FLAC, OGG).</li>',
     '<li>把一个或多个文件拖放到上方的框中（MP3、WAV、M4A、FLAC、OGG）。</li>'),
    ('<li>Choose a bitrate; for speech, a lower sample rate makes the file smaller still.</li>',
     '<li>选择码率；如果是语音，降低采样率还能让文件更小。</li>'),
    ('<li>Check the estimated size.</li>',
     '<li>查看预计大小。</li>'),
    ('<li>Click “Compress &amp; Download”. With several files, download each one or all of them as a ZIP.</li>',
     '<li>点击“压缩并下载”。多个文件时，可单独下载，也可打包成 ZIP 一次下载。</li>'),
    ('<h3>How small will the file be?</h3>',
     '<h3>文件会变成多大？</h3>'),
    ("<p>An MP3's size depends only on its bitrate and length: about 1 MB per minute at 128 kbps and about 0.5 MB per minute at 64 kbps. A 10-minute recording is roughly 10 MB at 128 kbps and 5 MB at 64 kbps.</p>",
     '<p>MP3 的大小只取决于码率和时长：128 kbps 约每分钟 1 MB，64 kbps 约每分钟 0.5 MB。一段 10 分钟的录音，128 kbps 约 10 MB，64 kbps 约 5 MB。</p>'),
    ('<h3>Which bitrate to choose</h3>',
     '<h3>如何选择码率</h3>'),
    ('<li>64 kbps — voice recordings, lectures and podcasts (smallest files)</li>',
     '<li>64 kbps — 语音录音、讲座和播客（文件最小）</li>'),
    ('<li>128 kbps — general purpose, good for most uses</li>',
     '<li>128 kbps — 通用，适合大多数用途</li>'),
    ('<li>192 kbps — music in high quality</li>',
     '<li>192 kbps — 高品质音乐</li>'),
    ('<li>320 kbps — maximum quality, for when size matters least</li>',
     '<li>320 kbps — 最高品质，适合不在意大小的时候</li>'),
    ('<h3>Fit email and chat limits</h3>',
     '<h3>满足邮件和聊天的大小限制</h3>'),
    ('<p>Most email services cap attachments at 20–25 MB: roughly 20–25 minutes of audio at 128 kbps, or 40–50 minutes at 64 kbps. For voice, 64 kbps at 22050 Hz keeps speech clear at the smallest size.</p>',
     '<p>大多数邮箱把附件限制在 20–25 MB：128 kbps 约可容纳 20–25 分钟音频，64 kbps 约 40–50 分钟。如果是语音，64 kbps 加 22050 Hz 能在最小体积下保持清晰。</p>'),
    ('<h3>WAV to MP3: the biggest saving</h3>',
     '<h3>WAV 转 MP3：节省最多</h3>'),
    ('<p>Uncompressed WAV (CD quality) takes about 10.6 MB per minute. Compressing it to MP3 at 128 kbps makes it about 11 times smaller with little audible difference for most uses.</p>',
     '<p>未压缩的 WAV（CD 音质）每分钟约 10.6 MB。压缩为 128 kbps 的 MP3 后约小 11 倍，对大多数用途来说几乎听不出区别。</p>'),
    ('<p>Need other edits? Join files first with the <a href="/audio-joiner/">audio joiner</a>, cut silence at the ends with the <a href="/audio-trimmer/">audio trimmer</a>, make a quiet recording louder with the <a href="/volume-booster/">volume booster</a>, or save M4A or FLAC with the <a href="/converter/">audio converter</a>.</p>',
     '<p>还需要其他处理？可以先用<a href="/audio-joiner/">音频合并</a>把文件连起来，用<a href="/audio-trimmer/">音频剪辑</a>去掉首尾的静音，用<a href="/volume-booster/">音量增强器</a>让小声的录音更响，或用<a href="/converter/">音频转换器</a>保存为 M4A 或 FLAC。</p>'),
    ('<div class="faq-q">How do I reduce the size of an MP3 file?</div><div class="faq-a">Re-encode it at a lower bitrate. Drop the MP3 here, pick 128 kbps or 64 kbps, and download the smaller file. Lowering the sample rate to 22050 Hz shrinks voice recordings further.</div>',
     '<div class="faq-q">如何减小 MP3 文件的大小？</div><div class="faq-a">以更低的码率重新编码。把 MP3 拖到这里，选择 128 kbps 或 64 kbps，下载更小的文件。把采样率降到 22050 Hz，语音录音还能更小。</div>'),
    ('<div class="faq-q">How much smaller will my file be?</div><div class="faq-a">About 1 MB per minute at 128 kbps and 0.5 MB per minute at 64 kbps. A WAV file usually becomes 5 to 20 times smaller. The tool shows the estimate before you compress.</div>',
     '<div class="faq-q">文件会小多少？</div><div class="faq-a">128 kbps 约每分钟 1 MB，64 kbps 约每分钟 0.5 MB。WAV 文件通常会小 5 到 20 倍。压缩前工具会显示预计大小。</div>'),
    ('<div class="faq-q">Does compression affect quality?</div><div class="faq-a">Lossy compression removes some data. At 192 kbps or higher, most listeners cannot tell the difference from the original; for speech, 64 kbps is enough.</div>',
     '<div class="faq-q">压缩会影响音质吗？</div><div class="faq-a">有损压缩会去掉一部分数据。在 192 kbps 及以上，大多数听众听不出与原文件的区别；如果是语音，64 kbps 就够了。</div>'),
    ('<div class="faq-q">Which sample rate should I use for voice?</div><div class="faq-a">22050 Hz keeps speech clear and makes the file smaller. 16000 Hz is the smallest and still fine for speech, but not for music.</div>',
     '<div class="faq-q">语音应该用什么采样率？</div><div class="faq-a">22050 Hz 能保持语音清晰，同时让文件更小。16000 Hz 最小，语音仍然可以，但不适合音乐。</div>'),
    ('<div class="faq-q">Is my audio uploaded?</div><div class="faq-a">No. All compression happens in your browser.</div>',
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
