from pathlib import Path
import datetime, hashlib, importlib.util, json, os, re, shutil

R = Path('/workspace/geometry-axiom')
P = Path('/workspace/geo337-performance-status-only-preparation-20261024')
O = Path('/workspace/geo337-performance-terminal-status-publication')
B = Path('evidence/geo337-train-20261024')
TARGET = B / 'final-L-performance-terminal-status-only'
L = '7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
BEFORE = '58a75f479fd9c65e71a7827b732ae738b667294e'
BRANCH = 'codex/train-337-continue-20261024'
PINS = {
    'PROGRESS.draft.md': 'afe9d81a28c6de51cf7f6c20d310f3a74e58d04317e0b90b191e811fa5efc3cb',
    'QUESTIONS.draft.md': '672a864926c9888f660f1fcfa8067c282f1b24032360c4c0ccfd4d0f214b78fb',
    'PR_BODY.draft.md': '008e25c5e08935de665daa99ccd39372b80b70b0f2e8c0a203f0417a4dcdf43b',
}
def sha(data):
    return hashlib.sha256(data).hexdigest()
for name, pin in PINS.items():
    assert sha((P/name).read_bytes()) == pin, name
manifest = json.loads((P/'MANIFEST.json').read_text())
assert manifest['source_sha'] == L and manifest['expected_evidence_head'] == BEFORE
assert manifest['complete_raw_archives_published'] is False and manifest['small_original_bytes'] == 451505
assert len(manifest['files']) == 50
assert manifest['original_exits'] == {'p52':0,'p189_full':1,'p189_timing':0,'geo323_prepare':0,'geo323_build':0,'geo323_compare':1}
assert manifest['unrun'] == ['geo323_perf','geo323_profile','memo']
known_raw = {}
for row in manifest['files']:
    name = row['name']
    assert not Path(name).is_absolute() and '..' not in Path(name).parts and not name.endswith('.tar.gz')
    path = P/'frozen-originals'/name
    assert path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    assert len(raw) == row['bytes'] and len(raw) < 400000 and sha(raw) == row['sha256']
    known_raw[str(TARGET/name)] = row['sha256']
# Do not publish an UNRUN current-state after the shared receipt has advanced.
assert Path('/workspace/g337323L/receipt.json').read_bytes() == (P/'frozen-originals/geo323-compare/receipt-after-compare.json').read_bytes()

cp = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert sha(cp.read_bytes()) == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec = importlib.util.spec_from_file_location('cap', cp)
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
O.mkdir(); env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0'); env.pop('PYTHONOPTIMIZE', None)
rec = c.Recorder(O, env, L)
def git(*args):
    row, out, err = rec.run(['git', *args], cwd=R, timeout=None, check=False, source_variant='original-performance-terminal-status-only')
    assert row['actual_process_returncode'] == 0, (args, err)
    return out.decode().strip()
assert git('rev-parse', 'HEAD') == BEFORE and git('branch', '--show-current') == BRANCH
assert not git('status', '--porcelain=v1', '--untracked-files=all')
for name in ('PROGRESS', 'QUESTIONS'):
    assert (R/B/(name+'.md')).read_bytes() == (P/(name+'.original.md')).read_bytes()
target = R/TARGET; target.mkdir()
for row in manifest['files']:
    source = P/'frozen-originals'/row['name']; dest = target/row['name']
    dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, dest)
    assert sha(dest.read_bytes()) == row['sha256']
shutil.copyfile(P/'MANIFEST.json', target/'STATUS_MANIFEST.json')
shutil.copyfile('/workspace/prepare_geo337_performance_status_only.py', target/'prepare_geo337_performance_status_only.py')
shutil.copyfile(__file__, target/Path(__file__).name)
for name in ('PROGRESS', 'QUESTIONS'):
    text = (P/(name+'.draft.md')).read_text()
    if name == 'PROGRESS':
        now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        text = re.sub(r'## 唯一 current-state（[^\n]+）', '## 唯一 current-state（'+now+'）', text, count=1)
    (R/B/(name+'.md')).write_text(text)
git('add', '-f', '--sparse', str(TARGET), str(B/'PROGRESS.md'), str(B/'QUESTIONS.md'))
assert all(name.startswith(str(TARGET)+'/') or name in {str(B/'PROGRESS.md'), str(B/'QUESTIONS.md')}
           for name in git('diff', '--cached', '--name-only').splitlines())
row, out, err = rec.run(['git','diff','--cached','--check'], cwd=R, timeout=None, check=False,
                        source_variant='verbatim-original-status-format-check')
if row['actual_process_returncode']:
    assert row['actual_process_returncode'] == 2 and not err
    excluded = set()
    for line in out.decode().splitlines():
        match = re.match(r'(.+):\d+: (.+)', line)
        if not match:
            continue
        name, message = match.groups()
        assert name in known_raw and message in ('trailing whitespace.', 'new blank line at EOF.'), line
        assert sha((R/name).read_bytes()) == known_raw[name]
        excluded.add(name)
    assert excluded
    c.dump(O/'VERBATIM_ORIGINAL_FORMAT_EXCLUSIONS.json', {'original_exit':2,'paths':{n:known_raw[n] for n in sorted(excluded)}})
    git('diff','--cached','--check','--','.',*[':(exclude)'+name for name in sorted(excluded)])
git('commit','-m','docs: record original performance and exact comparison terminal results')
E = git('rev-parse','HEAD'); git('push','origin','HEAD:'+BRANCH)
assert git('ls-remote','origin','refs/heads/'+BRANCH).split()[0] == E
result = {'source_sha':L,'previous_evidence_head':BEFORE,'evidence_head':E,'published':True,'push_exit':0,
          'original_exits':manifest['original_exits'],'complete_raw_archives_published':False,
          'prbody_candidate':str(P/'PR_BODY.draft.md'),'prbody_unchanged':True}
c.dump(O/'RESULT.json',result); print(json.dumps(result))
