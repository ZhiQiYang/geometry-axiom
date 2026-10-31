from pathlib import Path
import datetime, hashlib, importlib.util, json, os, re, shutil

# Root executes this evidence-only publisher after final package/peer pins are filled.
R = Path('/workspace/geometry-axiom')
L = '7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
BEFORE = '6d26aaaa9eade6ac3fdeba7a7d2d1e0291d72119'
O = Path('/workspace/geo337-maintenance-mapping-publication')
B = Path('evidence/geo337-train-20261024')
ROUND2 = Path('/workspace/terminal-storage-maintenance-round2-originals-20261024')
ROUND2_OUTER = Path('/workspace/terminal-storage-maintenance-round2-collection-launch-20261024')
MAPPING = Path('/tmp/train337-native-r1-special-coverage-mapping')
ISSUES = Path('/workspace/open-issue-triage-originals-publication-20261024')
NEW = Path('/workspace/cold212-and-sevenfinal15-originals-20261024')
NEW_OUTER = Path('/workspace/cold212-and-sevenfinal15-collection-launch-20261024')
ROUND2_PEER = Path('/workspace/train337-canvas-peer-resume/ROUND2_MAINTENANCE_PACKAGE_PEER.json')
NEW_PEER = Path('/workspace/train337-canvas-peer-resume/COLD212_SEVENFINAL15_PACKAGE_PEER.json')
PENDING_PINS = False

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

PINS = {
    ROUND2 / 'terminal-storage-maintenance-round2-originals.tar.gz': '6b43f60093971b791838c969133984fef91e3fb025f01b0a87628ba44e9d16c6',
    ROUND2 / 'INDEX.json': '4ea6a32f9eb28d854a7f3e832f51da64115e072b4c77f4f328e289a05243d444',
    ROUND2_PEER: '1420318071348aeffa24d1d5f3a5cfc344c4250d00d24ff4b5ad54f8a3631f8a',
    NEW / 'cold212-and-sevenfinal15-originals.tar.gz': '0e96fa4a6b07fa9b9d54cfc0821c7b92a40f1ddb0b03c07f4d918d6361f75cc4',
    NEW / 'MEMBER_INVENTORY.json': 'dd90dc1b126ed1317fedd7b408b28ad890305fe96a7868694609f1ecde87dd90',
    NEW_PEER: '6f4a287740ce852e2d2f4c8a1f8e4d7146a305fb60eb5867021f53ec75abe23e',
    NEW_PEER.parent / 'review_cold212_package.py': 'c2aacad1b5795c4c4fc65e06fbc5b60ff0922bad5ca5f386b63961823eb54939',
    ROUND2_PEER.parent / 'ROUND2_MAINTENANCE_PACKAGE_PEER.initial-schema-assumption.json': 'fec6280bccbd713a2df3ef0de5e79767a69b7ccdedcb88ad4913f94d6da94142',
    ROUND2_PEER.parent / 'review_round2_package.py': '404a4cf0b4f871f6047838f59d239b8f6abade8b4284dd011cb5fa2d56bd6013',
    ROUND2_PEER.parent / 'review_round2_package.v1.py.txt': '77b3993d90809310e2b3c54d1ac8a18dbbb4e9ad9b7ca5829ef3b5021cb17394',
    MAPPING / 'MAPPING.json': '412eaf03355f398857d00fd446085c504eca483cab3239223f15d4770cd9ce1f',
    Path('/tmp/train337-adversarial/FINAL_L_NATIVE_R1_SPECIFIC_COVERAGE_MAPPING_PEER.json'): 'e70ab7653a4f9182f6a272ba0a714ea9c44f6fcd0522d46ad51e2e45f007cde7',
    ISSUES / 'package/openissue-r1-r2-originals-and-independent-peers.tar.gz': 'fb43e78c03e176f4a700e6aa3481804d07b4c1081537522f3a3d12db70f3bbb9',
    ISSUES / 'package/INDEX.json': 'ff5550ef9c88137132d39e5f8be6759b4c153b83aaea5d571319560db80f8eb0',
    Path('/tmp/train337-adversarial/OPENISSUE_R1_R2_ORIGINAL_PACKAGE_PEER.json'): 'c7c97b4917135ce2f70000fa5e2d2680703cf8a343b040fd022a9a4ac0fd135b',
}
assert not PENDING_PINS, 'Preparation incomplete: new terminal package and independent peer pins required.'
assert not Path('/workspace/train337-native-L-7af8c5d8-r2-launch/receipt.json').exists(), 'Native terminal appeared: refresh current-state text before publication.'
assert not Path('/workspace/train337-L-q38-isolated-launch-7af8c5d8/RESULT.json').exists(), 'Q38 terminal appeared: refresh current-state text before publication.'
for path, pin in PINS.items():
    assert path.is_file() and not path.is_symlink(), path
    assert sha(path) == pin, path
mapping = json.loads((MAPPING / 'MAPPING.json').read_text())
assert mapping['L'] == L and mapping['checks'] == 52 and mapping['exitCode'] == 0
assert mapping['aggregateNative']['originalNativeExit'] == 1
assert mapping['314Node13']['separateNode13ProcessExit'] is None
for group in mapping['groups'].values():
    for module in group['modules']:
        assert module['directRecordedChildOSExit'] is None
        assert module['childOSExitSupportedByOriginalJudgeContract'] == 0
round2 = json.loads((ROUND2 / 'PACKAGE.json').read_text())
assert round2['exit_code'] == 0 and round2['member_count'] == 3101
round2_index = json.loads((ROUND2 / 'INDEX.json').read_text())
assert len(round2_index['actions']) == 27 and round2_index['maintenanceOnly'] is True
assert round2_index['productGateExecutedOrRelabeled'] is False
new_package = json.loads((NEW / 'PACKAGE.json').read_text())
assert new_package['exit_code'] == 0 and new_package['member_count'] == 26376
assert new_package['all_established_cold_alias_groups'] == 236
issues = json.loads((ISSUES / 'package/RESULT.json').read_text())
assert issues['exit_code'] == 0 and issues['members'] == 90
for peer_path in (ROUND2_PEER, NEW_PEER,
                  Path('/tmp/train337-adversarial/FINAL_L_NATIVE_R1_SPECIFIC_COVERAGE_MAPPING_PEER.json'),
                  Path('/tmp/train337-adversarial/OPENISSUE_R1_R2_ORIGINAL_PACKAGE_PEER.json')):
    peer = json.loads(peer_path.read_text())
    assert peer['exit_code'] == 0 and peer['findings'] == [], peer_path

O.mkdir()
p = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert sha(p) == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
s = importlib.util.spec_from_file_location('cap', p)
c = importlib.util.module_from_spec(s)
s.loader.exec_module(c)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0')
env.pop('PYTHONOPTIMIZE', None)
rec = c.Recorder(O, env, L)
def git(*args):
    row, out, err = rec.run(['git', *args], cwd=R, timeout=None, check=False,
                            source_variant='evidence-only-terminal-maintenance-and-historical-mapping')
    assert row['actual_process_returncode'] == 0, (args, err)
    return out.decode().strip()
assert git('rev-parse', 'HEAD') == BEFORE
assert git('branch', '--show-current') == 'codex/train-337-continue-20261024'
assert not git('status', '--porcelain=v1', '--untracked-files=all')
staged = []
def copy_file(source, relative):
    source = Path(source)
    assert source.is_file() and not source.is_symlink(), source
    target = B / relative
    assert not (R / target).exists(), target
    (R / target).parent.mkdir(parents=True, exist_ok=True)
    if source.name.endswith('.tar.gz'):
        blob = git('hash-object', '-w', str(source))
        git('update-index', '--add', '--cacheinfo', '100644', blob, str(target))
        git('update-index', '--skip-worktree', str(target))
    else:
        shutil.copyfile(source, R / target)
        assert sha(source) == sha(R / target), source
        staged.append(str(target))
def copy_tree(source, relative):
    source = Path(source)
    assert source.is_dir() and not source.is_symlink(), source
    for item in sorted(source.rglob('*')):
        assert not item.is_symlink(), item
        if item.is_dir():
            continue
        copy_file(item, Path(relative) / item.relative_to(source))

copy_tree(ROUND2, 'terminal-maintenance-round2-originals/package')
copy_tree(ROUND2_OUTER, 'terminal-maintenance-round2-originals/collector-outer')
# The full new inventory is already an exact member of the fixed archive.
# Keep one public copy there instead of duplicating the large index outside it.
for name in ('PACKAGE.json', 'cold212-and-sevenfinal15-originals.tar.gz'):
    copy_file(NEW / name, Path('terminal-maintenance-212-plus-15-originals/package') / name)
copy_tree(NEW_OUTER, 'terminal-maintenance-212-plus-15-originals/collector-outer')
# Peer/helper source lists for the new maintenance packages are fixed before execution.
MAINTENANCE_PEER_FILES = [
    (ROUND2_PEER, Path('terminal-maintenance-round2-originals/package-peer') / ROUND2_PEER.name),
    (ROUND2_PEER.parent / 'ROUND2_MAINTENANCE_PACKAGE_PEER.initial-schema-assumption.json', Path('terminal-maintenance-round2-originals/package-peer/ROUND2_MAINTENANCE_PACKAGE_PEER.initial-schema-assumption.json')),
    (ROUND2_PEER.parent / 'review_round2_package.py', Path('terminal-maintenance-round2-originals/package-peer/review_round2_package.py')),
    (ROUND2_PEER.parent / 'review_round2_package.v1.py.txt', Path('terminal-maintenance-round2-originals/package-peer/review_round2_package.v1.py.txt')),
    (NEW_PEER, Path('terminal-maintenance-212-plus-15-originals/package-peer') / NEW_PEER.name),
    (NEW_PEER.parent / 'review_cold212_package.py', Path('terminal-maintenance-212-plus-15-originals/package-peer/review_cold212_package.py')),
]
for source, relative in MAINTENANCE_PEER_FILES:
    copy_file(source, relative)

copy_tree(MAPPING, 'final-L-native-r1-special-coverage')
for source in (Path('/tmp/extract_L_native_r1_coverage_mapping.py'),
               Path('/tmp/train337-adversarial/review_native_r1_scope_mapping.py'),
               Path('/tmp/train337-adversarial/FINAL_L_NATIVE_R1_SPECIFIC_COVERAGE_MAPPING_PEER.json')):
    copy_file(source, Path('final-L-native-r1-special-coverage') / source.name)
copy_tree(ISSUES / 'package', 'open-issue-triage-originals/package')
copy_tree(ISSUES / 'producer', 'open-issue-triage-originals/producer')
copy_file(ISSUES / 'INITIAL_LAUNCH_FAILURE.txt', 'open-issue-triage-originals/INITIAL_LAUNCH_FAILURE.txt')
copy_tree(ISSUES / 'tools', 'open-issue-triage-originals/tools')
for source in (Path('/tmp/train337-adversarial/OPENISSUE_R1_R2_ORIGINAL_PACKAGE_PEER.json'),
               Path('/tmp/train337-adversarial/review_openissue_original_package.py'),
               Path('/tmp/train337-adversarial/review_openissue_original_package_v2.py')):
    copy_file(source, Path('open-issue-triage-originals/package-peer') / source.name)
copy_file(Path(__file__).resolve(), 'terminal-maintenance-212-plus-15-originals/publish_geo337_maintenance_mapping.py')

p = R / B / 'PROGRESS.md'
t = p.read_text()
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
t, n = re.subn(r'## 唯一 current-state（[^\n]+）', '## 唯一 current-state（' + now + '）', t, count=1)
assert n == 1
old = '§7 compiled0／axiom0，完整原件已公開；P52／Q38／P-189 UNRUN'
new = '§7 compiled0／axiom0，完整原件已公開；Q38 RUNNING（僅雲端、無終態判決）；P52／P-189 UNRUN'
assert t.count(old) == 1
t = t.replace(old, new, 1)
t += '\n## ' + now + '：終態維護完整原件、native切片映射與issue盤點封存\n\n'
t += ('原27項終態維護完整3101-member包、collector最外argv／環境／完整streams及退出碼，封於terminal-maintenance-round2-originals；原source SHA逐項保留，不把維護capture綁定的L當成所有歷史工作來源。包括95＋37普通終態ELF退休、receipt保真去重、4個外部index退休、第二組raw保真跨filesystem搬移、12＋15普通ELF退休。原失敗、修正、工具、原PLAN、側車與既有對抗審查皆保。12側車使用退休時已核原hash的凍結副本，沒有把native R2重建後的cache冒成原收據。跨filesystem搬移只轉移占用，不能算全機節省。維護不是產品gate。\n\n')
t += ('新增212組三份相同archive保真hardlink去重與seven-final舊15個普通ELF退休的原命令／退出碼／完整streams／原來源／PLAN／peer，封於terminal-maintenance-212-plus-15-originals。新212加既有24，共236組archive aliases；/workspace/geo261-cold/g261seal/{p-source,a-source,l-source}三個cold checkout一律禁寫，所有alias完全脫鉤前不可啟動測試或修改來源。收據、fixtures、Git objects與受控mutant／trace／withdrawn來源均保留；普通可重建ELF退休不算測試成功，未移標原歷史判決。\n\n')
t += ('final-L-native-r1-special-coverage保存原52項映射核對、三份L原Git來源、extractor及獨立122核對：#314六完整Python module共103、閱讀A兩module21、#323三module50原row與完整unittest log皆pass。Python child0僅原裁判契約支持，per-child OS欄位原本未保存而明列null；Node inspector13是失敗Node737中的13個通過事件，沒有獨立Node13 exit0。完整native r1／workflow／outer仍1，四個ENOENT未改判；此映射不替代完整native、專項或性能。\n\n')
t += ('open-issue-triage-originals封原90-member／1,482,357原bytes的534,257B小包及producer完整原流、初始outer未mkdir的準備1、286獨審與初helper錯誤。38個issue全文是既有歷史capture，不冒最新完整GitHub清單。r1把#340誤說已在L的finding1及r2修正均保：#340原獨立13項不在L原11項中；#214與#300仍是部分切片，不能宣稱母issue結案。沒有寫issue狀態或碰Grok分支。\n\n')
t += ('draft #346已由本機橋接開出，沒有重複請求。native R2及Q38仍待原正式終態；Q38環境物化0不算產品通過，啟動紀錄目前僅雲端。P52、P-189與#323其餘專項繼續排程；B1／B2／B3仍未解除，沒有READY-TO-MERGE。\n')
p.write_text(t)
staged.append(str(B / 'PROGRESS.md'))
git('add', '-f', '--sparse', *staged)
assert all(name.startswith(str(B) + '/') for name in git('diff', '--cached', '--name-only').splitlines())
git('diff', '--cached', '--check')
git('commit', '-m', 'docs: preserve terminal maintenance and acceptance coverage evidence')
E = git('rev-parse', 'HEAD')
git('push', 'origin', 'HEAD:codex/train-337-continue-20261024')
assert git('ls-remote', 'origin', 'refs/heads/codex/train-337-continue-20261024').split()[0] == E
result = dict(source_sha=L, previous_evidence_head=BEFORE, evidence_head=E,
              published=True, push_exit=0, maintenance_is_product_gate=False,
              native_r1_exit_unchanged=1, new_product_gate_claim=False,
              archive_alias_groups=236, cold_roots_write_banned=True)
c.dump(O / 'RESULT.json', result)
print(json.dumps(result))
