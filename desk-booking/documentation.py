"""Build offline manuals and require explicit documentation review before packaging."""
import argparse
from datetime import datetime
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
COMPONENT = ROOT / 'custom_components/desk_booking'
DOCS = COMPONENT / 'frontend/docs'
MANUALS = ('benutzer', 'administrator')


def inline(value):
    value = escape(value)
    value = re.sub(r'`([^`]+)`', r'<code>\1</code>', value)
    value = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', value)
    return re.sub(r'\[([^\]]+)\]\(((?:https://|/|[a-z])[\w\-./?=&#;:%+]+)\)',
                  r'<a href="\2" rel="noopener noreferrer">\1</a>', value)


def slug(value):
    return re.sub(r'[^\w-]+', '-', value.casefold()).strip('-')


def render_blocks(lines):
    out, paragraph, listing, table = [], [], None, False
    def close_paragraph():
        if paragraph:
            out.append('<p>' + inline(' '.join(paragraph)) + '</p>')
            paragraph.clear()
    def close_list():
        nonlocal listing
        if listing:
            out.append('</'+listing+'>'); listing = None
    def close_table():
        nonlocal table
        if table:
            out.append('</tbody></table></div>'); table = False
    for line in [*lines, '']:
        if line.startswith('|'):
            close_paragraph(); close_list()
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(re.fullmatch(r':?-+:?', c) for c in cells):
                continue
            if not table:
                out.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+inline(c)+'</th>' for c in cells)+'</tr></thead><tbody>'); table = True
            else:
                out.append('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in cells)+'</tr>')
            continue
        close_table()
        if not line.strip():
            close_paragraph(); close_list(); continue
        if line.startswith('### '):
            close_paragraph(); close_list(); out.append('<h3>'+inline(line[4:])+'</h3>'); continue
        match = re.match(r'^(?:(\d+)\. |(-) )(.*)$', line)
        if match:
            close_paragraph(); kind = 'ol' if match[1] else 'ul'
            if listing != kind:
                close_list(); out.append('<'+kind+'>'); listing = kind
            out.append('<li>'+inline(match[3])+'</li>'); continue
        close_list(); paragraph.append(line)
    return '\n'.join(out)


STYLE = '''
:root{color-scheme:light;--ink:#20343e;--muted:#526b76;--line:#d8e4e5;--brand:#236c70}*{box-sizing:border-box}body{margin:0;color:var(--ink);background:#f3f6f6;font:16px/1.65 system-ui,sans-serif}a{color:#155c72;text-underline-offset:3px}header{background:#fff;border-bottom:1px solid var(--line);padding:26px max(24px,calc((100vw - 1320px)/2));}header .brand{letter-spacing:2px;font-size:11px;font-weight:750;color:var(--brand)}h1{font-size:clamp(24px,3vw,36px);line-height:1.2;margin:10px 0}header p{color:var(--muted);margin:6px 0 18px}.actions{display:flex;flex-wrap:wrap;align-items:center;gap:12px}button,.actions a{font:inherit;border:1px solid var(--line);border-radius:8px;padding:8px 12px;background:#fff;color:var(--brand);cursor:pointer;text-decoration:none}.layout{display:grid;grid-template-columns:280px minmax(0,1fr);max-width:1320px;gap:36px;margin:auto;padding:30px 24px}aside{position:sticky;top:16px;align-self:start;max-height:calc(100vh - 32px);overflow:auto;padding:18px;background:#fff;border:1px solid var(--line);border-radius:12px}aside label{display:block;font-size:13px;font-weight:650}input[type=search]{display:block;width:100%;padding:10px;border:1px solid var(--line);border-radius:7px;font:inherit;margin:8px 0}nav a{display:block;font-size:13px;padding:6px 0;line-height:1.5}#found{font-size:12px;color:var(--muted)}main{min-width:0}section{background:white;border:1px solid var(--line);border-radius:12px;margin-bottom:24px;padding:24px 30px;scroll-margin-top:16px}h2{font-size:25px;line-height:1.3;margin:0 0 18px}h3{font-size:19px;line-height:1.4;margin:28px 0 12px}p{margin:12px 0}li{padding-left:4px;margin:8px 0}code{font:14px/1.5 ui-monospace,monospace;overflow-wrap:anywhere;background:#edf3f3;padding:2px 4px;border-radius:4px}.table-wrap{overflow-x:auto;margin:18px 0}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.55}th,td{padding:11px 13px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line);overflow-wrap:anywhere}th{background:#e9f2f1}tr:last-child td{border-bottom:0}footer{color:var(--muted);text-align:center;font-size:12px;padding:10px 24px 35px}.hidden{display:none}a:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid #51a5ae;outline-offset:3px}@media(max-width:850px){.layout{display:block;padding:18px 12px}aside{position:static;max-height:none;margin-bottom:20px}section{padding:20px 18px}nav{columns:2}h2{font-size:22px}}@media(max-width:500px){nav{columns:1}header{padding:22px 18px}}@media print{body{background:white;font:10pt/1.5 sans-serif}header{padding:0 0 14pt}.actions,aside{display:none}.layout{display:block;padding:0}section,section.hidden{display:block!important;border:0;border-radius:0;padding:0;margin:0 0 22pt}h2,h3{break-after:avoid}tr{break-inside:avoid}.table-wrap{overflow:visible}th,td{padding:6pt}a{color:inherit}footer{padding:10pt 0}code{font-size:9pt}h1{font-size:24pt}h2{font-size:17pt}h3{font-size:13pt}}
'''
SCRIPT = '''
const field=document.getElementById('search'),sections=[...document.querySelectorAll('main section')],links=[...document.querySelectorAll('nav a')];
function search(){const q=field.value.trim().toLocaleLowerCase('de');let visible=0;for(const section of sections){const match=!q||section.textContent.toLocaleLowerCase('de').includes(q);section.classList.toggle('hidden',!match);const link=links.find(a=>decodeURIComponent(a.hash.slice(1))===section.id);if(link)link.classList.toggle('hidden',!match);if(match)visible++;}document.getElementById('found').textContent=visible+' von '+sections.length+' Abschnitten';}
field.addEventListener('input',search);document.querySelector('nav').addEventListener('click',()=>{field.value='';search();});document.getElementById('print').addEventListener('click',()=>window.print());search();
'''


def render(name, version, reviewed):
    source = (DOCS / (name+'.md')).read_text(encoding='utf-8')
    sections, title, current = [], '', None
    for line in source.splitlines():
        if line.startswith('# '):
            title = line[2:]; current = ['Über dieses Handbuch', []]; sections.append(current)
        elif line.startswith('## '):
            current = [line[3:], []]; sections.append(current)
        elif current:
            current[1].append(line)
    toc = ''.join('<a href="#'+slug(heading)+'">'+escape(heading)+'</a>' for heading, _ in sections)
    content = ''.join('<section id="'+slug(heading)+'"><h2>'+escape(heading)+'</h2>'+render_blocks(lines)+'</section>' for heading, lines in sections)
    other = 'administrator' if name == 'benutzer' else 'benutzer'
    return '<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(title)+'</title><style>'+STYLE+'</style><header><div class="brand">DESK BOOKING · HANDBÜCHER</div><h1>'+escape(title)+'</h1><p>Version '+escape(version)+' · Redaktionell geprüft am '+escape(reviewed[:10])+'</p><div class="actions"><a href="'+other+'.html">'+('Administratorhandbuch' if other == 'administrator' else 'Benutzerhandbuch')+'</a><a href="'+name+'.md">Markdown-Quelle</a><button id="print" type="button">Drucken / als PDF speichern</button></div></header><div class="layout"><aside><label for="search">In diesem Handbuch suchen</label><input id="search" type="search" placeholder="Suchbegriff"><div id="found" aria-live="polite"></div><nav aria-label="Inhaltsverzeichnis">'+toc+'</nav></aside><main>'+content+'</main></div><footer>Mit der installierten Desk-Booking-Version ausgelieferte Dokumentation. Individuelle Einstellungen können von Standardwerten abweichen.</footer><script>'+SCRIPT+'</script></html>\n'


def content_digest(path):
    data = path.read_bytes()
    if path.suffix in {'.py', '.json', '.js', '.yaml', '.yml', '.md', '.html'}:
        data = data.replace(b'\r\n', b'\n')
    return sha256(data).hexdigest()


def sources():
    result = {}
    for path in COMPONENT.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and DOCS not in path.parents:
            result[path.relative_to(ROOT).as_posix()] = content_digest(path)
    for path in [ROOT/'package_m365.py', ROOT/'documentation.py', ROOT.parent/'AGENTS.md', ROOT.parent/'schreibtisch-display-01.checkedin.redacted.yaml']:
        result[path.relative_to(ROOT.parent).as_posix()] = content_digest(path)
    return result


def check():
    manifest = json.loads((DOCS/'review.json').read_text(encoding='utf-8'))
    version = json.loads((COMPONENT/'manifest.json').read_text())['version']
    if manifest['version'] != version or manifest['sources'] != sources():
        raise SystemExit('Handbuchprüfung fehlt: Code/Version geändert. Handbücher redaktionell prüfen und documentation.py --review ausführen.')
    for name, digest in manifest['manuals'].items():
        if content_digest(DOCS/name) != digest:
            raise SystemExit('Handbücher geändert: HTML-Ausgaben nach redaktioneller Prüfung mit documentation.py --review erzeugen.')
    for name in MANUALS:
        if (DOCS/(name+'.html')).read_text(encoding='utf-8') != render(name, version, manifest['reviewed_at']):
            raise SystemExit('Handbuch-HTML entspricht nicht der Markdown-Quelle.')
    for name, mirror in [('benutzer','USER_MANUAL.md'),('administrator','ADMIN_MANUAL.md')]:
        if (ROOT.parent/'docs'/mirror).read_text(encoding='utf-8') != (DOCS/(name+'.md')).read_text(encoding='utf-8'):
            raise SystemExit('Handbuch-Spiegel veraltet: documentation.py --review erforderlich.')
    print('HANDBUECHER_OK', version)


def review():
    version = json.loads((COMPONENT/'manifest.json').read_text())['version']
    reviewed = datetime.now(ZoneInfo('Europe/Berlin')).isoformat(timespec='seconds')
    for name in MANUALS:
        (DOCS/(name+'.html')).write_text(render(name, version, reviewed), encoding='utf-8')
    (ROOT.parent/'docs').mkdir(exist_ok=True)
    for name, mirror in [('benutzer','USER_MANUAL.md'),('administrator','ADMIN_MANUAL.md')]:
        (ROOT.parent/'docs'/mirror).write_bytes((DOCS/(name+'.md')).read_bytes())
    manuals = {p.name:content_digest(p) for p in DOCS.iterdir() if p.suffix in ('.md','.html')}
    (DOCS/'review.json').write_text(json.dumps({'version':version,'reviewed_at':reviewed,'sources':sources(),'manuals':manuals},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    check()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', action='store_true', help='Nach redaktioneller Inhaltsprüfung HTML und Reviewstand aktualisieren')
    parser.add_argument('--check', action='store_true', help='Quellen, Version und generierte Handbücher prüfen')
    args = parser.parse_args()
    review() if args.review else check()
