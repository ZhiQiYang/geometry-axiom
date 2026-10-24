from pathlib import Path
import datetime, hashlib, importlib.util, json, os, re, shutil

R = Path('/workspace/geometry-axiom')
O = Path('/workspace/geo337-p52-terminal-status-publication')
B = Path('evidence/geo337-train-20261024')
L = '7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
BEFORE = 'f16e0f51f92c5d1fe1fdbf65baf4d69160f67c09'
files = {
    'outer-RESULT.json': Path('/workspace/train337-L-p52-original-launch-20261024/RESULT.json'),
    'driver-receipt.json': Path('/tmp/g337p52L/receipt.json'),
    'formal-execution-receipt.json': Path('/tmp/g337p52L/formal/execution-receipt.json'),
    'original-protocol-receipt.json': Path('/tmp/g337p52L/formal/receipt.json'),
}
outer, driver, formal, original = [json.loads(p.read_text()) for p in files.values()]
assert outer['source_sha'] == driver['source_sha'] == original['sha'] == L
assert outer['actual_exit'] == driver['launcher_exit_code'] == 0
assert driver['passed'] and not driver['errors'] and formal['passed']
assert [p['primary_returncode'] for p in driver['phases']] == [0, 0]
assert original['timing']['no_regression'] and original['timing']['count'] == {'main': 16, 'fix': 16}
assert len(original['controls']) == 5 and all(x['expected_behavior_proved'] for x in original['controls'])
cp = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert hashlib.sha256(cp.read_bytes()).hexdigest() == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
s = importlib.util.spec_from_file_location('cap', cp)
c = importlib.util.module_from_spec(s); s.loader.exec_module(c)
O.mkdir(); env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1'); env.pop('PYTHONOPTIMIZE', None)
rec = c.Recorder(O, env, L)
def git(*args):
    row, out, err = rec.run(['git', *args], cwd=R, timeout=None, check=False, source_variant='p52-terminal-status-only')
    assert row['actual_process_returncode'] == 0, (args, err)
    return out.decode().strip()
assert git('rev-parse', 'HEAD') == BEFORE
assert git('branch', '--show-current') == 'codex/train-337-continue-20261024'
assert not git('status', '--porcelain=v1', '--untracked-files=all')
target = R / B / 'final-L-p52-terminal-status-only'; target.mkdir()
manifest = []
for name, source in files.items():
    body = source.read_bytes(); (target / name).write_bytes(body)
    manifest.append(dict(name=name, source_path=str(source), bytes=len(body), sha256=hashlib.sha256(body).hexdigest()))
c.dump(target / 'STATUS_MANIFEST.json', dict(source_sha=L, files=manifest, full_raw_package_published=False,
    limitation='Original terminal receipts only; complete streams and independent package verification remain pending. Initial collector failed on a terminal Chrome SingletonCookie symlink; subject formal/verifier remain original exit0.'))
shutil.copyfile(__file__, target / Path(__file__).name)
p = R / B / 'PROGRESS.md'; text = p.read_text()
old = 'P52／P-189 UNRUN'; assert text.count(old) == 1
text = text.replace(old, 'P52 formal／verifier／driver／outer0（終態原收據已封，完整流包待）；P-189 UNRUN', 1)
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
text = re.sub(r'## 唯一 current-state（[^\n]+）', '## 唯一 current-state（' + now + '）', text, count=1)
text += '\n## ' + now + '：P52原正式量測與五控制真終態0\n\n同L原main/fix/fix/main交錯四區塊、每側16筆全部保留，main中位218.2650215ms、fix176.218242ms，ratio0.8073590573008969；原門檻fix<=main成立，沒有+5ms容忍。normal/delay原0，revert-delay/wrong/missing原1且各符合原控制判準；formal/verifier/driver/outer全0。四份原終態收據先封於final-L-p52-terminal-status-only，完整streams仍在原OUT，尚待完整原件包與獨立核對，沒有冒稱已全封。第一次collector遇Chrome SingletonCookie symlink退出1，屬收件工具假設錯誤，完整失敗保留；沒有重跑產品、改斷言或改時限。P-189與#323性能接續，B2及B3仍未解除。\n'
p.write_text(text)
git('add', '-f', '--sparse', str(B / 'final-L-p52-terminal-status-only'), str(B / 'PROGRESS.md'))
assert all(x.startswith(str(B / 'final-L-p52-terminal-status-only') + '/') or x == str(B / 'PROGRESS.md') for x in git('diff', '--cached', '--name-only').splitlines())
git('diff', '--cached', '--check')
git('commit', '-m', 'docs: record terminal P52 measurement and control results')
E = git('rev-parse', 'HEAD')
git('push', 'origin', 'HEAD:codex/train-337-continue-20261024')
assert git('ls-remote', 'origin', 'refs/heads/codex/train-337-continue-20261024').split()[0] == E
result = dict(source_sha=L, evidence_head=E, published=True, push_exit=0, p52_original_exit=0, full_raw_package_published=False)
c.dump(O / 'RESULT.json', result); print(json.dumps(result))
