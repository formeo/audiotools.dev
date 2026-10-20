#!/usr/bin/env python3
"""Keep SEO metadata in step with the pages.

    python3 scripts/seo_sync.py          # rewrite FAQPage JSON-LD from the visible FAQ, refresh sitemap <lastmod>
    python3 scripts/seo_sync.py --check  # exit 1 if any FAQPage JSON-LD differs from the visible FAQ (used in CI)

The visible FAQ is the single source: Google requires FAQ markup to match what users see.
<lastmod> is the date of the last commit touching the page, or today if it has uncommitted changes.
"""
import datetime, json, re, subprocess, sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
FAQ_HEADINGS = ('Frequently Asked Questions', '常见问题')


def text(el):
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).replace(' ,', ',').replace(' .', '.').strip()


def visible_faq(soup):
    """[(question, answer)] from .faq-item blocks, or from h3 + paragraphs under an FAQ h2."""
    items = soup.select('.faq-item')
    if items:
        return [(text(i.select_one('.faq-q')), text(i.select_one('.faq-a'))) for i in items]
    h2 = next((h for h in soup.find_all('h2') if text(h) in FAQ_HEADINGS), None)
    if not h2:
        return []
    out = []
    for el in h2.find_next_siblings():
        if el.name in ('h2', 'section'):
            break
        if el.name == 'h3':
            out.append([text(el), ''])
        elif el.name == 'p' and out:
            out[-1][1] = (out[-1][1] + ' ' + text(el)).strip()
    return [tuple(x) for x in out]


def faq_nodes(data):
    nodes = data.get('@graph', [data]) if isinstance(data, dict) else data
    return [n for n in nodes if isinstance(n, dict) and n.get('@type') == 'FAQPage']


def sync_faq(path, check):
    html = path.read_text(encoding='utf-8')
    faq = visible_faq(BeautifulSoup(html, 'html.parser'))
    entity = [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]
    changed = False

    def fix(m):
        nonlocal changed
        data = json.loads(m.group(2))
        nodes = faq_nodes(data)
        if not nodes:
            return m.group(0)
        if not faq:
            raise SystemExit(f'{path}: FAQPage markup but no visible FAQ')
        for n in nodes:
            if n.get('mainEntity') != entity:
                changed = True
                n['mainEntity'] = entity
        body = json.dumps(data, ensure_ascii=False, indent=4).replace('\n', '\n    ')
        return f'{m.group(1)}\n    {body}\n    {m.group(3)}'

    new = re.sub(r'(<script type="application/ld\+json">)\s*(.*?)\s*(</script>)', fix, html, flags=re.S)
    if changed and not check:
        path.write_text(new, encoding='utf-8')
    return changed


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def sync_sitemap():
    sitemap = ROOT / 'sitemap.xml'
    xml = sitemap.read_text(encoding='utf-8')
    dirty = {l[3:] for l in git("status", "--porcelain").splitlines()}
    today = datetime.date.today().isoformat()

    def fix(m):
        rel = m.group(2).split('audiotools.dev/', 1)[1] + 'index.html'
        day = today if rel in dirty else (git('log', '-1', '--format=%cs', '--', rel) or today)
        return f'{m.group(1)}{m.group(2)}{m.group(3)}{day}{m.group(5)}'

    new = re.sub(r'(<loc>)([^<]+)(</loc>\s*<lastmod>)([^<]*)(</lastmod>)', fix, xml)
    if new != xml:
        sitemap.write_text(new, encoding='utf-8')


def main():
    check = '--check' in sys.argv
    pages = sorted(p for p in ROOT.rglob('index.html') if '.git' not in p.parts)
    drift = [str(p.relative_to(ROOT)) for p in pages if sync_faq(p, check)]
    if check:
        if drift:
            print('FAQPage JSON-LD differs from the visible FAQ in:', *drift, sep='\n  ')
            print('Run: python3 scripts/seo_sync.py')
            sys.exit(1)
        print('FAQ markup matches the visible FAQ on every page.')
        return
    sync_sitemap()
    print('FAQ markup updated:', drift or 'none', '| sitemap lastmod refreshed')


if __name__ == '__main__':
    main()
