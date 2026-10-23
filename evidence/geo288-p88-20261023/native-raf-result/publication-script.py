"""Publish completed P88 proof evidence without changing source or raw artifacts."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

here = Path(__file__).resolve().parent
repo = Path('/tmp/g288p88fix')
branch = 'codex/geo288-p88-stable-click-20261023'
prefix = 'evidence/geo288-p88-20261023'
dest = repo / prefix
out = here / 'native-raf-final-child-publication'
out.mkdir(exist_ok=False)
report = {'schema': 'geo288-p88-final-proof-publication/1', 'branch': branch,
          'product_sha': '3d681636902371ecc528b20f51eea33e272581c9',
          'source_commit': '8bce9239c014f070740455556c8ee1176c500af3',
          'commands': [], 'published': False, 'copied': {}}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save():
    (out / 'receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

def run(argv, check=True):
    process = subprocess.run(argv, cwd=repo, capture_output=True)
    stem = out / f'{len(report["commands"]) + 1:02}'
    stem.with_suffix('.stdout').write_bytes(process.stdout)
    stem.with_suffix('.stderr').write_bytes(process.stderr)
    report['commands'].append({'argv': argv, 'cwd': str(repo), 'actual_exit_code': process.returncode,
                              'stdout_sha256': sha(process.stdout), 'stderr_sha256': sha(process.stderr)})
    save()
    if check and process.returncode:
        raise RuntimeError(str(argv))
    return process

def copy(source, relative):
    data = source.read_bytes()
    target = dest / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == data, ('Refuse overwrite of prior raw artifact', relative)
    else:
        target.write_bytes(data)
    report['copied'][relative] = {'source': str(source), 'bytes': len(data), 'sha256': sha(data)}

save()
assert run(['git', 'branch', '--show-current']).stdout.decode().strip() == branch
assert run(['git', 'status', '--porcelain=v1', '--untracked-files=all']).stdout == b''
assert run(['git', 'rev-parse', 'HEAD']).stdout.decode().strip() == '5d14b40c60f2280f2a3f117c254d729bfcd00fa2'
assert sha((repo / 'geometry-web/grid_rule_lines_test.js').read_bytes()) == '8106476b6eb2271111caa835a863b72eced4bab3b2ef77244f28534d83ca0a52'
archive = here / 'native-raf-diagnostic-archive'
assert sha((archive / 'NATIVE_RAF_RAW.tar.gz').read_bytes()) == '3f107c0424c62844eaeac3ab6086ea75b7ebc6cc3c9e829dd61c34eedcb52e4a'
assert json.loads((archive / 'ROUNDTRIP.json').read_text())['all_archived_files_roundtrip_bytes_and_hashes_match'] is True
for source in sorted(archive.iterdir()):
    assert source.is_file()
    copy(source, 'native-raf-result/' + source.name)
for name in ['NATIVE_RAF_FINAL_SUMMARY.json', 'P88_NATIVE_RAF_VISIBILITY_ANALYSIS.md',
             'P88_NATIVE_RAF_VISIBILITY_ANALYSIS_final.md', 'P88_NATIVE_RAF_VISIBILITY_ANALYSIS_final_v2.md',
             'P88_NATIVE_RAF_VISIBILITY_FACTS.json']:
    copy(here / name, 'native-raf-result/' + name)
for source in sorted(here.glob('native-raf-archive-command.*')):
    copy(source, 'native-raf-result/archive-command/' + source.name)
for source in sorted((here / 'final-canvas-combined-peer').rglob('*')):
    if source.is_file():
        copy(source, 'final-canvas-peer/' + str(source.relative_to(here / 'final-canvas-combined-peer')))
copy(here / 'formal-three-child-publication/GIT_BLOB_ROUNDTRIP.json', 'final-canvas-peer/GIT_BLOB_ROUNDTRIP.json')
peer = Path('/tmp/geo323-merge-20261023')
for phase in ['FIXED', 'WITHDRAWN', 'RESTORED']:
    review = peer / f'P88_NATIVE_RAF_{phase}_ACTUAL_PEER_REVIEW.json'
    assert review.is_file()
    for source in sorted(peer.glob(f'P88_NATIVE_RAF_{phase}_ACTUAL_*.json')):
        copy(source, 'peer-review/' + source.name)
for pattern in ['P88_NATIVE_RAF_THREE_PHASE_ACTUAL_PEER_REVIEW.*', 'P88_NATIVE_RAF_*INPUT_WINDOW*']:
    for source in sorted(peer.glob(pattern)):
        copy(source, 'peer-review/' + source.name)
for source in sorted(Path('/workspace/kernel-no-wood-prep/p88-attribution').iterdir()):
    if source.is_file():
        copy(source, 'native-raf-product-attribution/' + source.name)
copy(here / 'publish_final_native_evidence.py', 'native-raf-result/publication-script.py')
progress = dest / 'PROGRESS.md'
progress.write_text(progress.read_text() + '''
- 12:53:28 UTC：公開 F `3d681636902371ecc528b20f51eea33e272581c9` 的新 native-rAF 受控反證全部終態。fixed／withdrawn／restored 原 outer、workflow、Node 各為 0／1／0；總 driver、outer、launcher 都為 0。固定與恢復各完成原 P88 143 斷言；撤回僅 P88 修正後，以原 `document.activeElement===document.querySelector("#refGuideMode")` 精確焦點 predicate 失敗，並非工具預條件或 CI 超時。三階段前提皆有效，source／index 前後相同乾淨。此為只跑 P88 的受控診斷，不冒正式 grid。
- 原量測真命中 mode 的 y=627.5，原 query renderer 登錄的真 native scroll-restore callback 一次完成後，舊點已命中 ratio label。撤回版原樣送出 y=627.5，焦點停在 ratio；修正版在該次唯一真實點擊前重新量測，使用 y=602.5 命中 mode。相同既有 query／原 callback，沒有手寫 scroll、rect、focus 或值，也沒有錯點後再次點擊補救。原 25 秒、12 次嘗試、斷言及 golden 不變。
- 12:55 UTC：完整原件封存完成，`native-raf-result/NATIVE_RAF_RAW.tar.gz` 22,446,502 bytes，SHA256 `3f107c0424c62844eaeac3ab6086ea75b7ebc6cc3c9e829dd61c34eedcb52e4a`；349 檔逐一 roundtrip bytes/hash 全相同。封包含各 phase 指令／環境／stdout／stderr／退出碼／SHA／trace 與全部凍結工具。各 phase/tmp 整樹（編譯產物、profile、cache、feedback）明列排除，原磁碟未刪。封存器 exit 0。
- 獨立對抗審已核 fixed／withdrawn／restored 的原 predicate、原座標、真 pointer、143 斷言、來源與時限；另附產品／測試歸因審查。新 F 正式 canvas 連續三輪 0／0／0 與兩位代理封包審查完整收錄。舊真 query 控制 1／1／1、總 driver 2 的無效反證仍原樣保留。
- 限制：本控制直接驗 measure→原 restore→click，沒有 Paint/compositor 畫面證據，也未窮盡 pointerdown→query/restore→pointerup。既有資料未建立新的產品交互紅燈；不能宣稱真人不受影響，亦不能把本次 query 回填成歷史自然紅唯一原因。最新 head ee28481 審查的同 F 其餘項目由主代理接續，這份子代理證據不宣稱 #288 全綠。未另開瀏覽器，heavy 槽已交回主代理。
''')
manifest = {}
for source in sorted(dest.rglob('*')):
    if source.is_file() and source != dest / 'FILES.json':
        data = source.read_bytes()
        manifest[str(source.relative_to(dest))] = {'bytes': len(data), 'sha256': sha(data)}
(dest / 'FILES.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
save()
run(['git', 'add', '--sparse', '--force', '--', prefix])
changed = run(['git', 'diff', '--cached', '--name-only']).stdout.decode().splitlines()
assert changed and all(path.startswith(prefix + '/') for path in changed)
# Raw streams retain their original whitespace; only newly authored prose is a whitespace gate.
run(['git', 'diff', '--cached', '--check', '--', prefix + '/PROGRESS.md',
     prefix + '/native-raf-result/P88_NATIVE_RAF_VISIBILITY_ANALYSIS_final_v2.md'])
run(['git', 'commit', '-m', 'docs: archive completed P88 native frame counterproof and peer reviews'])
report['evidence_commit'] = run(['git', 'rev-parse', 'HEAD']).stdout.decode().strip()
save()
for relative, item in report['copied'].items():
    data = subprocess.check_output(['git', 'show', report['evidence_commit'] + ':' + prefix + '/' + relative], cwd=repo)
    assert len(data) == item['bytes'] and sha(data) == item['sha256'], relative
report['all_copied_git_blobs_match'] = True
save()
pushed = run(['git', 'push', 'origin', 'HEAD:refs/heads/' + branch], check=False)
report['push_exit'] = pushed.returncode
save()
if pushed.returncode == 0:
    remote = run(['git', 'ls-remote', 'origin', 'refs/heads/' + branch])
    assert remote.stdout.decode().split()[0] == report['evidence_commit']
    report['published'] = True
assert run(['git', 'status', '--porcelain=v1', '--untracked-files=all']).stdout == b''
report['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
save()
print(json.dumps({key: report.get(key) for key in ['evidence_commit', 'published', 'push_exit', 'all_copied_git_blobs_match']}, ensure_ascii=False))
raise SystemExit(0 if report['published'] else 2)
