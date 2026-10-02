"""Targeted GCC fault injection in a disposable source copy (never edits the checkout).

Run on Linux/WSL: python3 tests/assembly_mutation_check.py
Baseline must pass; each injected guard fault must produce an assertion failure.
Crashes, compiler errors and skips are not counted as detection.
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
CASES = [
    ('conflict', 'geometry-core/assembly.inc',
     'if(!strcmp(scopes[k],scopes[i]))', 'if(false)',
     'test_duplicate_scope_and_endpoint_rejected'),
    ('missing-source', 'geometry-core/assembly.inc',
     '(resolve&&!eng_resolve(w,&source,&target,UINT32_MAX,0,&effective,path,sizeof path))', 'false',
     'test_bad_dimension_sources_rejected_not_incomplete'),
    ('cancelled-preview', 'geometry-web/engineering_bridge.inc',
     '||!g_preview.ready||!mine||g_preview.token!=token', '||!mine||g_preview.token!=token',
     'test_cancel_and_protocol_tokens_do_not_commit'),
    ('allocator-exhaustion', 'geometry-web/assembly_bridge.inc',
     'if(high==UINT32_MAX)', 'if(false)',
     'test_uint32_exhaustion_never_wraps_into_formal_or_reserved_ids'),
    ('binding-create-only', 'geometry-core/assembly.inc',
     'if(assembly_binding(w,id))', 'if(false)',
     'test_new_binding_cannot_overwrite_existing_formal_identity'),
    ('allocator-namespace', 'current_geometry.c',
     'bool same_namespace = w->allocation_namespace == snap->allocation_namespace;',
     'bool same_namespace = true;',
     'test_cross_project_history_keeps_separate_allocator_namespaces'),
    ('required-identity', 'current_geometry.c',
     'if (ok && g_assembly_file_identity_required && !g_assembly_file_identity_seen)',
     'if (false)',
     'test_identity_capability_requires_one_record_and_cannot_be_reset'),
]


def main():
    if os.name != 'posix':
        raise SystemExit('Use GCC on Linux/WSL; no security settings are changed.')
    import resource
    resource.setrlimit(resource.RLIMIT_STACK, (16 * 1024 * 1024, resource.RLIM_INFINITY))
    results = []
    with tempfile.TemporaryDirectory(prefix='assembly-mutations-') as directory:
        source = Path(directory)
        for parent in (ROOT, ROOT / 'geometry-core', ROOT / 'geometry-web'):
            paths = parent.iterdir() if parent == ROOT else parent.rglob('*')
            for path in paths:
                if path.is_file() and path.suffix in ('.c', '.h', '.inc') and 'vendor' not in path.parts:
                    target = source / path.relative_to(ROOT)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)
        for name, filename, before, after, test in [('baseline', '', '', '', '')] + CASES:
            target = source / filename if filename else None
            if target:
                original = target.read_bytes()
                assert original.count(before.encode()) == 1, (name, 'mutation anchor changed')
                target.write_bytes(original.replace(before.encode(), after.encode()))
            try:
                exe = source / ('bridge-' + name)
                subprocess.run(['cc', '-std=c11', '-O2', str(source/'geometry-web/web_bridge.c'), '-lm', '-o', str(exe)], check=True)
                tests = ['tests.test_assembly_rules.AssemblyRules.' + (test or c[4]) for c in (CASES if not test else [CASES[0]])]
                run = subprocess.run([sys.executable, '-m', 'unittest', *tests], cwd=ROOT,
                    env={**os.environ, 'GEOMETRY_TEST_BRIDGE': str(exe)}, capture_output=True, text=True, timeout=120)
                log = run.stdout + run.stderr
                print(name, log, flush=True)
                passed = run.returncode == 0 if name == 'baseline' else (run.returncode == 1 and 'AssertionError' in log and 'errors=' not in log and 'skipped=' not in log)
                results.append({'case': name, 'passed': passed, 'binary_sha256': hashlib.sha256(exe.read_bytes()).hexdigest()})
                if not passed:
                    raise RuntimeError('Fault-injection validation failed: ' + name)
            finally:
                if target:
                    target.write_bytes(original)
    print(json.dumps({'schema':'assembly-mutations/1', 'results':results}, indent=2))


if __name__ == '__main__':
    main()
