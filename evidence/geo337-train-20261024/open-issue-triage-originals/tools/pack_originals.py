"""Freeze the completed open-issue triage originals; no subject or Git writes."""
import datetime
import hashlib
import io
import json
import stat
import tarfile
from pathlib import Path

BASE = Path('/workspace/open-issue-triage-originals-publication-20261024')
OUT = BASE / 'package'
R1 = Path('/tmp/open-issue-triage-handoff-refresh-20261024')
R2 = Path('/workspace/open-issue-triage-handoff-refresh-20261024-r2')
PEER = Path('/tmp/train337-adversarial')
CAT = Path('/tmp/open-issue-source-triage-20261024')

def digest(value):
    return hashlib.sha256(value).hexdigest()

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

assert not OUT.exists(), 'fresh package output required'
assert len(json.loads((R1 / 'INDEX.json').read_text())['files']) == 31
for root in [R1, R2]:
    original = json.loads((root / 'INDEX.json').read_text())
    for row in original['files']:
        raw = (root / row['path']).read_bytes()
        assert len(raw) == row['bytes'] and digest(raw) == row['sha256']

sources = []
for label, root in [('r1', R1), ('r2', R2)]:
    sources += [(label + '/' + p.relative_to(root).as_posix(), p)
                for p in sorted(root.rglob('*')) if p.is_file()]
peer_names = [
    'OPENISSUE_TRIAGE_REFRESH_INITIAL_PEER.json',
    'OPENISSUE_TRIAGE_REFRESH_PEER.json',
    'OPENISSUE_TRIAGE_R2_NARROW_CORRECTION_PEER.json',
    'review_openissue_triage_refresh.py',
    'review_openissue_triage_refresh_v2.py',
]
sources += [('independent-peer/' + n, PEER / n) for n in peer_names]
sources += [('historical-catalog/' + n, CAT / n)
            for n in ['CATALOG.json', 'SUMMARY.json', 'HANDOFF.md']]
catalog = json.loads((CAT / 'CATALOG.json').read_text())
assert len(catalog['issues']) == 38
for issue in catalog['issues']:
    p = Path(issue['sourceJSON'])
    assert digest(p.read_bytes()) == issue['sourceSHA256']
    sources.append(('historical-issue-json/' + str(issue['number']) + '.json', p))
sources.append(('tools/pack_originals.py', Path(__file__).resolve()))
sources.append(('producer/REQUEST.json', BASE / 'producer/REQUEST.json'))
sources.append(('producer/INITIAL_LAUNCH_FAILURE.txt', BASE / 'INITIAL_LAUNCH_FAILURE.txt'))
assert len({name for name, _ in sources}) == len(sources)
OUT.mkdir()
notes = OUT / 'PACKAGING_NOTES.md'
notes.write_text('''本包保留 r1 的 #340 來源誤述、原 129 checks/finding1、reviewer 初版用詞誤判及 r2 的唯一更正和 19/0。
r1 的31項原 INDEX及 r2 INDEX均原樣包含。為讓本機盤點能讀到原 issue 全文，另收舊 catalog 與38件 captured JSON；沒有新 API分頁／目前 open狀態證明。
全部 member都是來源的完整 bytes；沒有產品、fixtures、Git objects、ELF或活躍測試目錄。peer原工具未保存的 OS pipes／r2 inline helper不事後捏造。
root common Git首次缺 body object的 show128與後續owner正文副本／原空stdout映射仍原樣保留，並非產品紅燈。
本包只封存唯讀分類證據，不代表產品gate、issue關閉或PR合併；沒有重審／重測或變更分類。
''')
sources.append(('PACKAGING_NOTES.md', notes))
entries = []
payloads = {}
for name, path in sources:
    st = path.lstat()
    assert stat.S_ISREG(st.st_mode), str(path)
    raw = path.read_bytes()
    entries.append({'member': name, 'source_path': str(path), 'bytes': len(raw),
                    'sha256': digest(raw), 'mode': stat.S_IMODE(st.st_mode),
                    'mtime_ns': st.st_mtime_ns})
    payloads[name] = raw
inventory = {'schema': 'openissue-triage-complete-originals/1',
             'source_member_count': len(entries), 'entries': entries,
             'r1_error_retained': True, 'r2_correction_only': True,
             'subject_executed': False, 'issue_or_pr_writes': False}
inventory_raw = (json.dumps(inventory, ensure_ascii=False, indent=2) + '\n').encode()
archive = OUT / 'openissue-r1-r2-originals-and-independent-peers.tar.gz'
with tarfile.open(archive, 'w:gz') as tar:
    for row in entries:
        info = tarfile.TarInfo(row['member'])
        info.size = row['bytes']; info.mode = row['mode']
        info.mtime = row['mtime_ns'] // 1000000000
        tar.addfile(info, io.BytesIO(payloads[row['member']]))
    info = tarfile.TarInfo('MEMBER_INVENTORY.json')
    info.size = len(inventory_raw); info.mode = 0o600
    tar.addfile(info, io.BytesIO(inventory_raw))
expected = {r['member']: r for r in entries}
with tarfile.open(archive, 'r:gz') as tar:
    members = tar.getmembers()
    assert len(members) == len(entries) + 1
    assert len({m.name for m in members}) == len(members)
    for member in members:
        assert member.isfile() and not member.issym() and not member.islnk()
        raw = tar.extractfile(member).read()
        if member.name == 'MEMBER_INVENTORY.json':
            assert raw == inventory_raw
        else:
            row = expected[member.name]
            assert len(raw) == row['bytes'] and digest(raw) == row['sha256']
            assert raw == Path(row['source_path']).read_bytes()
dump(OUT / 'INDEX.json', inventory)
result = {'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'archive': str(archive), 'archive_bytes': archive.stat().st_size,
          'archive_sha256': digest(archive.read_bytes()), 'members': len(entries) + 1,
          'original_member_bytes': sum(r['bytes'] for r in entries),
          'roundtrip_all_member_bytes': True, 'original_source_bytes_unchanged': True,
          'index': str(OUT / 'INDEX.json'), 'index_sha256': digest((OUT / 'INDEX.json').read_bytes()),
          'exit_code': 0, 'no_source_or_classification_changes': True}
dump(OUT / 'RESULT.json', result)
print(json.dumps(result, ensure_ascii=False))
