#!/usr/bin/env python3
"""Keep SEO metadata in step with the pages.

    python3 scripts/seo_sync.py          # rewrite FAQPage JSON-LD from the visible FAQ, complete WebApplication
                                         # markup (author, isPartOf, dateModified), refresh sitemap <lastmod>
    python3 scripts/seo_sync.py --check  # exit 1 if any FAQPage JSON-LD differs from the visible FAQ (used in CI)

The .github/workflows/seo-sync.yml workflow runs this script on demand and opens a PR with the result.

The visible FAQ is the single source: Google requires FAQ markup to match what users see.
<lastmod> is the date of the last commit touching the page, or today if it has uncommitted changes.
"""
import datetime, json, re, subprocess, sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
FAQ_HEADINGS = ('frequently asked questions', '常见问题')


def text(el):
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).replace(' ,', ',').replace(' .', '.').strip()


def visible_faq(soup):
    """[(question, answer)] from .faq-item blocks, or from h3 + paragraphs under an FAQ h2."""
    items = soup.select('.faq-item')
    if items:
        return [(text(i.select_one('.faq-q')), text(i.select_one('.faq-a'))) for i in items]
    h2 = next((h for h in soup.find_all('h2') if text(h).lower() in FAQ_HEADINGS), None)
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


AUTHOR = {"@type": "Person", "name": "Roman Gordienko", "url": "https://github.com/formeo"}
IS_PART_OF = {"@type": "WebSite", "name": "AudioTools.dev", "url": "https://audiotools.dev"}


def schema_nodes(body):
    try:
        data = json.loads(body)
    except ValueError:
        return []
    nodes = data.get('@graph', [data]) if isinstance(data, dict) else data
    return [n for n in nodes if isinstance(n, dict)]


def sync_schema(path, check, dirty):
    """WebApplication blocks: author, isPartOf and a dateModified = the last commit touching the page.

    Author and site attribution help AI crawlers (a growing share of the site's traffic) tie every
    tool to the same entity; dateModified is a freshness signal on the page itself (the sitemap's
    <lastmod> covers search engines). Insertions keep the block's own style (compact or pretty).
    """
    html = path.read_text(encoding='utf-8')
    rel = str(path.relative_to(ROOT))
    today = datetime.date.today().isoformat()
    day = today if rel in dirty else (git('log', '-1', '--format=%cs', '--', rel) or today)

    def fix(m):
        block = m.group(0)
        nodes = schema_nodes(m.group(2))
        app = next((n for n in nodes if n.get('@type') == 'WebApplication'), None)
        if not app:
            return block
        if check:
            return block   # only the FAQ drift is enforced in CI; this runs via the SEO sync workflow
        i, j = block.index('{'), block.rindex('}')
        core = block[i:j + 1]
        compact = '\n' not in core
        sep = ',' if compact else ',\n        '
        dump = lambda d: json.dumps(d, ensure_ascii=False, separators=(',', ':')) if compact else json.dumps(d, ensure_ascii=False)
        ins = ''
        if 'author' not in app:
            ins += sep + f'"author": {dump(AUTHOR)}' if not compact else sep + f'"author":{dump(AUTHOR)}'
        if 'isPartOf' not in app:
            ins += sep + f'"isPartOf": {dump(IS_PART_OF)}' if not compact else sep + f'"isPartOf":{dump(IS_PART_OF)}'
        elif app['isPartOf'].get('name') == 'Audio Tools':
            core = core.replace('"name": "Audio Tools"', '"name": "AudioTools.dev"')
        ins += sep + (f'"dateModified":"{day}"' if compact else f'"dateModified": "{day}"')
        if compact:
            newcore = re.sub(r'"dateModified":"[^"]*"', '', core)  # drop the stale one, re-add below
            newcore = newcore.replace(',}', '}')                   # in case it was the last field
            newcore = newcore[:-1] + ins + '}'
        else:
            lines = core.split('\n')
            body_lines = [l for l in lines if '"dateModified"' not in l]
            if len(body_lines) != len(lines):                      # a stale date was there: fix the comma
                body_lines[-2] = body_lines[-2].rstrip(',')
            lines = body_lines
            lines[-2] += ','
            lines.insert(-1, f'        "dateModified": "{day}"')
            # author/isPartOf insertions (rare: only pages missing them)
            extra = []
            if 'author' not in app:
                extra.append('        "author": ' + dump(AUTHOR) + ',')
            if 'isPartOf' not in app:
                extra.append('        "isPartOf": ' + dump(IS_PART_OF) + ',')
            for k, e in enumerate(extra):
                lines.insert(-2 + k, e)
            newcore = '\n'.join(lines)
        return block[:i] + newcore + block[j + 1:]

    new = re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)', fix, html, flags=re.S)
    if new != html:
        path.write_text(new, encoding='utf-8')
        return [rel]
    return []


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
    dirty = {l[3:] for l in git('status', '--porcelain').splitlines()}
    schema = [m for p in pages for m in sync_schema(p, check, dirty)]
    sync_sitemap()
    print('FAQ markup updated:', drift or 'none',
          '| WebApplication schema touched:', schema or 'none',
          '| sitemap lastmod refreshed')


if __name__ == '__main__':
    main()
