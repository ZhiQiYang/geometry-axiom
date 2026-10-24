from pathlib import Path
import datetime, hashlib, importlib.util, json, os, re, shutil

# Preparation only: root owns the train and executes this publisher.
R = Path('/workspace/geometry-axiom')
L = '7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
BEFORE = 'f05e7cfd373c9a77a366f7b2ddafd9401f261cf4'
O = Path('/workspace/geo337-canvas-publication')
SRC = Path('/workspace/train337-browser-terminal-collection/canvas')
PEER = Path('/workspace/train337-canvas-peer-resume')
ARCHIVE_PIN = '4153cafa4e1a24b75368a31c4fe8c71ab7b8bb5dde056c55880820bb41b78dbc'
PINS = {
    SRC / 'ORIGINAL_BROWSER_JOB_AND_TEMP_OUTPUTS.tar.gz': ARCHIVE_PIN,
    PEER / 'FINAL_L_CANVAS_ACTUAL_PACKAGE_PEER.json': '98ad284c8534d98593dcb67803f71df10f276892314b9684ccf81c52255a130b',
    PEER / 'review_L_canvas_actual_package.py': '331fb4be8b338a4ca8cf3dc0fdc0de80b10d026c29266c5c8e90d1079ccb1d1e',
    PEER / 'build_reviewer.py': '6f4e6d783cb020bd4bf22487941bf669bbb971aa3b7b5969c1e2c97e2bbb4104',
    Path('/workspace/train337-browser-terminal-collection/collect_terminal_browser.py'): '035f189e5f6a9195cccc7afcf25f84eadcce5dc6bd27e81ea5376153fe619e23',
    Path('/workspace/train337-native-L-7af8c5d8-r2-launch/launch-request.json'): 'e94c052befa217a317d363009378b9edb1769aadafd97f48ba4ff8f3aebb6ee4',
    Path('/workspace/train337-native-L-7af8c5d8-r2-launch/subcommands/000001/request.json'): 'a63fda2eea60e922ab826e1e32c7c6490fc56bb24a91b6e346a0dc4f0a976562',
    Path('/workspace/launch_geo337_L_native_r2.py'): '83cfa7b2f817a68ec378fb25d760b3497dd07847f8be75bb30de76bab340d59f',
    Path('/tmp/train337-adversarial/FINAL_L_NATIVE_R2_OUTER_DELTA_PEER.json'): '8005ce531a2f148bdaf9008d0de1d3caebeb985c8352daa6da6048e0ddc4cc3f',
}
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()
for path, expected in PINS.items():
    assert path.is_file() and not path.is_symlink(), path
    assert sha(path) == expected, path
package = json.loads((SRC / 'PACKAGE.json').read_text())
summary = json.loads((SRC / 'SUMMARY.json').read_text())
peer = json.loads((PEER / 'FINAL_L_CANVAS_ACTUAL_PACKAGE_PEER.json').read_text())
assert package['sourceSHA'] == L and package['archiveSHA256'] == ARCHIVE_PIN
assert package['memberCount'] == 742 and package['archiveBytes'] == 10485838
assert sha(SRC / 'RAW_INVENTORY.json') == package['rawInventorySHA256']
assert summary['sourceSHA'] == L and summary['passed'] is True
assert summary['originalExit'] == 0 and summary['wrapperExit'] == 0
assert summary['overOriginalCITimeout'] is False and summary['originalCITimeoutMinutes'] == 35
assert peer['source_sha'] == L and peer['exit_code'] == 0 and peer['findings'] == []
assert peer['passed_assertions'] == 2267 and peer['failed_assertions'] == 0
assert peer['golden_compare'] == 'matched' and peer['skipped'] == []
# This publication records an immutable launch, not unfinished native streams.
assert not Path('/workspace/train337-native-L-7af8c5d8-r2-launch/receipt.json').exists(), 'Native terminal appeared: update current state before publication.'

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
                            source_variant='evidence-only-final-L-canvas')
    assert row['actual_process_returncode'] == 0, (args, err)
    return out.decode().strip()
assert git('rev-parse', 'HEAD') == BEFORE
assert git('branch', '--show-current') == 'codex/train-337-continue-20261024'
assert not git('status', '--porcelain=v1', '--untracked-files=all')
B = Path('evidence/geo337-train-20261024')
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
for name in ('PACKAGE.json', 'SUMMARY.json', 'RAW_INVENTORY.json', 'ORIGINAL_BROWSER_JOB_AND_TEMP_OUTPUTS.tar.gz'):
    copy_file(SRC / name, Path('final-L-browser-canvas') / name)
for source in (PEER / 'FINAL_L_CANVAS_ACTUAL_PACKAGE_PEER.json',
               PEER / 'review_L_canvas_actual_package.py', PEER / 'build_reviewer.py',
               Path('/workspace/train337-browser-terminal-collection/collect_terminal_browser.py'),
               Path(__file__).resolve()):
    copy_file(source, Path('final-L-browser-canvas') / source.name)
for source, name in (
    (Path('/workspace/train337-native-L-7af8c5d8-r2-launch/launch-request.json'), 'launch-request.json'),
    (Path('/workspace/train337-native-L-7af8c5d8-r2-launch/subcommands/000001/request.json'), 'original-outer-command-request.json'),
    (Path('/workspace/launch_geo337_L_native_r2.py'), 'launch_geo337_L_native_r2.py'),
    (Path('/tmp/train337-adversarial/FINAL_L_NATIVE_R2_OUTER_DELTA_PEER.json'), 'FINAL_L_NATIVE_R2_OUTER_DELTA_PEER.json'),
):
    copy_file(source, Path('final-L-native-r2-start') / name)

p = R / B / 'PROGRESS.md'
t = p.read_text()
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
t, n = re.subn(r'## 唯一 current-state（[^\n]+）', '## 唯一 current-state（' + now + '）', t, count=1)
assert n == 1
def replace_once(old, new):
    global t
    assert t.count(old) == 1, old
    t = t.replace(old, new, 1)
replace_once('r1原exit1：4個ENOENT環境紅；同L三fixture已補齊、完整r2待跑',
             'r1原exit1：4個ENOENT環境紅；同L三fixture已補齊、完整r2 RUNNING（啟動紀錄，無終態判決）')
replace_once('documents0；assembly0；grid0；space0；timber0；canvas RUNNING',
             'canvas0；assembly0；documents0；grid0；space0；timber0')
replace_once('documents47原assert全0／64.316s；assembly150原assert全0／191.692s；獨立checkout／埠／暫存，canvas獨占、原CI時限保留',
             'canvas2267原assert全0／1718.885s<35min，85 golden一致、零skip；P88=143；其餘五job各原收據已封，獨立checkout／埠／暫存、canvas獨占、原CI時限保留')
replace_once('native r1及§7均已終態釋放；同L補齊三fixture，r2待canvas終態後原完整重跑',
             'native r1、§7及canvas均已終態；同L補齊三fixture後，r2已於00:38 UTC啟動原完整重跑，ROOT與共用cache由native獨占')
t += '\n## ' + now + '：完整 canvas 通過，六項 browser 同 L 收齊\n\n'
t += ('canvas 原完整 CDP_RESULT 為2267通過／0失敗、skipped=[]，85個golden section完全相符；P88=143、P73=69，原workflow與outer皆0。原elapsed1718.8848816149984秒，低於原35分鐘，沒有改斷言、golden或時限。原紀錄的1個uncaughtBrowserExceptions是P38故意注入fb-auto-probe，原EXPECTED標記及兩個P38檢查均通過，沒有UNEXPECTED EXCEPTION標記；transport/network故障注入診斷亦逐字保留，沒有宣稱例外欄位為0。\n\n')
t += ('完整742members／51,393,525原bytes封於final-L-browser-canvas，tar為10,485,838B、SHA256 ' + ARCHIVE_PIN + '。包含原指令、結束碼、完整streams、環境、L來源、4張workflow截圖及5個本地artifact；本地保存不冒GitHub上傳。三個可重建ELF僅省略payload而保真hash與sidecar；82個Chrome cache葉列明省略且未刪除。前後checkout／pool守門、reaper均原0，獨立3712核對0只驗收據，不增加產品測試數。六項browser現已同L全0。\n\n')
t += ('native第二輪已在三個原fixture補齊後，依原完整230列入口重新啟動；final-L-native-r2-start只保存不變的啟動argv、原環境、來源SHA與launcher靜審，沒有封未完成streams，也不宣稱native通過。第一輪環境exit1保留。P52、Q38、P-189、#323 required-eight／PF3／timing／profile／memo仍UNRUN；B2原跨版本exact紅與B3待同L完整補驗仍未解除，沒有READY-TO-MERGE。\n')
p.write_text(t)
staged.append(str(B / 'PROGRESS.md'))
git('add', '-f', '--sparse', *staged)
assert all(name.startswith(str(B) + '/') for name in git('diff', '--cached', '--name-only').splitlines())
git('diff', '--cached', '--check')
git('commit', '-m', 'docs: publish complete final canvas acceptance receipts')
E = git('rev-parse', 'HEAD')
git('push', 'origin', 'HEAD:codex/train-337-continue-20261024')
assert git('ls-remote', 'origin', 'refs/heads/codex/train-337-continue-20261024').split()[0] == E
result = dict(source_sha=L, previous_evidence_head=BEFORE, evidence_head=E,
              published=True, push_exit=0, canvas_exit=0, canvas_assertions=2267,
              all_six_browser_original_exits=0, native_r1_exit=1,
              native_r2_launch_record_only=True, native_r2_pass_claim=False)
c.dump(O / 'RESULT.json', result)
print(json.dumps(result))
