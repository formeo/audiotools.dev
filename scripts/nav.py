#!/usr/bin/env python3
"""Site navigation on every page, English and Chinese: the links bar, the "Tools" menu and the footer's tool list.

    python3 scripts/nav.py           # rewrite the navigation of every page
    python3 scripts/nav.py --check   # exit 1 if a page is out of step (CI)

On a computer the bar shows the main tools, then the language switch and a "Tools" menu with every tool; on a phone
(narrow screens) only the logo, the language switch and the menu are left, in one row. build_zh.py and build_landing.py run this after building.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (path, English name, Chinese name); the bar shows the first ones, the menu all of them
TOOLS = [
    ('converter', 'Converter', '转换器'),
    ('vocal-remover', 'Vocal Remover', '人声消除'),
    ('voice-to-text', 'Voice to Text', '语音转文字'),
    ('text-to-speech', 'Text to Speech', '文字转语音'),
    ('volume-booster', 'Volume Booster', '音量增强'),
    ('audio-trimmer', 'Audio Trimmer', '音频剪辑'),
    ('audio-speed-changer', 'Speed Changer', '音频变速'),
    ('slowed-reverb', 'Slowed + Reverb', '慢速混响'),
    ('audio-joiner', 'Audio Joiner', '音频合并'),
    ('audio-compressor', 'Audio Compressor', '音频压缩'),
]
IN_BAR = 4
ZH_PAGES = {'converter', 'volume-booster', 'text-to-speech', 'audio-joiner', 'audio-compressor', 'audio-trimmer',
            'audio-speed-changer', 'voice-to-text', 'vocal-remover', 'slowed-reverb'}   # tools with a Chinese page
# the footer's list of every tool, short names
FOOTER = [('converter', 'Converter', '转换器'), ('voice-to-text', 'Voice to Text', '语音转文字'), ('text-to-speech', 'Text to Speech', '文字转语音'),
          ('audio-trimmer', 'Trimmer', '剪辑'), ('audio-speed-changer', 'Speed Changer', '变速'), ('volume-booster', 'Volume Booster', '音量增强'),
          ('audio-joiner', 'Joiner', '合并'), ('audio-compressor', 'Compressor', '压缩'), ('vocal-remover', 'Vocal Remover', '人声消除'),
          ('slowed-reverb', 'Slowed + Reverb', '慢速混响')]
FOOTER_RE = re.compile(r'<nav class="at-footer-tools"[^>]*>.*?</nav>', re.S)

NAV_RE = re.compile(r'<div class="at-nav-links">.*?</div>', re.S)
MENU_RE = re.compile(r'\s*<details class="at-menu".*?</details>', re.S)
LANG_RE = re.compile(r'<a href="[^"]*" class="at-lang"[^>]*>[^<]*</a>')

# Closes when the reader taps outside it or presses Escape (works without this too: the summary toggles it)
TOGGLE = ("if(this.open){var d=this;setTimeout(function(){document.addEventListener('click',function c(e){"
          "if(!d.contains(e.target))d.open=false;document.removeEventListener('click',c)})})}")   # no '>' in it: the attribute stays easy to parse
ESCAPE = "if(event.key==='Escape'){this.open=false;this.querySelector('summary').focus()}"
ICON = ('<svg width="18" height="14" viewBox="0 0 18 14" aria-hidden="true"><path d="M1 1h16M1 7h16M1 13h16" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>')


def href(tool, lang):
    if tool == 'home':
        return '/zh/' if lang == 'zh' else '/'
    return f'/zh/{tool}/' if lang == 'zh' and tool in ZH_PAGES else f'/{tool}/'


def link(tool, name, lang, current):
    return f'<a href="{href(tool, lang)}"{" aria-current=\"page\"" if tool == current else ""}>{name}</a>'


def bar(lang, current, lang_link):
    zh = lang == 'zh'
    links = [link(t, z if zh else e, lang, current) for t, e, z in TOOLS[:IN_BAR]]
    if lang_link:
        links.append(lang_link)
    return '<div class="at-nav-links">\n' + ''.join(f'                {l}\n' for l in links) + '            </div>'


def menu(lang, current):
    zh = lang == 'zh'
    items = ''.join(f'\n                    <li>{link(t, z if zh else e, lang, current)}</li>' for t, e, z in TOOLS)
    items += f'\n                    <li class="at-menu-all">{link("home", "全部工具" if zh else "All tools", lang, current)}</li>'
    label = '工具' if zh else 'Tools'
    return (f'\n            <details class="at-menu" ontoggle="{TOGGLE}" onkeydown="{ESCAPE}">'
            f'\n                <summary>{ICON}<span>{label}</span></summary>'
            f'\n                <ul class="at-menu-list" aria-label="{"全部工具" if zh else "All tools"}">{items}\n                </ul>'
            f'\n            </details>')


def footer_tools(lang, current):
    zh = lang == 'zh'
    links = ''.join(link(t, z if zh else e, lang, current) for t, e, z in FOOTER)
    return f'<nav class="at-footer-tools" aria-label="{"全部工具" if zh else "All tools"}">{links}</nav>'


def page_info(path):
    """(lang, current tool) from the file's place in the site."""
    parts = path.relative_to(ROOT).parts
    lang = 'zh' if parts[0] == 'zh' else 'en'
    rest = parts[1:] if lang == 'zh' else parts
    if rest == ('index.html',):
        return lang, 'home'
    tool = rest[0] if len(rest) == 2 else None
    return lang, tool if tool in {t for t, _, _ in TOOLS} else None


def apply(s, lang, current):
    m = NAV_RE.search(s)
    if not m:
        return s
    lang_link = LANG_RE.search(m.group(0))
    s = s[:m.start()] + bar(lang, current, lang_link.group(0) if lang_link else '') + s[m.end():]
    s = MENU_RE.sub('', s, count=1)
    m = NAV_RE.search(s)
    s = s[:m.end()] + menu(lang, current) + s[m.end():]
    return FOOTER_RE.sub(lambda _: footer_tools(lang, current), s, count=1)


def pages():
    for p in sorted(ROOT.rglob('*.html')):
        if any(x in p.parts for x in ('vendor', 'models', 'node_modules', '.git', 'og')):
            continue
        yield p


def main(check=False):
    stale = []
    for p in pages():
        s = p.read_text(encoding='utf-8')
        if 'class="at-nav-links"' not in s:
            continue
        out = apply(s, *page_info(p))
        if out != s:
            stale.append(str(p.relative_to(ROOT)))
            if not check:
                p.write_text(out, encoding='utf-8')
    if check and stale:
        print('Navigation out of step (run scripts/nav.py):', ', '.join(stale))
        sys.exit(1)
    print(('Navigation up to date' if check else 'Navigation written') + (f': {len(stale)} changed' if stale and not check else ''))


if __name__ == '__main__':
    main(check='--check' in sys.argv)
