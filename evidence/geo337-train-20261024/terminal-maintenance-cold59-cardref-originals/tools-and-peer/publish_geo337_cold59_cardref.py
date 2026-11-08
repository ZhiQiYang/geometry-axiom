from pathlib import Path
import datetime, hashlib, importlib.util, json, os, shutil

# Root-only maintenance evidence publication; execute only outside performance.
R = Path('/workspace/geometry-axiom')
L = '7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
BEFORE = 'c22ab27787322ae9fc07d410d1a17397f4809c1d'
BRANCH = 'codex/train-337-continue-20261024'
B = Path('evidence/geo337-train-20261024')
TARGET = B / 'terminal-maintenance-cold59-cardref-originals'
O = Path('/workspace/geo337-cold59-cardref-publication')
SOURCE = Path('/workspace/cold59-and-cardref-links-originals-20261024')
OUTER = Path('/workspace/cold59-and-cardref-links-collection-launch-20261024')
PEER = Path('/workspace/train337-canvas-peer-resume')
ARCHIVE = SOURCE / 'cold59-and-cardref-links-originals.tar.gz'
ARCHIVE_PIN = '0c9cb4ef4f425d7cb7ab7542c0b183ac55f09d6ada7350ea7e4e36bf7c95fcdb'
PENDING_SMALL_PINS = False
PINS = {
    SOURCE / 'PACKAGE.json': '43759f9d932eb66581fc3aad6a94e936e4c6334355c5e7fb56cc359646e0ab7d',
    OUTER / 'RESULT.json': 'c506f4561d2143f7a61e7f8a15fa943a33c7b602c64112246bfaedcc7db97aa0',
    Path('/workspace/cold59-root-sequential-execution-20261024.json'): '21fbf9dcd4942517d7eea0861bcfdf119d8dee9a132c916adb1f77536724840d',
    PEER / 'COLD59_CARDREF_ACTUAL_PACKAGE_PEER.json': '99d82a9e0469e3f21ee157a9d64f1e756d8f5ceb936da30aa303c2640fce0783',
    PEER / 'COLD59_CARDREF_COLLECTOR_STATIC_PEER.json': 'ba8dbc8628998920169f288df823e3a8a149e09e8cb764f49cb4bcb8aabd4558',
    PEER / 'review_cold59_cardref_collector.py': '564615934f76a96b1008d972c1f2f4377a31ea094718ec346d3eaf1e3f848700',
    PEER / 'review_cold59_cardref_package.py': '7cd79d987727ec2715c7ea9c76c9f99736030c70e68c13f0ec28f83fd1d3ba37',
    Path('/workspace/collect_cold59_and_cardref_originals_20261024.py'): 'e4b0056a2dc08a5b1900f26abbeb7644726464a5a75d77b8a0fb226051a0c1b5',
}
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()
assert not PENDING_SMALL_PINS, 'Preparation only: exact collector/peer helper pins are not yet installed.'
for path, pin in PINS.items():
    assert path.is_file() and not path.is_symlink() and sha(path) == pin, path
assert ARCHIVE.is_file() and not ARCHIVE.is_symlink()
assert ARCHIVE.stat().st_size == 4160382 and sha(ARCHIVE) == ARCHIVE_PIN
package = json.loads((SOURCE / 'PACKAGE.json').read_text())
assert package['exit_code'] == 0 and package['member_count'] == 7487
assert package['archive_sha256'] == ARCHIVE_PIN and package['roundtrip_original_bytes'] is True
assert package['all_established_cold_alias_groups'] == 295
assert package['cardref_elf_alias_groups_added'] == 2
for name in ('COLD59_CARDREF_ACTUAL_PACKAGE_PEER.json', 'COLD59_CARDREF_COLLECTOR_STATIC_PEER.json'):
    d = json.loads((PEER / name).read_text())
    assert d['exit_code'] == 0 and d['findings'] == []
outer = json.loads((OUTER / 'RESULT.json').read_text())
assert outer['source_sha'] == L and outer['actual_process_returncode'] == 0

O.mkdir()
cp = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert sha(cp) == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec = importlib.util.spec_from_file_location('cap', cp)
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0'); env.pop('PYTHONOPTIMIZE', None)
rec = c.Recorder(O, env, L)
def git(*args):
    row, out, err = rec.run(['git', *args], cwd=R, timeout=None, check=False,
                            source_variant='evidence-only-terminal-cold59-cardref-maintenance')
    assert row['actual_process_returncode'] == 0, (args, err)
    return out.decode().strip()
assert git('rev-parse', 'HEAD') == BEFORE and git('branch', '--show-current') == BRANCH
assert not git('status', '--porcelain=v1', '--untracked-files=all')
staged = []
def copy_file(source, relative):
    assert source.is_file() and not source.is_symlink(), source
    target = TARGET / relative
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
copy_file(ARCHIVE, ARCHIVE.name)
copy_file(SOURCE / 'PACKAGE.json', 'PACKAGE.json')
# MEMBER_INVENTORY.json already exists inside the fixed tar; do not duplicate it.
for relative in ('REQUEST.json', 'RESULT.json', 'subcommands.json', 'subcommands/000001/request.json',
                 'subcommands/000001/result.json', 'subcommands/000001/stdin.bin',
                 'subcommands/000001/stdout.bin', 'subcommands/000001/stderr.bin'):
    copy_file(OUTER / relative, Path('collector-outer') / relative)
for source in PINS:
    if source in (SOURCE / 'PACKAGE.json', OUTER / 'RESULT.json'):
        continue
    copy_file(source, Path('tools-and-peer') / source.name)
copy_file(Path(__file__), Path('tools-and-peer') / Path(__file__).name)

progress = R / B / 'PROGRESS.md'
t = progress.read_text()
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
t += ('\n## ' + now + '：59組cold receipts與cardref受控突變ELF保全原件公開\n\n'
      '本批僅維護證據，不執行或移標產品gate。59組新增cold aliases的177原路徑與bytes全保，連同既有236組共295組cold aliases；三個cold checkouts在全部aliases脫鉤前禁寫、禁復用。原plan配置節省量286,375,936B，不能當成有背景寫入時的df淨回收。\n\n'
      'cardref另有兩組受控突變ELF aliases，原116路徑與bytes全留，63個重複payload以保全link共享；原plan配置節省量79,196,160B，不是df淨回收。這兩組與295組cold aliases分開，任一alias寫入或復用前須全部delink。原inode與per-path mtime不保原樣，原metadata在PLAN；沒有刪受控ELF、收據、fixture或git object。\n\n'
      '固定原件包7487members、4,160,382B、SHA256 0c9cb4ef4f425d7cb7ab7542c0b183ac55f09d6ada7350ea7e4e36bf7c95fcdb已公開於terminal-maintenance-cold59-cardref-originals。它保存原小metadata與完整命令流，不另複製cold receipt本體或ELF payload；cardref原931份非ELF原件由既有§7完整包／inventory覆蓋，沒有聲稱新包二次包含。collector完整外層與包外root sequential原件另外公開，未回寫固定tar；原收包0、獨審30026/0及collector靜審19/0均保。這些核對數不計產品gate，不更新其他效能終態，也不宣稱整體READY。\n')
progress.write_text(t); staged.append(str(B / 'PROGRESS.md'))
questions = R / B / 'QUESTIONS.md'
q = questions.read_text()
old = '最新 #338 審查（handoff a47d625c，2026-10-23 20:44 UTC，head b6）'
assert q.count(old) == 1
q = q.replace(old, '首輪 #338 審查（handoff a47d625c，2026-10-23 20:44 UTC，head b6）', 1)
anchor = '\n\n已封根因（`review-b6-response/b2-diagnostic-originals-and-peer.tar.gz`）'
assert q.count(anchor) == 1
q = q.replace(anchor, '\n\n後續2026-10-24 00:39:37 UTC／head f05e7cf的#338審查重申B2仍未解除：須先取得並登記診斷版本界線／comparator裁決或恢復exact，再以L跑原comparator；memo-only不能取代。本補記只更正審查沿革，沒有採納新裁決、變更比較器或改寫原exit1。' + anchor, 1)
questions.write_text(q); staged.append(str(B / 'QUESTIONS.md'))
git('add', '-f', '--sparse', *staged)
assert all(name.startswith(str(TARGET) + '/') or name in {str(B / 'PROGRESS.md'), str(B / 'QUESTIONS.md')}
           for name in git('diff', '--cached', '--name-only').splitlines())
git('diff', '--cached', '--check')
git('commit', '-m', 'docs: publish preserved cold receipts and cardref ELF maintenance evidence')
E = git('rev-parse', 'HEAD')
git('push', 'origin', 'HEAD:' + BRANCH)
assert git('ls-remote', 'origin', 'refs/heads/' + BRANCH).split()[0] == E
result = dict(source_sha=L, previous_evidence_head=BEFORE, evidence_head=E, published=True,
              push_exit=0, maintenance_only=True, product_gates_changed=False,
              cold_alias_groups=295, separate_controlled_cardref_elf_alias_groups=2)
c.dump(O / 'RESULT.json', result); print(json.dumps(result))
