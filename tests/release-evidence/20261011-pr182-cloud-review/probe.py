"""Reproduce SPM41 against #182 and a disposable #192 shared-predicate overlay.

This overlay is a fault-compatibility probe, not an integrated product checkout.
Run: python3 probe.py before|after OUTPUT_DIRECTORY
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path.cwd()
PHASE, OUTPUT = sys.argv[1], Path(sys.argv[2]).resolve()
OUTPUT.mkdir(parents=True, exist_ok=True)
OWNER = 'e37c06826d3ed5503117a47d6e3699908e2804b6'
spec = importlib.util.spec_from_file_location('gate', ROOT / 'tests/section_profile_mutation_check.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
gate.posix_only()
gate.ALL['native'] = gate.test_names(gate.NATIVE_MODULE, gate.NATIVE_CLASS, gate.EXCLUDED, ROOT)
case = next(c for c in gate.CASES if c['id'] == 'SPM41')
owner = subprocess.check_output(['git', 'show', OWNER + ':current_geometry.c'])

def sha(data):
    return hashlib.sha256(data).hexdigest()

def functions(data, helper=False):
    start = data.index(b'static bool poly_rect_center_inside(' if helper else b'static bool poly_contains_rect(')
    end = data.index(b'\r\n}\r\n', data.index(b'static bool poly_contains_rect(', start)) + 5
    return start, end

def execute(label, argv, cwd=ROOT):
    start = time.monotonic()
    run = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
    (OUTPUT / (label + '.log')).write_bytes(run.stdout)
    return {'command': argv, 'cwd': str(cwd), 'exit': run.returncode,
            'seconds': time.monotonic() - start, 'log_sha256': sha(run.stdout)}

receipt = {'phase': PHASE, 'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
           'status_before': subprocess.check_output(['git', 'status', '--porcelain'], text=True),
           'gate_sha256': sha((ROOT / 'tests/section_profile_mutation_check.py').read_bytes()),
           'test_sha256': sha((ROOT / 'tests/test_section_profile_native.py').read_bytes()),
           'shared_predicate_owner': OWNER, 'owner_core_sha256': sha(owner), 'case': case, 'contexts': {}}
with tempfile.TemporaryDirectory(prefix='pr182-spm41-') as scratch:
    work = Path(scratch)
    source = work / 'original'
    gate.copy_sources(source)
    for context in ('pr182', 'shared-predicate-192'):
        tree = work / context
        shutil.copytree(source, tree)
        core = tree / 'current_geometry.c'
        if context != 'pr182':
            data = core.read_bytes()
            start, end = functions(data)
            owner_start, owner_end = functions(owner, helper=True)
            core.write_bytes(data[:start] + owner[owner_start:owner_end] + data[end:])
        closure = {p.relative_to(tree).as_posix(): sha(p.read_bytes()) for p in sorted(tree.rglob('*')) if p.is_file()}
        (OUTPUT / (context + '-closure.json')).write_text(json.dumps(closure, indent=2))
        info = {'source_digest': gate.tree_digest(tree), 'core_sha256': sha(core.read_bytes()),
                'validation_sha256': sha((tree / case['file']).read_bytes()), 'runs': {}}
        for mode in ('baseline', 'mutant', 'restored'):
            if mode == 'mutant':
                original = (tree / case['file']).read_bytes()
                gate.mutate_file(tree, case)
                info['mutated_validation_sha256'] = sha((tree / case['file']).read_bytes())
            elif mode == 'restored':
                (tree / case['file']).write_bytes(original)
            exe = work / (context + '-' + mode)
            label = context + '-' + mode
            build = execute(label + '-compile', ['cc', '-std=c11', '-O2', str(tree / 'geometry-web/web_bridge.c'), '-lm', '-o', str(exe)])
            assert build['exit'] == 0, build
            names = gate.ALL['native'] if mode == 'baseline' else case['tests']
            argv = [sys.executable, '-c', gate.NATIVE_CHILD, str(exe), *[gate.NATIVE_MODULE + '.' + gate.NATIVE_CLASS + '.' + name for name in names]]
            test = execute(label + '-test', argv)
            log = (OUTPUT / (label + '-test.log')).read_text()
            record = {'compile': build, 'test': test, 'binary_sha256': gate.sha256(exe),
                      'skips': 'skipped=' in log, 'failures': gate.failures(log)}
            if mode == 'mutant':
                record['verdict'] = gate.verdict(case, test['exit'], log)
            else:
                assert test['exit'] == 0 and not record['skips'], record
            info['runs'][mode] = record
        assert info['runs']['baseline']['binary_sha256'] == info['runs']['restored']['binary_sha256']
        assert info['runs']['baseline']['binary_sha256'] != info['runs']['mutant']['binary_sha256']
        receipt['contexts'][context] = info
receipt['status_after'] = subprocess.check_output(['git', 'status', '--porcelain'], text=True)
(OUTPUT / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
print(json.dumps({c: {m: r['test']['exit'] for m, r in v['runs'].items()} for c, v in receipt['contexts'].items()}))
