from pathlib import Path
import hashlib
import json

OUT = Path('/tmp/geo337-full-R5-R6-publication-preparation-20261024')
BASE = 'evidence/geo337-train-20261024/'
PEERS = Path('/workspace/train337-canvas-peer-resume')
files = []

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def add(source, destination, pin=None, extra=None):
    source = Path(source)
    assert source.is_file() and not source.is_symlink()
    actual = digest(source) if not extra else pin
    if pin:
        assert actual == pin
    files.append(dict(source_path=str(source), destination=BASE + destination,
                      bytes=source.stat().st_size, sha256=actual, **(extra or {})))

def tree(source, destination):
    source = Path(source)
    for path in sorted(source.rglob('*')):
        assert not path.is_symlink()
        if path.is_file():
            add(path, destination + '/' + str(path.relative_to(source)))

OUT.mkdir()
root_store = Path('/tmp/geo337-archive-object-store-root-20261024')
summary = json.loads((root_store / 'RESULT.json').read_text())
assert summary['exit'] == 0
for item in summary['archives']:
    label = item['label']
    package = Path('/tmp/geo323-' + label + '-full-package-20261024')
    destination = 'full-' + label.upper() + '-five-stage-raw'
    for path in sorted(package.iterdir()):
        if path.name.endswith('.tar.gz'):
            add(path, destination + '/' + path.name, item['sha256'],
                {'preloaded_blob': item['oid'], 'preload_receipt': item['receipt'],
                 'preload_receipt_sha256': digest(item['receipt'])})
        elif path.is_file():
            add(path, destination + '/' + path.name)
    name = label.upper() + '_FULL_FIVE_STAGE_ACTUAL_PACKAGE_PEER.json'
    pin = {'r5': 'b61eb5136f4be7884484b2978167b34916ad743c35cc75f34672aac3c9ff02d9',
           'r6': '85e835f23d2c595de5abc63b18eea45e1b3c56a9b52dc5e392660bf4450be9b9'}[label]
    add(PEERS / name, destination + '/peer/' + name, pin)

tree(root_store, 'archive-object-store/originals')
for source, destination in [
    ('/workspace/connect_geo337_archive_object_store_20261024.py', 'root-wrapper.py'),
    ('/workspace/git-archive-object-store-tool-20261024/write_archive_blob.py', 'write_archive_blob.py'),
    ('/workspace/root-archive-store-actual-peer-combined-20261024/REVIEW.json', 'ACTUAL_REVIEW.json'),
    ('/workspace/review_root_archive_store_actual_combined_20261024.py', 'review_actual.py'),
    ('/workspace/PERMANENT_TMP_GIT_OBJECT_STORE_STORAGE_EXCLUSION_20261024.json', 'PERMANENT_STORE_EXCLUSION.json'),
    ('/tmp/geo337-published-archive-git-objects-20261024/info/CODEX_PERMANENT_OBJECTS.json', 'PERMANENT_LEASE.json')]:
    add(source, 'archive-object-store/' + destination)

for path, pin in [
    ('/workspace/storage-maintenance-three-set-publication-final-20261024/MANIFEST.json',
     '9f783961d15bf44016473596841003fa7a1b2d714b8840c3238c487468bafd9f'),
    ('/workspace/four-scope-alias-publication-manifest-20261024/MANIFEST.json',
     'd3c35b8a7ba056bc880583103d7587d0ea52b15d96014d27ceed45917f3d0201')]:
    assert digest(path) == pin
    for item in json.loads(Path(path).read_text())['files']:
        assert item['destination'].startswith(BASE)
        add(item['source_path'], item['destination'][len(BASE):], item['sha256'])

for name in ['STORAGE_THREE_SETS_FINAL_MANIFEST_STATIC_PEER.json',
             'FOUR_SCOPE_ALIAS_ORIGINALS_ACTUAL_PACKAGE_PEER.json']:
    add(PEERS / name, 'archive-object-store/maintenance-peer/' + name)
add(__file__, 'archive-object-store/prepare_publication.py')
add('/tmp/publish_geo337_evidence_tree_20261024.py', 'archive-object-store/publish_evidence_tree.py')
assert len({x['destination'] for x in files}) == len(files)
result = {'schema': 'geo337-full-R5-R6-publication-plan/1', 'published': False,
          'execution_sources': {'R5': 'a22df116c7e9f6b7d074451f1c8052d59e7e4f3e',
                                'R6': '2bbe54f19b2d19e8a816530f0c4edca950629a34'},
          'original_failures_preserved': True, 'files': files}
target = OUT / 'FILES.json'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'path': str(target), 'sha256': digest(target), 'files': len(files),
                  'bytes': sum(x['bytes'] for x in files)}, ensure_ascii=False))
