"""Read-only reproduction against the dedicated audit service. No scene mutation."""
import argparse
import json
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url', required=True, help='A running isolated audit server, e.g. http://localhost:8803')
parser.add_argument('--out', type=Path, help='Write new responses here; defaults to a fresh TEMP directory')
args = parser.parse_args()
output = args.out or Path(tempfile.mkdtemp(prefix='geometry-capability-repro-'))
output.mkdir(parents=True, exist_ok=True)
dump = json.loads((HERE / 'manual-native-dump.json').read_text(encoding='utf-8-sig'))
scene = dump['text']
kept, inside = [], False
for line in scene.splitlines():
    if line == 'assembly begin':
        inside = True
    elif line == 'assembly end':
        inside = False
    elif not inside and not line.startswith(('requires assembly-', 'canvas-pos assembly-')):
        kept.append(line)

results = []
for label, source in [('original-mixed-project', scene), ('diagnostic-copy-without-assembly', '\n'.join(kept) + '\n')]:
    payload = {'definitions': {'base_scene': source, 'extensions': []}, 'request': {
        'roots': [{'kind': 'profile-run', 'id': 0}], 'role': 'geometry',
        'target': 'solid-set', 'allow_partial': False}}
    request = Request(args.url.rstrip('/') + '/model', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=60) as response:
            result = json.load(response)
    except Exception as exc:
        if hasattr(exc, 'read'):
            result = json.loads(exc.read())
        else:
            result = {'transport_error': str(exc)}
    (output / (label + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    results.append({'case': label, 'ok': result.get('ok'), 'manifest': result.get('manifest', {}).get('schema'), 'error': result.get('error'), 'diagnostics': result.get('diagnostics'), 'objects': len(result.get('derived', {}).get('objects', []))})
print(json.dumps(results, ensure_ascii=False, indent=2))
print('Responses:', output)
