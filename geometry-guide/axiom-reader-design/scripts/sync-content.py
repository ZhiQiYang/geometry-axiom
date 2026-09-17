"""Read the project's sources; write only this prototype's data and diagram assets."""
from pathlib import Path
import hashlib
import html
import json
import re
import sys

APP = Path(__file__).resolve().parents[1]
GUIDE = APP.parent
ROOT = GUIDE.parent
sys.path.insert(0, str(GUIDE))
import axiom_matrix as am

source = (ROOT / '公理層.md').read_text(encoding='utf-8')
plain_source = (GUIDE / '公理層-白話.md').read_text(encoding='utf-8')
reader = (GUIDE / '公理層-閱讀器.html').read_text(encoding='utf-8')
clauses = am.parse_clauses(source)
assert len(clauses) == 63, 'Review parser if the axiom inventory changes.'
known = {c[0] for c in clauses}
plain = {m[1]: m[2].strip() for m in re.finditer(r'^## ([DIR]\d+[a-z]?)\s*\n(.*?)(?=^## |\Z)', plain_source, re.S | re.M)}
assert set(plain) <= known
articles = {m[1]: m[2] for m in re.finditer(r'<article\b[^>]*id="c-([^"]+)"[^>]*>(.*?)</article>', reader, re.S)}
assert set(articles) == known
assets = APP / 'public' / 'assets' / 'diagrams'
assets.mkdir(parents=True, exist_ok=True)

# Preserve engineering output exactly. Only apply the reader's dark presentation.
svg_css = '''svg{background:#181e24} .frame{fill:#181e24;stroke:none}
polygon,line,rect{vector-effect:non-scaling-stroke}
.title{font:bold 150px sans-serif;fill:#d7dfe6}
.label{font:110px sans-serif;fill:#c5cfd8;text-anchor:middle;dominant-baseline:middle}
.guide-label{text-anchor:start;fill:#ed9494}
.timber-label{fill:#efba69;font-weight:bold}
.guide-label,.timber-label{paint-order:stroke;stroke:#181e24;stroke-width:30px;stroke-linejoin:round}
.surface{fill:#304557;fill-opacity:.7;stroke:#84c8f6;stroke-width:1.5px}
.hole{fill:#181e24;stroke:#84c8f6;stroke-width:1.5px}
.edge{stroke:#84c8f6;stroke-width:1.5px}
.edge-free{stroke:#efba69;stroke-width:1.5px;stroke-dasharray:30 15}
.guide{stroke:#ed9494;stroke-width:1px;stroke-dasharray:60 30}
.timber-face{fill:#edb365;fill-opacity:.5;stroke:#edb365;stroke-width:1.5px}
.timber-face-near{fill-opacity:.85}'''

def diagram_asset(match):
    svg = match[0]
    digest = hashlib.sha256(svg.encode()).hexdigest()[:16]
    svg = svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    p = svg.index('>') + 1
    svg = svg[:p] + '<style>' + svg_css + '</style>' + svg[p:]
    (assets / f'{digest}.svg').write_text(svg, encoding='utf-8')
    full = re.search(r'data-full="([^"]+)"', svg)
    if full:
        wide = re.sub(r'viewBox="[^"]+"', f'viewBox="{full[1]}"', svg, count=1)
        (assets / f'{digest}-full.svg').write_text(wide, encoding='utf-8')
    return f'<img class="scene-diagram" src="/assets/diagrams/{digest}.svg" data-plan="/assets/diagrams/{digest}.svg" data-full="/assets/diagrams/{digest}-full.svg" alt="由專案場景產生的幾何配置圖" loading="lazy" />'

data = []
for cid, line, title, body in clauses:
    refs = list(dict.fromkeys(m[0] for m in re.finditer(r'\b(?:D\d+[a-z]?|I\d+|R\d+)(?:\([a-z]\))?', body) if m[0] != cid))
    assert all(re.sub(r'\([a-z]\)', '', ref) in known for ref in refs)
    subs = {}
    for match in re.finditer(r'^\s+\(([a-z])\)\s+(.*?)(?=^\s+\([a-z]\)\s|\Z)', body, re.S | re.M):
        subs[match[1]] = match[2].strip()
    example_sections = re.findall(r'<section class="ex-wrap">.*?</section>', articles[cid], re.S)
    examples = []
    for section in example_sections:
        for entry in re.findall(r'<details\b.*?</details>', section, re.S):
            entry = re.sub(r'<svg\b.*?</svg>', diagram_asset, entry, flags=re.S)
            entry = re.sub(r'(<details\b[^>]*?)\sopen(?=[\s>])', r'\1', entry)
            examples.append(entry)
    data.append(dict(id=cid, line=line, title=title, body=body, plain=plain.get(cid, ''), refs=refs, subs=subs, examples=examples))

for clause in data:
    clause['backlinks'] = [c['id'] for c in data if any(re.sub(r'\([a-z]\)', '', r) == clause['id'] for r in c['refs'])]

r6 = next(c for c in data if c['id'] == 'R6')
hero = re.search(r'src="([^"]+\.svg)"', r6['examples'][0])[1]
# A presentation crop of the supplied engine SVG; no geometry is changed.
hero_svg = (APP / 'public' / hero.lstrip('/')).read_text(encoding='utf-8')
hero_svg = re.sub(r'viewBox="[^"]+"', 'viewBox="-420 1650 5320 3990"', hero_svg, count=1)
hero_svg = re.sub(r'<text\b[^>]*class="title"[^>]*>.*?</text>', '', hero_svg)
hero_svg = re.sub(r'<text\b[^>]*>邊[345]</text>', '', hero_svg)
hero_svg = hero_svg.replace('x="10" y="1500" class="label timber-label"', 'x="-130" y="1500" class="label timber-label" text-anchor="end"')
hero_svg = hero_svg.replace('x="3990" y="2000" class="label timber-label"', 'x="4290" y="2000" class="label timber-label"')
hero_svg = hero_svg.replace('x="2000" y="2990" class="label timber-label"', 'x="2000" y="3270" class="label timber-label"')
hero_svg = hero_svg.replace('x="3000" y="1010" class="label timber-label"', 'x="3000" y="1230" class="label timber-label"')
hero_svg = hero_svg.replace('x="3040" y="1020"', 'x="3040" y="1510"')
hero_svg = re.sub(r'(角材[1345]) A0', r'\1', hero_svg)
hero_svg = hero_svg.replace('font:110px sans-serif', 'font:170px sans-serif')
hero_svg = hero_svg.replace('fill:#304557;fill-opacity:.7', 'fill:#415b73;fill-opacity:.82')
hero_svg = hero_svg.replace('stroke-width:1.5px', 'stroke-width:2px')
hero_svg = hero_svg.replace(' transform="rotate(-90 2120 500)"', '')
(assets / 'r6-overview.svg').write_text(hero_svg, encoding='utf-8')
hero = '/assets/diagrams/r6-overview.svg'
out = dict(clauses=data, hero=hero, sourceHash=hashlib.sha256(source.encode()).hexdigest(), sourceFile='公理層.md', exampleSource='公理層-閱讀器.html', exampleNote='既有閱讀器的範例記錄，未在新版中重新執行引擎。')
(APP / 'src' / 'content.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Synced {len(data)} clauses, {sum(len(c["examples"]) for c in data)} examples; source SHA256 {out["sourceHash"][:12]}')
