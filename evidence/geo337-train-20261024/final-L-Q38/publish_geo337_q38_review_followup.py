from pathlib import Path
import datetime, hashlib, importlib.util, json, os, re, shutil

# Root-only publisher. Only the explicitly reviewed public Actions v2 files
# are admitted; private unredacted signed-log responses are never traversed.
R = Path('/workspace/geometry-axiom')
L = '7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
BEFORE = '935dc904c933a2c54e89848bc99436073e84fcd8'
O = Path('/workspace/geo337-q38-review-followup-publication')
B = Path('evidence/geo337-train-20261024')
Q = Path('/workspace/train337-q38-terminal-collection')
QP = Path('/workspace/train337-q38-terminal-collection-producer')
REV = Path('/workspace/geo337-review-followup-f05-preparation-20261024')
N = Path('/workspace/train337-native-r2-terminal-collection/completed')
NP = Path('/workspace/train337-native-r2-terminal-collection-producer')
N_PEER = Path('/workspace/train337-canvas-peer-resume/FINAL_L_NATIVE_R2_ACTUAL_PACKAGE_PEER.json')
Q_PEER = Path('/workspace/train337-canvas-peer-resume/FINAL_L_Q38_ACTUAL_PACKAGE_PEER.json')
ACTIONS = Path('/workspace/pr338-pr339-current-actions-publication-v2-20261024')
ACTIONS_PEER = Path('/workspace/train337-canvas-peer-resume/CURRENT_ACTIONS_SAFE_PACKAGE_PEER.json')
PENDING_PEERS = False
PINS = {
    N / 'ORIGINAL_FULL_NATIVE_WORKFLOW_LOGS_AND_RUNTIME_SIDECARS.tar.gz': 'f9c5ca6b5d6b368a52657aff6ac73b4b7b31195973d840e1f99180eae4e0efde',
    N / 'RAW_INVENTORY.json': 'a12c4db628adbe0d887723b328a34cb0242452a9851422a0cfaa1509270b4f62',
    N_PEER: '9849acd9bdd2ec43ed240a1bd923c672a4c3d187ef92ebc9403471b8e7ec58de',
    Q / 'ORIGINAL_Q38_OUTPUTS_MATERIALIZATION_AND_TOOL_PINS.tar.gz': 'acbf826d08488d4d678c68004d0c5e9e5979d0ba05951f5926dc73a6a28a1690',
    Q / 'RAW_INVENTORY.json': 'ddfde6d17da329666ddc2af0278a646e76822fc2e6b69b9c6cfc9a281af29e3a',
    REV / 'PREPARATION.json': '77b16c64954b2f2795073e6d4811d65036158838fdbf97249218cd9456134c2d',
    REV / 'PROGRESS.draft.md': '12048af25e59c67b9e45e49663216f2225c22db30fd12ed83738754f9e444b53',
    Path('/workspace/prepare_geo337_review_followup_f05.py'): '4e60f5836012bc52f98dc2ff375066d0418e5f198095fc34fa5d598b5386e242',
    Q_PEER: '1a1c32016056ea9899245292bc5b0d9a08f83f8edfadb689848c6b105a4798ed',
    Q_PEER.parent / 'review_q38_actual.py': 'a48686d4027ef09c09711dcb140851c238fb0f4f5172aa7b4aad8ac3a89ab743',
    Q_PEER.parent / 'Q38_ORIGINAL_L_SOURCE.py.txt': '3004734c4e1052e95d3234091bc8fb03c20cf7546282432704fca0a07071ee6c',
    Q_PEER.parent / 'Q38_ORIGINAL_L_SOURCE_COMMAND.json': 'c479ac67bff79a912ad4b50813b3ac5cc0606d0bf6039cc61a4ff8c7e15d980d',
    ACTIONS / 'current-actions-and-complete-source-binding-with-explicit-redactions.tar.gz': '40567a58ce19e563245b109736ee1417a28e8d77308ce0027df19dfc6fd361c8',
    ACTIONS / 'PUBLIC_REDACTIONS.json': '29452ec5766d7383fa90ef04abe30fd2833b1ca81175a6b9c8004e5452d8b6e5',
    ACTIONS_PEER: '50a59abac96c3f36af5aea9520596715455e15137ec97c0b00afa7309b1e493a',
    ACTIONS_PEER.parent / 'review_current_actions_safe_package.py': 'ed068e1568cbf3548ec67185a13be1fa09f5ca0fcff620d22a64ac4816a4f2c9',
    ACTIONS_PEER.parent / 'CURRENT_ACTIONS_SAFE_PACKAGE_PEER.initial-schema-assumptions.json': 'bcb1bef99a7dcca1af3ed2a4bd27d12f413686e6bc7cd3e02d748df350d0e2c6',
    ACTIONS_PEER.parent / 'review_current_actions_safe_package.v1.py.txt': 'e4802a18e22d8d84486e763b0fffe5116cd25046c433304fc48964fb7ff43082',
}
RAW_WHITESPACE_PINS = {
    '339-all-original.md': 'dcafc57f309a7b65bea083fddce5c0b9db93a9cd182fb7d95b46a0b469b8df36',
    '339-latest-review-excerpt.md': '52ee0d882eaa1a2997e37545518a1005291108a7d18ead371e4482001a88b4fe',
    '338-latest-review-excerpt.md': '2503baf167d08cb1c075591a22a1dda2cd0cc289b2f2651ec4fd130df85c4a5b',
    '338-all-original.md': 'dc7fa1048d52f215aef967ac8a5f8081a1f68e5969f3200d431394b8568ab206',
    'PROGRESS.review-only.diff': 'e043533883015b74461f5f1a7173692c59e3ffddcf0b7ae4a264f50687fc6ff8',
    'NEXT.review-only.diff': '09306ad85331293d8eccf61f9dc5af896f76844bcf7d41c4ff95a4995c411a28',
    'source-capture/subcommands/000002/stdout.bin': 'dcafc57f309a7b65bea083fddce5c0b9db93a9cd182fb7d95b46a0b469b8df36',
    'source-capture/subcommands/000001/stdout.bin': 'dc7fa1048d52f215aef967ac8a5f8081a1f68e5969f3200d431394b8568ab206',
}
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()
assert not PENDING_PEERS, 'Preparation incomplete: accepted package and review-followup peer pins required.'
for path, pin in PINS.items():
    assert path.is_file() and not path.is_symlink(), path
    assert sha(path) == pin, path
for relative, pin in RAW_WHITESPACE_PINS.items():
    assert sha(REV / relative) == pin, relative
native_package = json.loads((N / 'PACKAGE.json').read_text())
native_summary = json.loads((N / 'SUMMARY.json').read_text())
assert native_package['sourceSHA'] == L and native_package['memberCount'] == 1366
assert native_package['originalNativeExit'] == native_package['workflowExit'] == native_package['CI35GateExit'] == native_package['outerExit'] == 0
assert native_summary['passed'] is True and native_summary['metadataErrors'] == []
package = json.loads((Q / 'PACKAGE.json').read_text())
summary = json.loads((Q / 'SUMMARY.json').read_text())
assert package['source_sha'] == L and package['archive']['members'] == 449
assert package['archive']['sha256'] == PINS[Q / 'ORIGINAL_Q38_OUTPUTS_MATERIALIZATION_AND_TOOL_PINS.tar.gz']
assert summary['source_sha'] == L and summary['original_passed'] is True
assert summary['driver_exit'] == summary['outer_exit'] == summary['execution_capture_exit'] == 0
assert summary['original_case_count'] == 42 and summary['original_summary'] == {'killed': 41, 'equivalent': 1}
for name, count in [('native', 27), ('model', 20)]:
    baseline = summary['original_baselines'][name]
    assert baseline['exit'] == 0
    assert len(baseline['exception_evidence']['executed']) == count
    assert baseline['exception_evidence']['skipped'] == 0
actions_package = json.loads((ACTIONS / 'PACKAGE.json').read_text())
assert actions_package['exit_code'] == 0 and actions_package['member_count'] == 365
assert actions_package['command_count'] == 65 and actions_package['command_exit_counts'] == {'0': 63, '1': 2}
assert actions_package['public_redactions'] == 2 and actions_package['all_other_public_bytes_match_originals'] is True
for peer_path in (N_PEER, Q_PEER, ACTIONS_PEER):
    peer = json.loads(peer_path.read_text())
    assert peer['exit_code'] == 0 and peer['findings'] == [], peer_path
STATUS_PATHS = {gate: Path('/workspace/train337-final-L-' + gate + '-7af8c5d8-launch/RESULT.json')
                for gate in ('required-eight', 'pf3')}
status = {}
for gate, path in STATUS_PATHS.items():
    assert path.is_file(), gate + ' has no terminal RESULT; do not publish a stale current state'
    raw = path.read_bytes()
    row = json.loads(raw)
    assert row['source_sha'] == L and row['gate'] == gate
    assert type(row['actual_exit']) is int
    assert row['command']['source_sha'] == L
    assert row['command']['actual_process_returncode'] == row['actual_exit']
    assert row['command']['ended_epoch'] >= row['command']['started_epoch']
    status[gate] = dict(source_sha=L, actual_exit=row['actual_exit'],
                        original_path=str(path), sha256=hashlib.sha256(raw).hexdigest(),
                        complete_original_package_published_here=False)

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
                            source_variant='evidence-only-final-L-Q38-and-latest-review-followup')
    assert row['actual_process_returncode'] == 0, (args, err)
    return out.decode().strip()
assert git('rev-parse', 'HEAD') == BEFORE
assert git('branch', '--show-current') == 'codex/train-337-continue-20261024'
assert not git('status', '--porcelain=v1', '--untracked-files=all')
assert (R / B / 'PROGRESS.md').read_bytes() == (REV / 'PROGRESS.original.md').read_bytes()
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
for name in ('PACKAGE.json', 'SUMMARY.json', 'RAW_INVENTORY.json', 'EXCLUDED_ELF_PAYLOADS.json', 'ORIGINAL_Q38_OUTPUTS_MATERIALIZATION_AND_TOOL_PINS.tar.gz'):
    copy_file(Q / name, Path('final-L-Q38') / name)
copy_tree(QP, 'final-L-Q38/collector-outer')
for name in ('PACKAGE.json', 'SUMMARY.json', 'RAW_INVENTORY.json', 'BUDGET.json', 'ORIGINAL_FULL_NATIVE_WORKFLOW_LOGS_AND_RUNTIME_SIDECARS.tar.gz'):
    copy_file(N / name, Path('final-L-native-r2-complete') / name)
copy_tree(NP, 'final-L-native-r2-complete/collector-outer')
for source in (Path('/workspace/train337-native-r2-terminal-collection/collect_terminal_native.py'),
               Path('/workspace/train337-native-r2-terminal-collection/PREPARATION.json'),
               Path('/workspace/launch_collect_geo337_native_r2.py')):
    copy_file(source, Path('final-L-native-r2-complete/collection-tools') / source.name)
copy_tree(REV, 'review-f05-e9-originals-and-preparation')
copy_file(Path('/workspace/prepare_geo337_review_followup_f05.py'), 'review-f05-e9-originals-and-preparation/prepare_geo337_review_followup_f05.py')
for name in ('PACKAGE.json', 'PUBLIC_REDACTIONS.json', 'current-actions-and-complete-source-binding-with-explicit-redactions.tar.gz'):
    copy_file(ACTIONS / name, Path('actions-f05-e9-environment-public-v2') / name)
PEER_FILES = [(Q_PEER.parent / name, Path('final-L-Q38/independent-peer') / name) for name in (
    'FINAL_L_Q38_ACTUAL_PACKAGE_PEER.json', 'review_q38_actual.py',
    'Q38_ORIGINAL_L_SOURCE.py.txt', 'Q38_ORIGINAL_L_SOURCE.stderr.bin', 'Q38_ORIGINAL_L_SOURCE_COMMAND.json')]
PEER_FILES += [(ACTIONS_PEER.parent / name, Path('actions-f05-e9-environment-public-v2/independent-peer') / name) for name in (
    'CURRENT_ACTIONS_SAFE_PACKAGE_PEER.json', 'review_current_actions_safe_package.py',
    'CURRENT_ACTIONS_SAFE_PACKAGE_PEER.initial-schema-assumptions.json', 'review_current_actions_safe_package.v1.py.txt')]
PEER_FILES += [(N_PEER.parent / name, Path('final-L-native-r2-complete/independent-peer') / name) for name in (
    'FINAL_L_NATIVE_R2_ACTUAL_PACKAGE_PEER.json', 'review_native_r2_actual.py',
    'review_native_r2_actual.v1.py.txt', 'NATIVE_R2_PEER_INITIAL_PRODUCER_SCHEMA_ERROR.json',
    'NATIVE_R2_COLLECTOR_STATIC_PEER.json')]
for source, relative in PEER_FILES:
    copy_file(source, relative)
copy_file(Path(__file__).resolve(), 'final-L-Q38/publish_geo337_q38_review_followup.py')
for gate, path in STATUS_PATHS.items():
    assert sha(path) == status[gate]['sha256']
    copy_file(path, Path('final-L-required-eight-pf3-status-only') / (gate + '-outer-RESULT.json'))
status_target = B / 'final-L-required-eight-pf3-status-only/STATUS_SNAPSHOT.json'
c.dump(R / status_target, dict(source_sha=L, statuses=status,
    scope='Original terminal outer command receipts only; no full raw package is claimed present here.'))
staged.append(str(status_target))

t = (REV / 'PROGRESS.draft.md').read_text()
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
t, n = re.subn(r'## 唯一 current-state（[^\n]+）', '## 唯一 current-state（' + now + '）', t, count=1)
assert n == 1
old = '| 完整 native | L | r1原exit1：4個ENOENT環境紅；同L三fixture已補齊、完整r2 RUNNING（啟動紀錄，無終態判決） | 原全230列／5309=5304pass+4fail+1原允許WindowsGDI skip，1873.241s<35min；原完整流封final-L-native-r1-environment-failure |'
new = '| 完整 native | L | r2原CLI／workflow／CI35／outer全0；r1環境1保歷史 | r2全230列，5309=5308pass+0fail+1原允許WindowsGDI skip；1819.561s<35min，Node737/737；完整原件封final-L-native-r2-complete；r1四ENOENT不改舊判 |'
assert t.count(old) == 1
t = t.replace(old, new, 1)
t = t.replace('| #323 required-eight／PF3／timing／profile／memo反證 | L | 全部UNRUN |',
              '| #323 required-eight／PF3／timing／profile／memo反證 | L | required-eight原exit' + str(status['required-eight']['actual_exit']) + '／PF3原exit' + str(status['pf3']['actual_exit']) + '（小RESULT已封，完整包待）；timing／profile／memo UNRUN |', 1)
t = t.replace('r2已於00:38 UTC啟動原完整重跑，ROOT與共用cache由native獨占', 'r2於00:38～01:09 UTC完成原完整重跑且原件／sidecar已封，獨審確認後ROOT與共用cache交還root排程', 1)
t = t.replace('現在canvas真0已封、r2仍RUNNING', '現在canvas真0已封、native r2真0與完整原件已同批封存', 1)
t = t.replace('待native真終態後與已完成canvas一併重寫唯一矩陣', 'native真終態已到，將與已完成canvas一併重寫PR唯一矩陣；這次提交不自動更新正文', 1)
old = '§7 compiled0／axiom0，完整原件已公開；Q38 RUNNING（僅雲端、無終態判決）；P52／P-189 UNRUN'
new = '§7 compiled0／axiom0；Q38原0／outer0，完整原件已公開；P52／P-189 UNRUN'
assert t.count(old) == 1
t = t.replace(old, new, 1)
old = '| 最新B3：Actions 40043471807 required jobs | head f05e7cf | 最新審查記七項failure；新run原始分類收集中 | 2026-10-24 00:39:37 UTC審查要求同head CI真啟動終態或正式替代流程；舊c6／40034196788分類只作歷史，不能解除新head B3 |'
new = '| 最新B3：Actions 40043471807 required jobs | head f05e7cf | 七項failure；新run原annotation已分類帳戶／支出環境阻擋 | 同批封新run原件及source binding；未取得CI真啟動終態或正式替代接受，B3仍未解除；舊c6／40034196788只作歷史 |'
assert t.count(old) == 1
t = t.replace(old, new, 1)
t = t.replace('這兩個run的原始API／annotation分類正在收集，未以舊run40034196788／40032957675的付款或支出限制證據移標新head，也未宣稱新CI有runner、已啟動或已通過。', '這兩個run的14份原annotation已逐項取得：付款失敗或支出上限，API不區分兩者。新run原件與source binding已同批封存，未以舊run40034196788／40032957675移標，也未宣稱新CI有runner、已啟動或已通過。', 1)
t = t.replace('新F38da的142 importer／三個predicate反證與aggregate native仍待正式驗收', '新F38da的142 importer原0與三個predicate各0/1/0已完成且actual peer6636/0；aggregate native仍未跑，這批不替其餘正式項移標或解除阻擋', 1)
t = t.replace('（2026-10-24 00:39 UTC評論；文件準備稿）', '（2026-10-24 00:39 UTC評論）', 1)
t += '\n## ' + now + '：同L原完整Q38終態0與最新f05／e9審查對照\n\n'
t += ('native R2原230列全部依expected完整執行，5309=5308pass＋0fail＋1原允許Windows GDI skip；Node737/737全通過，r1四個ENOENT已在同L補fixture後消除。原native CLI／workflow／CI35／outer皆0，00:38:48.178258～01:09:07.739721 UTC約1819.561秒，小於原35分鐘；沒有新增skip或放寬判準。final-L-native-r2-complete封1366-member／2,230,143B完整原包，SHA256 f9c5ca6b5d6b368a52657aff6ac73b4b7b31195973d840e1f99180eae4e0efde；原globalcache側車、完整已暴露streams、命令／環境／SHA與registry原Git bytes都在包內。6個普通ELF只省略payload，真hash與側車完整，原物件未刪；舊cache payload依原collector排除並保原保全manifest，不冒本輪輸出。collector不重跑subject，原7386獨審0只驗原件與來源；初peer誤讀producer schema的工具失敗亦保。\n\n')
t += ('Q38原42案例完整執行，41 killed＋SPM24原equivalent，native27／model20兩baseline原exit0、零skip；原CLI、環境driver、兩層outer均真0，00:44:33～00:57:50 UTC。原registry排除test_source_index_typed_closure_and_display_identity保持，不把原排除改稱新增skip或補成已跑；SPM38／40的原允許ModelError沿原判決，不把它冒FAIL或新增擊殺。沒有縮table、改斷言／golden／600或900秒子時限。\n\n')
t += ('final-L-Q38封449-member完整原包（4,717,550B，SHA256 acbf826d08488d4d678c68004d0c5e9e5979d0ba05951f5926dc73a6a28a1690），保原privatebridge／model-base環境driver、同L 22→565物化、原來源前後守門、兩outer、所有已暴露commands／退出碼／完整streams／環境／SHA，另保collector最外原流。兩個private ELF僅省略payload並保真hash、sidecar及原路徑；原TemporaryDirectory自行清理的突變payload未虛構仍在。此環境隔離不改產品／測試，不共用native R2 global cache。\n\n')
t += ('原handoff e393的#338 f05／#339 e9最新審查全文、精確摘錄、四條Git原流與最小文件補正封於review-f05-e9-originals-and-preparation；初excerpt guard把正文小標誤認下一留言造成準備1的原件亦保，僅修辨識日期comment界線後復用同四capture，沒有改審查原文。新Actions40043471807／40040764499的365-member安全公開包封於actions-f05-e9-environment-public-v2；65條原讀取為63 exit0＋2次log Forbidden exit1，14原annotation都明示付款失敗或支出上限，不能猜是哪一項。兩次signed-log回應僅遮罩signature查詢值，PUBLIC_REDACTIONS明列位置與原hash，未遮罩的完整原件留雲端；其他公開bytes保持原件，不冒所有原流完全未遮罩。只發布已審v2指定三檔及安全peer附件，未遍歷私有原件目錄。\n\n')
t += ('原四份完整Git tree與rawdiff顯示L7af→E935的260個變動路徑、F38→Ee9的20個變動路徑均為evidence/，所有非evidence path/blob相同；這是來源一致性證據，不把受測L／F換成CI evidence head，也不宣稱任何正式替代流程已接受。舊c6／47fd run分類只作歷史；最新兩run CI仍failure，B3不因分類或tree比對自行解除。\n\n')
t += ('依最新C1，canvas與native已全終態，原件／唯一GDI skip已核對；正文仍暫維持D5bc，接著由root一次更新唯一矩陣，不把舊中間正文冒成此批結果。root已在native收包與7386原件核對後交還cache，接續同L原required-eight及PF3；本批保存兩份真正終態outer RESULT：required-eight原exit' + str(status['required-eight']['actual_exit']) + '、PF3原exit' + str(status['pf3']['actual_exit']) + '，都保原command／環境／來源／stdout與stderr hash。這只是小原RESULT，完整原流／側車及專項包仍待另封，沒有冒稱已入庫。P52、P-189與#323性能／profile／memo仍UNRUN，B1／B2／B3未全解除，沒有READY-TO-MERGE。\n')
(R / B / 'PROGRESS.md').write_text(t)
staged.append(str(B / 'PROGRESS.md'))
git('add', '-f', '--sparse', *staged)
assert all(name.startswith(str(B) + '/') for name in git('diff', '--cached', '--name-only').splitlines())
row, raw_out, raw_err = rec.run(['git', 'diff', '--cached', '--check'], cwd=R, timeout=None, check=False,
                               source_variant='complete-format-check-preserving-verbatim-review-bytes')
if row['actual_process_returncode'] != 0:
    assert row['actual_process_returncode'] == 2 and not raw_err
    allowed = {str(B / 'review-f05-e9-originals-and-preparation' / name) for name in RAW_WHITESPACE_PINS}
    reported = set()
    for line in raw_out.decode().splitlines():
        if line.startswith('+'):
            continue
        match = re.fullmatch(r'(.+):[0-9]+: (trailing whitespace|new blank line at EOF)\.', line)
        assert match and match.group(1) in allowed, line
        reported.add(match.group(1))
    assert reported
    for name, pin in RAW_WHITESPACE_PINS.items():
        assert sha(R / B / 'review-f05-e9-originals-and-preparation' / name) == pin
    c.dump(O / 'VERBATIM_RAW_FORMAT_EXCLUSIONS.json', dict(original_complete_check=row,
        exact_hashes=RAW_WHITESPACE_PINS, reported_paths=sorted(reported),
        reason='Original review Git bytes, exact excerpts and unified diff context must remain verbatim. Only their format check is excluded; product/test assertions and all other staged files are unchanged.'))
    git('diff', '--cached', '--check', '--', '.', *[':(exclude)' + name for name in sorted(reported)])
git('commit', '-m', 'docs: publish complete native and Q38 acceptance with latest reviews')
E = git('rev-parse', 'HEAD')
git('push', 'origin', 'HEAD:codex/train-337-continue-20261024')
assert git('ls-remote', 'origin', 'refs/heads/codex/train-337-continue-20261024').split()[0] == E
result = dict(source_sha=L, previous_evidence_head=BEFORE, evidence_head=E,
              published=True, push_exit=0, q38_original_exit=0, q38_cases=42,
              q38_killed=41, q38_equivalent=1, native_r2_original_exit=0,
              nonperf_terminal_status_only=status,
              new_actions_classification='current runs independently classified; CI still failure and acceptance not inferred', prbody_unchanged=True)
c.dump(O / 'RESULT.json', result)
print(json.dumps(result))
