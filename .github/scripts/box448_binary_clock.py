from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import hashlib
import io
import inspect
import json
import os
import subprocess
import sys
import types
import unittest

BASE = 'b3c4b981bb96b118c1c05b7a1bd98062d710c8b2'
CANDIDATE = '37800a5f11865024bf98e487019131ab460f0918'
ROOT = Path.cwd()
OUT = Path(os.environ['RUNNER_TEMP']) / 'box448-binary-clock'
TEXT = 'tests/test_binaries.py'
HOST = 'test_host_and_template_source_bytes_invalidate_native_freshness'
NO_WRITE = 'test_compile_and_launch_failure_leave_no_fresh_credentials'
MATCH = ('geometry-templates/woodworking/native', '.h')
OUT.mkdir()
sys.path.insert(0, str(ROOT / 'tests'))
import binaries


def git(*args):
    return subprocess.check_output(['git', *args])


def text_blob(sha, path):
    return git('show', sha + ':' + path)


def test_module(contents, label):
    mod = types.ModuleType(label)
    mod.__file__ = str(ROOT / TEXT)
    exec(compile(contents, mod.__file__, 'exec'), mod.__dict__)
    return mod


def run(label, case):
    stream = io.StringIO()
    with redirect_stdout(stream):
        result = unittest.TextTestRunner(stream, verbosity=2).run(case)
    output = stream.getvalue()
    (OUT / (label + '.log')).write_text(output, encoding='utf8')
    return dict(exit=0 if result.wasSuccessful() else 1, count=result.testsRun,
                failures=[(str(test), str(detail)) for test, detail in result.failures],
                errors=[(str(test), str(detail)) for test, detail in result.errors],
                skipped=[(str(test), reason) for test, reason in result.skipped])


def clock_trial(sha, label):
    case = test_module(text_blob(sha, TEXT), label).BinaryFreshnessTests(HOST)
    raw_write = Path.write_bytes
    fake = case.fake_compile
    ticks = []
    calls = []
    last = None
    stamp = 1_750_000_000

    def implicit_write(path, data):
        nonlocal last, stamp
        written = raw_write(path, data)
        if hasattr(case, 'b') and path == case.b.path:
            params = case._subtest.params
            key = (params['directory'], params['suffix'])
            # 所有間隔為兩秒。只有被回報那組的兩次假連結落在同一刻。
            if key != MATCH or key != last:
                stamp += 2
            last = key
            os.utime(path, (stamp, stamp))
            ticks.append((key, path.stat().st_mtime_ns))
        return written

    def measured(binary, source):
        before = binary.path.stat().st_mtime_ns if binary.path.exists() else None
        outcome = fake(binary, source)
        params = case._subtest.params
        calls.append(dict(directory=params['directory'], suffix=params['suffix'],
                          before=before, after=binary.path.stat().st_mtime_ns, compilerExit=outcome[0]))
        return outcome

    with patch.object(Path, 'write_bytes', implicit_write), patch.object(case, 'fake_compile', measured):
        result = run(label, case)
    result.update(sha=sha, ticks=ticks, compilerCalls=calls)
    return result


assert git('rev-parse', 'HEAD').decode().strip() == CANDIDATE
assert git('rev-parse', 'HEAD^').decode().strip() == BASE
assert git('diff', '--name-only', BASE, CANDIDATE).decode().splitlines() == [TEXT]
source = text_blob(CANDIDATE, TEXT)
before = clock_trial(BASE, 'old')
after = clock_trial(CANDIDATE, 'fixed')
print('修前／修後退出', before['exit'], after['exit'])
assert before['exit'] == 1 and not before['errors'] and len(before['failures']) == 1
name, trace = before['failures'][0]
assert MATCH[0] in name and "suffix='.h'" in name
assert 'AssertionError: False is not true : 回傳碼 0，且 exe 的 mtime 沒有更新' in trace
assert after['exit'] == 0 and not after['skipped']
assert before['ticks'] == after['ticks']
for row in (before, after):
    observed = [c for c in row['compilerCalls'] if (c['directory'], c['suffix']) == MATCH]
    assert len(observed) == 2 and all(c['compilerExit'] == 0 for c in observed)
    reread = observed[1]
    assert (reread['before'] == reread['after']) == (row is before)

mod = test_module(source, 'guard')
gate_before = run('strict-baseline', mod.BinaryFreshnessTests(NO_WRITE))
original = inspect.getsource(binaries._build_one)
needle = 'if code != 0 or not exists or (before is not None and after == before):'
assert original.count(needle) == 1
mutant = original.replace(needle, 'if code != 0 or not exists:')
ns = {}
exec(compile(mutant, str(ROOT / 'tests/binaries.py'), 'exec'), binaries.__dict__, ns)
with patch.object(binaries, '_build_one', ns['_build_one']):
    gate_retraction = run('strict-withdrawn', mod.BinaryFreshnessTests(NO_WRITE))
gate_after = run('strict-restored', mod.BinaryFreshnessTests(NO_WRITE))
assert [r['exit'] for r in (gate_before, gate_retraction, gate_after)] == [0, 1, 0]
assert not gate_retraction['errors'] and len(gate_retraction['failures']) == 1
assert "'built' != 'compile-failed'" in gate_retraction['failures'][0][1]

suites = unittest.defaultTestLoader.loadTestsFromModule(test_module(source, 'candidate_suite'))
full = run('full', suites)
assert full['count'] == 36 and full['exit'] == 0 and not full['skipped']
receipt = dict(schema=1, source=BASE, candidate=CANDIDATE, tree=git('rev-parse','HEAD^{tree}').decode().strip(),
               path=TEXT, runner=sys.version, mtimeModel='兩秒示意檔案系統時鐘、目標子測試兩次假連結位於同一刻',
               sourceSha256=hashlib.sha256(text_blob(BASE,TEXT)).hexdigest(),
               candidateSha256=hashlib.sha256(source).hexdigest(),
               buildJudgeSha256=hashlib.sha256(text_blob(CANDIDATE,'tests/binaries.py')).hexdigest(),
               old=before, fixed=after, guardBaseline=gate_before, guardWithdrawn=gate_retraction,
               guardRestored=gate_after, fullSuite=full)
(OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding='utf8')
assert not git('diff','--name-only','HEAD').strip()
print('粗時鐘 1/0，原 mtime 守門 0/1/0，正式夾具全套 36/36。')
