from PIL import Image
from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[1]
a = Image.open(root / 'qa/reference.png')
b = Image.open(root / 'qa/implementation-final.png')
print('Source/capture dimensions:', a.size, b.size)
b = b.resize(a.size)

def compare(x, y, name):
    board = Image.new('RGB', (x.width * 2, x.height))
    board.paste(x, (0, 0))
    board.paste(y, (x.width, 0))
    board.save(root / 'qa' / name)

compare(a, b, 'comparison-final.png')
for name, box in {'reading': (224, 75, 952, 615), 'reference': (952, 142, 1487, 910)}.items():
    compare(a.crop(box), b.crop(box), f'detail-{name}.png')

data = json.loads((root / 'src/content.json').read_text(encoding='utf-8'))
images = [s for c in data['clauses'] for ex in c['examples'] for s in re.findall(r'(?:src|data-full)="([^"]+)"', ex)]
missing = [s for s in images if not (root / 'public' / s.lstrip('/')).exists()]
assert not missing, missing
assert not any(re.search(r'<script|onload=|onclick=|javascript:', ex, re.I) for c in data['clauses'] for ex in c['examples'])
print('Clauses:', len(data['clauses']), 'Examples:', sum(len(c['examples']) for c in data['clauses']), 'Missing images:', len(missing))
