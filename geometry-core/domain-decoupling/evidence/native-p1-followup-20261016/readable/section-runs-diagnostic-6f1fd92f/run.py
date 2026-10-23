"""Capture one original runs-client failure, separate from prior unittest evidence."""
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent
original = EVIDENCE / 'native-candidate-6f1fd92f-v1'
prior = json.loads((original / 'summary.json').read_bytes())
root = Path(prior['source_root'])
out = EVIDENCE / 'section-runs-diagnostic-6f1fd92f-v1'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest():
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}

def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

held, lock = os.fstat(7), Path('/run/lock/ga-wsl-v3.lock').stat()
assert (held.st_dev, held.st_ino) == (lock.st_dev, lock.st_ino)
assert prior['source'] == '6f1fd92f6886d6512c355baba4435e297b4e9664' and prior['source_unchanged']
before = manifest()
assert before == json.loads((original / 'source-after.json').read_bytes())
out.mkdir(exist_ok=False)
save(out / 'source-before.json', before)
runner_before = {name: sha(HERE / name) for name in ('run.py', 'namespace.sh')}
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
sys.path.insert(0, str(root))
module = importlib.import_module('tests.test_geo261_wood_section_profile')
module.WoodSectionProfile.setUpClass()
build = module.native()
binary = module.WoodSectionProfile.exe
command = [str(binary), 'runs']
result = subprocess.run(command, cwd=root, capture_output=True, timeout=20)
(out / 'stdout.bin').write_bytes(result.stdout)
(out / 'stderr.log').write_bytes(result.stderr)
save(out / 'build-log.json', build.logs)
artifacts = {}
for path in sorted(build.work.rglob('*')):
    if not path.is_file():
        continue
    relative = path.relative_to(build.work)
    artifacts[str(relative)] = {'sha256': sha(path), 'bytes': path.stat().st_size}
    if path.suffix in ('.json', '.c', '.h'):
        target = out / 'build-inputs' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
save(out / 'build-artifacts.json', artifacts)
after = manifest()
save(out / 'source-after.json', after)
runner_after = {name: sha(HERE / name) for name in runner_before}
old_artifacts = json.loads((original / 'native-build-artifacts.json').read_bytes())
summary = {'kind': 'new-diagnostic-original-section-runs-once', 'source': prior['source'], 'source_root': str(root),
           'started_utc': started, 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'command': command, 'observed_exit': result.returncode,
           'stdout_sha256': sha(out / 'stdout.bin'), 'stderr_sha256': sha(out / 'stderr.log'),
           'stdout_text': result.stdout.decode('utf-8', errors='replace'), 'stderr_text': result.stderr.decode('utf-8', errors='replace'),
           'binary_sha256': sha(binary), 'original_binary_sha256': old_artifacts['section-profile-client']['sha256'],
           'binary_matches_original': sha(binary) == old_artifacts['section-profile-client']['sha256'],
           'source_files': len(before), 'source_unchanged': before == after,
           'source_before_sha256': sha(out / 'source-before.json'), 'source_after_sha256': sha(out / 'source-after.json'),
           'runner_sha256_before': runner_before, 'runner_sha256_after': runner_after, 'runners_unchanged': runner_before == runner_after,
           'compiler_commands': len(build.logs), 'build_artifacts': len(artifacts),
           'shared_lock_holder': Path('/run/lock/ga-wsl-v3.holder').read_text(),
           'unittest_methods_executed': 0, 'mutations_executed': False, 'full_suite_executed': False,
           'capture_exit': 0 if before == after and runner_before == runner_after else 1,
           'meaning': 'Capture completion is not product acceptance; original failing unittest receipt remains unchanged.'}
save(out / 'summary.json', summary)
(out / 'exit.txt').write_text(str(summary['capture_exit']) + '\n', encoding='ascii')
print(json.dumps(summary, ensure_ascii=False, indent=2))
sys.exit(summary['capture_exit'])
