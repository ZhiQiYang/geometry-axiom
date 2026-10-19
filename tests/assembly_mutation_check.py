"""Targeted GCC fault injection in a disposable source copy (never edits the checkout).

Run on Linux/WSL: python3 tests/assembly_mutation_check.py
Baseline must pass; each injected guard fault must produce an assertion failure.
Crashes, compiler errors and skips are not counted as detection.

A case is (name, [(file, before, after), ...], killer test). GEO-261 enforces some rules in more than one
layer, so a case may carry one patch per layer: removing a single layer leaves the other one standing and
the fault survives. Where the integration branch has such a rule, the case removes every layer and
reproduces the fault main had. The per-case table (main line, line used now, layers, single-layer controls)
is in geometry-web/docs/ASSEMBLY-RULES-VALIDATION.md.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCOPE = 'geometry-templates/woodworking/native/assembly.c'
BRIDGE = 'geometry-web/engineering_bridge.inc'
CASES = [
    ('conflict', [(SCOPE, 'if(!strcmp(scopes[k],scopes[i]))', 'if(false)')],
     'test_duplicate_scope_and_endpoint_rejected'),
    ('missing-source', [(SCOPE,
     '(resolve&&!(w->evaluation&&w->evaluation->slot_dimension?w->evaluation->slot_dimension(w->evaluation->user,b->id,id,axis,&source,&effective,path,sizeof path):wood_eng_resolve(&w->engineering,&source,&target,UINT32_MAX,0,&effective,path,sizeof path)))',
     'false')],
     'test_bad_dimension_sources_rejected_not_incomplete'),
    # Two layers: the confirm guard on g_preview.ready, and the candidate discard that cancel performs.
    ('cancelled-preview', [(BRIDGE, '||!g_preview.ready||!mine||g_preview.token!=token', '||!mine||g_preview.token!=token'),
                           (BRIDGE, 'if(cancelled){g_preview.ready=false;app_candidate_discard(g_preview.transaction->control);}',
                            'if(cancelled){g_preview.ready=false;}')],
     'test_cancel_and_protocol_tokens_do_not_commit'),
]


def main():
    if os.name != 'posix':
        raise SystemExit('Use GCC on Linux/WSL; no security settings are changed.')
    import resource
    resource.setrlimit(resource.RLIMIT_STACK, (16 * 1024 * 1024, resource.RLIM_INFINITY))
    results = []
    with tempfile.TemporaryDirectory(prefix='assembly-mutations-') as directory:
        source = Path(directory)
        for parent in (ROOT, ROOT / 'geometry-core', ROOT / 'geometry-web', ROOT / 'geometry-app', ROOT / 'geometry-templates'):
            paths = parent.iterdir() if parent == ROOT else parent.rglob('*')
            for path in paths:
                if path.is_file() and path.suffix in ('.c', '.h', '.inc') and 'vendor' not in path.parts:
                    target = source / path.relative_to(ROOT)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)
        for name, patches, test in ([('baseline', [], '')] + CASES + [('baseline-restored', [], '')]):
            originals = {}
            try:
                for filename, before, after in patches:
                    target = source / filename
                    data = target.read_bytes()
                    originals.setdefault(filename, data)
                    assert data.count(before.encode()) == 1, (name, filename, 'mutation anchor changed')
                    target.write_bytes(data.replace(before.encode(), after.encode()))
                exe = source / ('bridge-' + name)
                subprocess.run(['cc', '-std=c11', '-O2', str(source/'geometry-web/web_bridge.c'), '-lm', '-o', str(exe)], check=True)
                tests = ['tests.test_assembly_rules.AssemblyRules.' + (test or c[2]) for c in (CASES if not test else [CASES[0]])]
                # This freshly compiled, deliberately fault-injected harness is
                # caller-owned, not a registry binary from the unmodified ROOT.
                # Use the existing direct BridgeSession(path) contract rather
                # than declaring it a fresh GEOMETRY_TEST_BRIDGE override.
                child = ('import sys, unittest\nfrom unittest.mock import patch\n'
                         'from tests import test_assembly_rules\n'
                         'exe = sys.argv.pop(1)\n'
                         'with patch.object(test_assembly_rules, "find_bridge", return_value=exe):\n'
                         '    unittest.main(module=None)\n')
                run = subprocess.run([sys.executable, '-c', child, str(exe), *tests], cwd=ROOT,
                    capture_output=True, text=True, timeout=120)
                log = run.stdout + run.stderr
                print(name, log, flush=True)
                passed = (run.returncode == 0 and 'skipped=' not in log) if name.startswith('baseline') else (run.returncode == 1 and 'AssertionError' in log and 'errors=' not in log and 'skipped=' not in log)
                results.append({'case': name, 'passed': passed, 'binary_sha256': hashlib.sha256(exe.read_bytes()).hexdigest()})
                if not passed:
                    raise RuntimeError('Fault-injection validation failed: ' + name)
            finally:
                for filename, data in originals.items():
                    (source / filename).write_bytes(data)
    print(json.dumps({'schema':'assembly-mutations/1', 'results':results}, indent=2))


if __name__ == '__main__':
    main()
