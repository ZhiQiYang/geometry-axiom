"""Generate D06 controls and legal PDF close-path cases; never overwrite evidence.

Usage: python3 tests/diagnostics/pdf_snap_close_fixtures.py --out /tmp/pdf-close
All fixtures have two pages. Page 2 uses a 360 x 220 PDF coordinate box;
calibrate viewport (60, 200) -> (260, 200) as 2000 mm in the App.
"""
import argparse
import hashlib
import json
from pathlib import Path

PREFIX = '60 40 m 300 40 l 300 140 l 220 140 l 220 200 l '
CASES = {
    'malformed-h': PREFIX + '60 200 h S',
    'valid-h': PREFIX + '60 200 l h S',
    'explicit-l': PREFIX + '60 200 l 60 40 l S',
    'implicit-s': PREFIX + '60 200 l s',
    'implicit-b': PREFIX + '60 200 l b',
    'implicit-b-star': PREFIX + '60 200 l b*',
    'double-h': PREFIX + '60 200 l h h S',
    'h-then-s': PREFIX + '60 200 l h s',
    # Endpoint (40, 180) in viewport coordinates is not on the scale line.
    'h-then-line': PREFIX + '60 200 l h 40 40 l S',
    'h-h-then-line': PREFIX + '60 200 l h h 40 40 l S',
    'h-then-move': PREFIX + '60 200 l h 30 10 m 50 10 l S',
    'rectangle-re': '60 40 240 160 re S',
    'curved-v-h': '60 40 m 100 80 60 120 v 120 120 l 120 40 l h S',
    'curved-y-h': '60 40 m 100 80 60 120 y 120 120 l 120 40 l h S',
    'straight-v-h': '60 40 m 60 80 60 120 v 120 120 l 120 40 l h S',
    'straight-y-h': '60 40 m 60 80 60 120 y 120 120 l 120 40 l h S',
    'curved-h-then-line': '60 40 m 100 80 60 120 v 120 120 l 120 40 l h 40 40 l S',
}


def pdf(path):
    page1 = b'''0 0 0 RG 2 w
40 60 160 120 re S
240 60 140 120 re S
.5 w 40 195 m 200 195 l S
BT /F1 9 Tf 95 200 Td (1600) Tj ET
'''
    page2 = ('0 0 0 RG 2 w\n' + path + '\n' + '''.5 w 60 20 m 260 20 l S
BT /F1 9 Tf 150 8 Td (2000) Tj ET
BT /F1 10 Tf 120 110 Td (page 2 L room) Tj ET
''').encode('ascii')
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [4 0 R 6 0 R] /Count 2 >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 220] /Rotate 0 /Resources << /Font << /F1 3 0 R >> >> /Contents 5 0 R >>',
        b'<< /Length %d >>\nstream\n' % len(page1) + page1 + b'endstream',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 360 220] /Rotate 0 /Resources << /Font << /F1 3 0 R >> >> /Contents 7 0 R >>',
        b'<< /Length %d >>\nstream\n' % len(page2) + page2 + b'endstream',
    ]
    output = bytearray(b'%PDF-1.4\n')
    offsets = []
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output += b'%d 0 obj\n' % number + obj + b'\nendobj\n'
    xref = len(output)
    output += b'xref\n0 %d\n0000000000 65535 f \n' % (len(objects) + 1)
    for offset in offsets:
        output += b'%010d 00000 n \n' % offset
    output += b'trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(objects) + 1, xref)
    return bytes(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, path in CASES.items():
        data = pdf(path)
        (args.out / (name + '.pdf')).write_bytes(data)
        manifest[name] = {'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'fixtures': len(manifest), 'out': str(args.out.resolve())}))


if __name__ == '__main__':
    main()
