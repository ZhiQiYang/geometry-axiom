"""Create evidence contact sheets; never edits the source design or capture."""
from pathlib import Path
import sys
from PIL import Image, ImageOps, ImageDraw

root = Path(__file__).parent
name = sys.argv[1]
source = Image.open(root / 'reference-selected.png').convert('RGB')
actual = Image.open(root / name).convert('RGB')
if actual.size != source.size:
    raise ValueError(f'Size mismatch: {source.size} / {actual.size}')
for region, bounds in [('full', (0, 0, *source.size)), ('inspector', (1082, 66, 1487, 1058))]:
    a, b = source.crop(bounds), actual.crop(bounds)
    sheet = Image.new('RGB', (a.width * 2 + 20, a.height + 32), '#e8edf3')
    sheet.paste(a, (0, 32)); sheet.paste(b, (a.width + 20, 32))
    draw = ImageDraw.Draw(sheet)
    draw.text((10, 10), 'SELECTED REFERENCE', fill='#17233c')
    draw.text((a.width + 30, 10), 'BROWSER IMPLEMENTATION', fill='#17233c')
    sheet.save(root / f'compare-{Path(name).stem}-{region}.png')
