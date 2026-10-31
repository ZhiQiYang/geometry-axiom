from pathlib import Path
import datetime, hashlib, importlib.util, json, os, re, shutil

# Root-only publication. No subject, build, archive creation, or cache access.
R = Path('/workspace/geometry-axiom')
L = '7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
BEFORE = '732ac159043ab311fd66e338c21d33f322f6e968'
BRANCH = 'codex/train-337-continue-20261024'
B = Path('evidence/geo337-train-20261024')
O = Path('/workspace/geo337-required8-pf3-publication')
S = Path('/workspace/train337-final-required8-pf3-collection')
P = Path('/workspace/train337-canvas-peer-resume')
CASES = {
    'required-eight': dict(archive='81937992087ce136bdc34ece9d9da468e05beba5c931add719c9fb2501e661e4',
                          bytes=2063262, members=841,
                          inventory='b71ba19597cece10c8f807f62aec71e0d213be8ff2630d51898184a74f282ac6',
                          peer='REQUIRED8_ACTUAL_PACKAGE_PEER.json',
                          peer_hash='a2efd495495ffa716fa165f9673b7dcd913e08688b0dad6aaaa8e320d5b4c19d'),
    'pf3': dict(archive='fb3fc268318ec6844433fb35ef6a0c2dc1f72715f11f52d1417e633e068bd127',
                bytes=14686234, members=4759,
                inventory='c9fd3d048f73a79e6cec8aa281356ac3c1bb2ce0f4ac84ac090a527cc7deecd0',
                peer='PF3_ACTUAL_PACKAGE_PEER.json',
                peer_hash='817aeb05512c561df35d2e2c95a2331cb38fde6b07f0bccd19e5199f2966aa38'),
}
TOOL_PINS = {
    S / 'collect_original_nonperf.py': 'ce93f88fa5bd8f409977adf7731dcbd418f286afe64838ec3e2d5cad80acfeb4',
    S / 'PREPARATION.json': '441a8af3cfe51845c3a8c120903558c18735fb15c6c960e56aeb10614057c604',
    S / 'COLLECTOR_DIFF.patch': 'f1c6a031832cd37c8b97111ab286d0af2daa4aaaccb0467b94697f405ffbd105',
    S / 'prepare_minimal_collector.py': '419491fbba415d25d3e485b1e5bf4bde7ca1127dc0708936df63f8845c24da86',
    S / 'launch_collection.py': '1a5aec0bc693c400e7b603c77a335c807900fcd1c00bde21f0acbd7c42439a93',
    P / 'REQUIRED8_PF3_COLLECTOR_STATIC_PEER.json': '844814f17219ac00ac1c42c845916fdb7144912982429eec87ae5dd622353d59',
    P / 'review_required8_pf3_collector.py': '5434ac3b850a9b404d3a24d6ec0d1b1bc9ae5a65cc7d54eac4c48203a9330cce',
    P / 'review_required8_actual.py': 'dbba3b24a203250e9ac83aca72eeda38f5e629db6b751cb969c5ce761336afb8',
    P / 'review_required8_actual.v1.py.txt': 'b86fce11c589d8ca8b7f940a98777b345968cefe32ff45307cbd1e29403726a0',
    P / 'REQUIRED8_ACTUAL_PACKAGE_PEER.initial-schema-assumptions.json': '0caf426791cb5f6655efb3542f3761d0ef3b1a637aa97a0efc1d261cd1c18c60',
    P / 'review_pf3_actual.py': 'a9ae312353a998fade0f05d840d2820b74afd3fc1bae478aad2dac4902e121b5',
    P / 'PF3_ORIGINAL_L_TREE.COMMAND.json': '67d661f0304d119ea15b377426c2454f6a93e7f92fc2a5f20b2d531d2a6a830b',
    P / 'PF3_ORIGINAL_L_TREE.stdout.bin': '571b9d5c2cb0c65bc99ffa806fb3871004e648ad49de985c5357779b729dc910',
    P / 'PF3_ORIGINAL_L_TREE.stderr.bin': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    P / 'V4_OUTER_SOURCE_ROLE_DIAGNOSTIC.json': '5425a7ad9bede750c218798fb550b71e92a5320ddb16f519e5d8a02363b95185',
    P / 'diagnose_v4_outer_source_role.py': '0a579bdfa5eefe87607ae888801d32bff2e3b0369292a194a109f46e40f0022a',
}
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()
for path, pin in TOOL_PINS.items():
    assert path.is_file() and not path.is_symlink() and sha(path) == pin, path
for gate, spec in CASES.items():
    package = json.loads((S / gate / 'PACKAGE.json').read_text())
    summary = json.loads((S / gate / 'SUMMARY.json').read_text())
    archive = S / gate / 'ORIGINAL_NONPERF_LOGS_REPORTS_AND_ELF_HASHES.tar.gz'
    assert package['source_sha'] == summary['source_sha'] == L
    assert package['gate'] == summary['gate'] == gate
    assert package['archive']['sha256'] == spec['archive'] and package['archive']['members'] == spec['members']
    assert archive.stat().st_size == spec['bytes'] and sha(archive) == spec['archive']
    assert sha(S / gate / 'RAW_INVENTORY.json') == spec['inventory']
    assert summary['original_exit'] == summary['driver_exit'] == summary['outer_exit'] == 0
    assert summary['original_passed'] is True and summary['source_before'] == summary['source_after']
    assert summary['source_before']['head'] == L and summary['source_before']['status'] == ''
    peer = P / spec['peer']
    assert sha(peer) == spec['peer_hash']
    d = json.loads(peer.read_text())
    assert d['exit_code'] == 0 and d['findings'] == [] and d['source_sha'] == L
    assert d['archive_sha256'] == spec['archive'] and d['archive_members'] == spec['members']
    outer = json.loads((S / (gate + '-collection-launch') / 'RESULT.json').read_text())
    assert outer['actual_process_returncode'] == 0 and outer['source_sha'] == L

O.mkdir()
cp = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert sha(cp) == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec = importlib.util.spec_from_file_location('cap', cp)
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0'); env.pop('PYTHONOPTIMIZE', None)
rec = c.Recorder(O, env, L)
def git(*args):
    row, out, err = rec.run(['git', *args], cwd=R, timeout=None, check=False,
                            source_variant='evidence-only-final-L-required-eight-PF3')
    assert row['actual_process_returncode'] == 0, (args, err)
    return out.decode().strip()
assert git('rev-parse', 'HEAD') == BEFORE and git('branch', '--show-current') == BRANCH
assert not git('status', '--porcelain=v1', '--untracked-files=all')
staged = []
def copy_file(source, relative):
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
    for path in sorted(source.rglob('*')):
        assert not path.is_symlink(), path
        if path.is_file():
            copy_file(path, Path(relative) / path.relative_to(source))
for gate, spec in CASES.items():
    for name in ('PACKAGE.json', 'SUMMARY.json', 'INNER_COMMANDS.json', 'RAW_INVENTORY.json',
                 'EXCLUDED_ELF_PAYLOADS.json', 'ORIGINAL_NONPERF_LOGS_REPORTS_AND_ELF_HASHES.tar.gz'):
        copy_file(S / gate / name, Path('final-L-' + gate + '-complete') / name)
    copy_tree(S / (gate + '-collection-launch'), 'final-L-' + gate + '-complete/collector-outer')
    copy_file(P / spec['peer'], Path('final-L-' + gate + '-complete') / spec['peer'])
for source in TOOL_PINS:
    copy_file(source, Path('final-L-required-eight-pf3-tools-and-peer') / source.name)
copy_file(Path(__file__), Path('final-L-required-eight-pf3-tools-and-peer') / Path(__file__).name)

progress = R / B / 'PROGRESS.md'
t = progress.read_text()
old = 'required-eight原exit0／PF3原exit0（小RESULT已封，完整包待）；timing／profile／memo UNRUN'
assert t.count(old) == 1
t = t.replace(old, 'required-eight原exit0／PF3原exit0，完整原件包已封；timing／profile／memo UNRUN', 1)
old = '依最新C1，正文D5bc暫不再發布中間版本，native真終態已到，將與已完成canvas一併重寫PR唯一矩陣；這次提交不自動更新正文；'
assert t.count(old) == 1
t = t.replace(old, '依最新C1，canvas／native終態後已更新正文Da26b2a18（完整SHA a26b2a18dbb0b7746726716046f9a1039365e81a），唯一矩陣綁E732；本次再公開R8/PF3完整包，該正文中的status-only是當時狀態，後續由root更新；', 1)
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
t = re.sub(r'## 唯一 current-state（[^\n]+）', '## 唯一 current-state（' + now + '）', t, count=1)
t += ('\n## ' + now + '：required-eight／PF3完整原件公開\n\n'
      '同L兩項原CLI／nested wrapper／stage／driver／outer均0。required-eight原八列676個登記單位全部通過且零skip；676混合Python tests、C檢查點與core場景，不是676個unittest方法。原runner複製619份global suite-log，包含歷史未選項；只按當次--only八項argv與八列原stdout計數。841-member完整包2,063,262B／SHA256 81937992087ce136bdc34ece9d9da468e05beba5c931add719c9fb2501e661e4封於final-L-required-eight-complete。\n\n'
      'PF3原baseline20全部通過，19刀各命中指定方法與marker的正常AssertionError exit1，restored20全部通過；原21次build invocation皆0，產生42個binary，不虛構42份獨立compiler OS退出碼。4759-member完整包14,686,234B／SHA256 fb3fc268318ec6844433fb35ef6a0c2dc1f72715f11f52d1417e633e068bd127封於final-L-pf3-complete；42個ELF共42,641,000B留原地，只省略包內payload，保hash／側車／recipe。\n\n'
      '原v4 Recorder.role掃整串argv，遇--base設定而將兩項orchestration外層source_role/source_sha誤標base b74f9a2；原欄位與streams不回寫。acceptance_sha、顯式--sha L、真正subject inner與執行前後Git guards獨立綁定L，不能概稱所有source_sha欄皆L，也不能把base標籤當成實跑base。V4_OUTER_SOURCE_ROLE_DIAGNOSTIC與純role重現工具保此病因；未改原裁判或重跑subject。\n\n'
      '兩份collector外層完整命令／stdout／stderr／環境／exit及原工具均公開；R8初peer schema誤判與v1保歷史。獨立2768／19603核對0只驗原件，不算產品測試。舊status-only小RESULT保原樣；本批不移標其他性能、exact、CI或整體驗收，不新增skip、放寬斷言或時限。P52／P-189／#323 timing、profile、memo及L跨版本exact仍待原正式結果，B1/B2/B3尚未全解除，沒有READY-TO-MERGE。\n')
progress.write_text(t); staged.append(str(B / 'PROGRESS.md'))
git('add', '-f', '--sparse', *staged)
assert all(name.startswith(str(B) + '/') for name in git('diff', '--cached', '--name-only').splitlines())

# Preserve the original unified diff verbatim; retain any actual check exit.
row, out, err = rec.run(['git', 'diff', '--cached', '--check'], cwd=R, timeout=None, check=False,
                         source_variant='original-evidence-format-check')
if row['actual_process_returncode']:
    raw_path = str(B / 'final-L-required-eight-pf3-tools-and-peer/COLLECTOR_DIFF.patch')
    assert row['actual_process_returncode'] == 2 and not err
    diagnostics = [line for line in out.decode().splitlines() if re.match(r'.+:\d+: ', line)]
    assert diagnostics and all(re.fullmatch(re.escape(raw_path) + r':\d+: (trailing whitespace\.|new blank line at EOF\.)', line) for line in diagnostics)
    assert sha(R / raw_path) == TOOL_PINS[S / 'COLLECTOR_DIFF.patch']
    c.dump(O / 'VERBATIM_DIFF_FORMAT_EXCLUSION.json', {'path': raw_path, 'sha256': TOOL_PINS[S / 'COLLECTOR_DIFF.patch'], 'original_check_exit': 2})
    git('diff', '--cached', '--check', '--', '.', ':(exclude)' + raw_path)
git('commit', '-m', 'docs: publish complete required-eight and PF3 acceptance receipts')
E = git('rev-parse', 'HEAD')
git('push', 'origin', 'HEAD:' + BRANCH)
assert git('ls-remote', 'origin', 'refs/heads/' + BRANCH).split()[0] == E
result = dict(source_sha=L, previous_evidence_head=BEFORE, evidence_head=E, published=True,
              push_exit=0, required_eight_original_exit=0, pf3_original_exit=0,
              full_packages_published=True, prbody_unchanged=True)
c.dump(O / 'RESULT.json', result); print(json.dumps(result))
