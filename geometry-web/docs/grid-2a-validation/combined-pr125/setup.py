from pathlib import Path
from urllib.request import urlopen
import datetime, hashlib, json, os, socket, subprocess, time

repo = Path('/workspace/pr130-integration')
out = Path('/tmp/pr130-combined-20261004')
old = Path('/tmp/pr130-qa-e06ff2a')
base = '8d134fcb08041708ac174c11185f175cfa369c4a'
main = 'a4caf166675fbdfa4664a55f4d59a5f43c3a50c1'
p125 = '5a82f4435443872b9cb66ede3da456dad75e4424'
p130 = 'b0174da3940f462b80e40b462a4bfd1c08d119d1'
def git(*args): return subprocess.check_output(['git', *args], cwd=repo, text=True).strip()
def sha(data): return hashlib.sha256(data).hexdigest()
assert not git('status', '--porcelain')
head = git('rev-parse', 'HEAD')
assert git('show', '-s', '--format=%P', head).split() == [p130, main]
assert git('rev-parse', main+'^{tree}') == git('rev-parse', p125+'^{tree}')
changed125 = set(git('diff', '--name-only', base, main).splitlines())
changed130 = set(git('diff', '--name-only', base, p130).splitlines())
assert changed125 & changed130 == {'geometry-web/docs/DOM-CONTRACT.md'}
preserved = {}
for parent, paths in [(main, changed125-changed130), (p130, changed130-changed125)]:
    for path in sorted(paths):
        expected = subprocess.check_output(['git', 'show', parent+':'+path], cwd=repo)
        actual = (repo/path).read_bytes()
        assert expected == actual, path
        preserved[path] = {'parent': parent, 'sha256': sha(actual)}
native = [p for p in git('ls-files').splitlines() if Path(p).suffix in {'.c', '.h', '.inc'}]
for path in native:
    assert subprocess.check_output(['git', 'show', p130+':'+path], cwd=repo) == (repo/path).read_bytes(), path
for path in ['geometry-web/project-store.js', 'geometry-web/reference-workspace.js', 'geometry-web/parameters.js', '公理層.md']:
    assert subprocess.check_output(['git', 'show', base+':'+path], cwd=repo) == (repo/path).read_bytes(), path
labels = ['grid', 'infinite-face', 'selection', 'b-menu', 'pointer', 'mixed']
services = {}
for port, label in zip(range(8840, 8846), labels):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', port))
    feedback = out/('feedback-'+label)
    feedback.mkdir(exist_ok=True)
    env = dict(os.environ, GEOMETRY_BRIDGE=str(old/'web_bridge'), GEOMETRY_MODEL_BASE=str(old/'model_base'), GEOMETRY_FEEDBACK_DIR=str(feedback))
    log = open(out/(label+'-server.log'), 'wb')
    proc = subprocess.Popen(['python', 'geometry-web/serve.py', str(port)], cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    log.close()
    runtime = None
    for _ in range(100):
        assert proc.poll() is None, (label, proc.returncode)
        try:
            runtime = json.load(urlopen(f'http://127.0.0.1:{port}/runtime', timeout=2))
            break
        except (OSError, ValueError): time.sleep(.1)
    assert runtime and runtime['fresh'] and Path(runtime['root']) == repo
    services[label] = {'port':port, 'pid':proc.pid, 'feedback':str(feedback), 'runtime':runtime}
assert len({s['runtime']['version'] for s in services.values()}) == 1
record = {'schema':'geometry-pr125-pr130-combined-identity/1', 'capturedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'base':base, 'main':main, 'pr125':p125, 'pr130Before':p130, 'testedHead':head, 'testedTree':git('rev-parse', 'HEAD^{tree}'), 'parents':git('show','-s','--format=%P',head).split(), 'overlap':sorted(changed125&changed130), 'exclusiveFilesPreserved':preserved, 'nativeClosureByteIdenticalToPR130':native, 'nativeBinaries':{name:sha((old/name).read_bytes()) for name in ['core','web_bridge','model_base']}, 'services':services, 'browser':'Browser plugin not available; existing Playwright and /usr/bin/chromium used', 'scope':'Targeted combined integration; no repeat of unrelated full suites. Synthetic fixtures only.'}
(out/'identity.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'head':head,'tree':record['testedTree'],'overlap':record['overlap'],'preservedFiles':len(preserved),'nativeClosureFiles':len(native),'runtime':services['grid']['runtime']['version'],'services':{k:v['port'] for k,v in services.items()}},ensure_ascii=False))
