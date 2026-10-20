"""Targeted GCC fault injection in a disposable source copy (never edits the checkout).

    python3 tests/assembly_mutation_check.py --out /var/tmp/assembly-mutations   # Linux/WSL, --out must not exist
    python3 tests/assembly_mutation_check.py --check      # static: every case is bound to a live, unique assertion
    python3 tests/assembly_mutation_check.py --selftest   # the verdict rules on synthetic observations

A case is (name, [(file, before, after), ...], killer test, killer tag). GEO-261 enforces some rules in more than
one layer, so a case may carry one patch per layer: removing a single layer leaves the other one standing and the
fault survives. Where the integration branch has such a rule, the case removes every layer and reproduces the
fault main had. The per-case table (main line, line used now, layers, single-layer controls) is in
geometry-web/docs/ASSEMBLY-RULES-VALIDATION.md.

What "killed" means. The killer test is the test method that must fail, the killer tag is the one assertion in it
that must fail: that assertion carries `tests.test_assembly_rules.killer(tag)` as its message, and the failure
record the child writes lists the tags found in the failure message. A case is killed only when

  1. the unmodified build ran the killer tests green, without skips, and executed every tagged assertion;
  2. the fault build ran the killer test and exactly one failure was recorded: in that test, an assertion failure
     (not an error) whose message carries that one tag, with no skip, error, bridge crash, timeout or second failure;
  3. the reverted tree is byte-identical to the unmodified tree, and the rebuilt unmodified bridge is green again
     with the same binary digest as the first.

Any other outcome is `not-killed` with a named reason (survived, wrong-assertion, wrong-test, extra-failures,
error, skipped, bridge-closed, timeout, ...). The earlier rule (exit status 1 and the word AssertionError somewhere
in the output) counted a fault as killed when some other assertion of the test failed; legacy_killed() keeps that
rule only so the negative controls can show what it would have said. A bridge that dies under the test is a recorded
failure too (tests/_bridge.py::BridgeClosed subclasses AssertionError) but carries no tag; it is told apart as
bridge-closed so the receipt says the bridge died, not that an assertion failed.

Negative controls (CONTROLS) are real faults that must NOT be judged killed, each for its named reason. They run the
same build, test and judge as a case.

Receipts go to --out: summary.json, sources.json and, per phase (baseline, cases/*, controls/*, restored), the
patches, build output, test output, the structured test result, the binary digest and the source digests before and
after the revert. Binaries and source copies are not kept. Not part of tests/run_all.py (it compiles one bridge per
phase), like tests/section_profile_mutation_check.py; tests/test_assembly_mutation_check.py runs the parts that need
no compiler.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
SCOPE = 'geometry-templates/woodworking/native/assembly.c'
BRIDGE = 'geometry-web/engineering_bridge.inc'
TEST_FILE = 'tests/test_assembly_rules.py'
TEST_PREFIX = 'tests.test_assembly_rules.AssemblyRules.'
JUDGE_FILES = (TEST_FILE, 'tests/_bridge.py', 'tests/binaries.py', 'tests/assembly_mutation_check.py')
SCHEMA = 'assembly-mutations/2'
TAG = re.compile(r'KILLER\[([^\]\s]+)\]')

CASES = [
    ('conflict', [(SCOPE, 'if(!strcmp(scopes[k],scopes[i]))', 'if(false)')],
     'test_duplicate_scope_and_endpoint_rejected', 'conflict:scope'),
    ('missing-source', [(SCOPE,
     '(resolve&&!(w->evaluation&&w->evaluation->slot_dimension?w->evaluation->slot_dimension(w->evaluation->user,b->id,id,axis,&source,&effective,path,sizeof path):wood_eng_resolve(&w->engineering,&source,&target,UINT32_MAX,0,&effective,path,sizeof path)))',
     'false')],
     'test_bad_dimension_sources_rejected_not_incomplete', 'missing-source:literal-zero'),
    # Two layers: the confirm guard on g_preview.ready, and the candidate discard that cancel performs.
    ('cancelled-preview', [(BRIDGE, '||!g_preview.ready||!mine||g_preview.token!=token', '||!mine||g_preview.token!=token'),
                           (BRIDGE, 'if(cancelled){g_preview.ready=false;app_candidate_discard(g_preview.transaction->control);}',
                            'if(cancelled){g_preview.ready=false;}')],
     'test_cancel_and_protocol_tokens_do_not_commit', 'cancelled-preview:confirm-after-cancel'),
]

# (name, [(file, before, after), ...], case whose killer test and tag it is judged against, reason it must be rejected
#  for[, seconds the test run may take instead of --timeout])
CANCEL = 'bool cancelled=g_preview.ready&&mine&&g_preview.token==token;'
CONTROLS = [
    # A fault in the same test that fails an earlier assertion (assembly-cancel must report cancelled:true).
    # Exit status 1 and an AssertionError in the output: the earlier rule called this killed.
    ('control-wrong-assertion', [(BRIDGE, CANCEL, 'bool cancelled=false;')], 'cancelled-preview', 'wrong-assertion'),
    # The bridge dies while cancelling. BridgeClosed is an AssertionError subclass, so unittest records a failure
    # (not an error) with no tag; the judge names it bridge-closed. The earlier rule did not count this one, since
    # the traceback names BridgeClosed rather than AssertionError.
    ('control-bridge-crash', [(BRIDGE, CANCEL, CANCEL + 'if(cancelled)abort();')], 'cancelled-preview', 'bridge-closed'),
    # The cancel reply is not JSON any more: json.loads raises inside the test, an error rather than a failure.
    ('control-error', [(BRIDGE, 'printf("{\\"ok\\":true,\\"cancelled\\":%s,', 'printf("{ok:true,\\"cancelled\\":%s,')],
     'cancelled-preview', 'error'),
    # The bridge never answers the cancel; the run is killed (process group included) after the 15 s given here.
    ('control-hang', [(BRIDGE, CANCEL, CANCEL + 'if(cancelled)for(;;){}')], 'cancelled-preview', 'timeout', 15),
    # One of the two layers only: the other still refuses the late confirm, so the fault survives (XA1 in
    # ASSEMBLY-RULES-VALIDATION.md).
    ('control-single-layer', [(BRIDGE, '||!g_preview.ready||!mine||g_preview.token!=token', '||!mine||g_preview.token!=token')],
     'cancelled-preview', 'survived'),
]

REASONS = ('survived', 'wrong-assertion', 'wrong-test', 'extra-failures', 'error', 'skipped', 'unexpected-outcome',
           'bridge-closed', 'timeout', 'child-crash', 'child-inconsistent', 'identical-binary')


# ------------------------------------------------------------------ verdicts (pure; no compiler needed)

def legacy_killed(returncode, log):
    """The judgement before 2026-10-20, kept only to show in control receipts what it would have said."""
    return returncode == 1 and 'AssertionError' in log and 'errors=' not in log and 'skipped=' not in log


def judge_pass(obs, selected, tags):
    """Baseline / restored: every selected test ran and passed, nothing skipped, every tagged assertion was executed.

    obs = {'exit': int or None, 'timeout': bool, 'result': child result dict or None}. Returns (verdict, reason)."""
    result = obs['result']
    if obs['timeout']:
        return 'fail', 'timeout'
    if result is None or obs['exit'] not in (0, 1):
        return 'fail', 'child-crash'
    for key, reason in (('failures', 'failures'), ('errors', 'errors'), ('skipped', 'skipped'),
                        ('expectedFailures', 'unexpected-outcome'), ('unexpectedSuccesses', 'unexpected-outcome')):
        if result[key]:
            return 'fail', reason
    if obs['exit'] != 0 or result['run'] != len(selected):
        return 'fail', 'child-inconsistent'
    if not set(tags) <= set(result['reached']):
        return 'fail', 'killer-not-reached'
    return 'pass', 'green'


def judge_mutant(obs, selected, test, tag):
    """The fault build ran `selected` (the killer test alone). Returns ('killed' | 'not-killed', reason)."""
    result = obs['result']
    if obs['timeout']:
        return 'not-killed', 'timeout'
    if result is None or obs['exit'] not in (0, 1):
        return 'not-killed', 'child-crash'
    if result['skipped']:
        return 'not-killed', 'skipped'
    if result['expectedFailures'] or result['unexpectedSuccesses']:
        return 'not-killed', 'unexpected-outcome'
    if result['errors']:
        return 'not-killed', 'error'
    failures = result['failures']
    if any(item.get('bridgeClosed') for item in failures):
        return 'not-killed', 'bridge-closed'
    if not failures:
        if obs['exit'] == 0 and result['run'] == len(selected):
            return 'not-killed', 'survived'
        return 'not-killed', 'child-inconsistent'
    if obs['exit'] != 1 or result['run'] != len(selected):
        return 'not-killed', 'child-inconsistent'
    if len(failures) != 1:
        return 'not-killed', 'extra-failures'
    if failures[0]['test'] != test:
        return 'not-killed', 'wrong-test'
    if failures[0]['tags'] != [tag]:
        return 'not-killed', 'wrong-assertion'
    return 'killed', 'exact-assertion'


# ------------------------------------------------------------------ static binding of tags to the test source

def read_lf(root, relative):
    return (Path(root) / relative).read_bytes().replace(b'\r\n', b'\n').decode('utf-8')


def method_body(text, name):
    """Lines of `def name(` up to the next method of the class, or None unless it is defined exactly once."""
    lines = text.split('\n')
    starts = [i for i, line in enumerate(lines) if re.match(r'    def %s\(' % re.escape(name), line)]
    if len(starts) != 1:
        return None
    end = next((i for i in range(starts[0] + 1, len(lines)) if re.match(r'    def |\S', lines[i])), len(lines))
    return '\n'.join(lines[starts[0]:end])


def binding_problems(test_text, cases=None, controls=None):
    """Problems with the way cases and controls are bound to assertions in the test source (list of strings)."""
    cases = CASES if cases is None else cases
    controls = CONTROLS if controls is None else controls
    problems = []
    names = [case[0] for case in cases] + [control[0] for control in controls]
    problems += ['duplicate case name %s' % name for name in sorted(set(names)) if names.count(name) > 1]
    tags = [case[3] for case in cases]
    problems += ['tag %s is claimed by more than one case' % tag for tag in sorted(set(tags)) if tags.count(tag) > 1]
    for name, patches, test, tag in cases:
        if not patches or any(len(patch) != 3 or patch[1] == patch[2] for patch in patches):
            problems.append('%s: every patch needs a file and a before text that differs from the after text' % name)
        body = method_body(test_text, test)
        if body is None:
            problems.append('%s: test method %s is not defined exactly once' % (name, test))
            continue
        literal = re.compile(r'''(["'])%s\1''' % re.escape(tag))
        if len(literal.findall(test_text)) != 1:
            problems.append('%s: the tag literal %r must occur exactly once in %s' % (name, tag, TEST_FILE))
        elif not literal.search(body):
            problems.append('%s: the tag literal %r is not inside %s' % (name, tag, test))
    known = {case[0] for case in cases}
    for name, patches, target, reason, *_ in controls:
        if target not in known:
            problems.append('%s: unknown case %s' % (name, target))
        if reason not in REASONS:
            problems.append('%s: unknown reason %s' % (name, reason))
        if not patches or any(len(patch) != 3 or patch[1] == patch[2] for patch in patches):
            problems.append('%s: every patch needs a file and a before text that differs from the after text' % name)
    return problems


def anchor_problems(root, cases=None, controls=None):
    """Every patch anchor must occur exactly once when its turn comes (LF form, patches applied in order)."""
    problems = []
    cache = {}
    for entry in (CASES if cases is None else cases) + (CONTROLS if controls is None else controls):
        current = {}
        for relative, before, after in entry[1]:
            if relative not in cache:
                cache[relative] = read_lf(root, relative) if (Path(root) / relative).is_file() else None
            text = current.get(relative, cache[relative])
            count = None if text is None else text.count(before)
            if count != 1:
                problems.append('%s: anchor occurs %s times in %s: %r' % (entry[0], count, relative, before[:80]))
                break
            current[relative] = text.replace(before, after, 1)
    return problems


def static_problems(root=ROOT):
    return binding_problems(read_lf(root, TEST_FILE)) + anchor_problems(root)


# ------------------------------------------------------------------ child: run the killer tests, write a structured result

def recording_result_class():
    """unittest result class that keeps what each outcome was, with the KILLER tags found in a failure message."""
    import traceback
    import unittest

    def entry(test, err=None, **extra):
        item = {'test': test.id()}
        if err is not None:
            kind, exc, tb = err
            message = str(exc)
            item.update(exception='%s.%s' % (kind.__module__, kind.__qualname__), tags=TAG.findall(message),
                        message=message[:4000], bridgeClosed=bool(getattr(exc, 'bridge_closed', False)),
                        returncode=getattr(exc, 'returncode', None),
                        frames=[{'file': Path(f.filename).name, 'line': f.lineno, 'function': f.name,
                                 'text': (f.line or '').strip()} for f in traceback.extract_tb(tb)[-6:]])
        item.update(extra)
        return item

    class Recording(unittest.TextTestResult):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.records = {'failures': [], 'errors': [], 'skipped': [], 'expectedFailures': [], 'unexpectedSuccesses': []}

        def addFailure(self, test, err):
            super().addFailure(test, err)
            self.records['failures'].append(entry(test, err))

        def addError(self, test, err):
            super().addError(test, err)
            self.records['errors'].append(entry(test, err))

        def addSkip(self, test, reason):
            super().addSkip(test, reason)
            self.records['skipped'].append(entry(test, reason=reason))

        def addExpectedFailure(self, test, err):
            super().addExpectedFailure(test, err)
            self.records['expectedFailures'].append(entry(test, err))

        def addUnexpectedSuccess(self, test):
            super().addUnexpectedSuccess(test)
            self.records['unexpectedSuccesses'].append(entry(test))

        def addSubTest(self, test, subtest, err):
            super().addSubTest(test, subtest, err)
            if err is not None:
                key = 'failures' if issubclass(err[0], test.failureException) else 'errors'
                self.records[key].append(entry(test, err, subtest=str(subtest)))

    return Recording


def child_main(argv):
    """--child <bridge exe> <result.json> <test id>...: the standard unittest run plus a structured result."""
    import unittest
    from unittest.mock import patch
    exe, destination, *names = argv
    sys.path.insert(0, str(ROOT))
    from tests import test_assembly_rules as module
    result = None
    try:
        # The freshly compiled, deliberately fault-injected harness is caller-owned, not a registry binary from
        # the unmodified ROOT. Use the existing direct BridgeSession(path) contract rather than declaring it a
        # fresh GEOMETRY_TEST_BRIDGE override.
        runner = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=recording_result_class())
        with patch.object(module, 'find_bridge', return_value=exe):
            result = runner.run(unittest.defaultTestLoader.loadTestsFromNames(names))
    finally:
        if result is not None:
            Path(destination).write_text(json.dumps(dict(
                selected=names, run=result.testsRun, **result.records, reached=sorted(getattr(module, 'REACHED', ())),
                python=sys.version.split()[0]), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


# ------------------------------------------------------------------ the run

def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def collect_sources():
    paths = []
    for parent in (ROOT, ROOT / 'geometry-core', ROOT / 'geometry-web', ROOT / 'geometry-app', ROOT / 'geometry-templates'):
        for path in (parent.iterdir() if parent == ROOT else parent.rglob('*')):
            if path.is_file() and path.suffix in ('.c', '.h', '.inc') and 'vendor' not in path.parts:
                paths.append(path)
    return sorted(paths)


def tree_hashes(base):
    base = Path(base)
    return {p.relative_to(base).as_posix(): sha256(p.read_bytes()) for p in sorted(base.rglob('*')) if p.is_file()}


def digest(hashes):
    return sha256(''.join('%s\0%s\n' % item for item in sorted(hashes.items())).encode())


def run_logged(argv, directory, cwd, env, timeout):
    """Run with stdout and stderr kept in `directory`; on timeout kill the whole process group (the bridge too)."""
    import signal
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    timed_out = False
    with (directory / 'stdout').open('wb') as out, (directory / 'stderr').open('wb') as err:
        try:
            process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=out, stderr=err, start_new_session=True)
        except OSError as exc:
            write(directory / 'execution.json', dict(argv=argv, cwd=str(cwd), exit=None, error=str(exc)))
            return None, False
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except OSError:
                process.kill()
            process.wait()
            code = None
    write(directory / 'execution.json', dict(argv=argv, cwd=str(cwd), exit=code, timedOut=timed_out,
                                              seconds=round(time.monotonic() - started, 2)))
    return code, timed_out


def read_log(directory):
    return ''.join((directory / name).read_text(encoding='utf-8', errors='replace') for name in ('stdout', 'stderr')
                   if (directory / name).is_file())


def run_phase(ctx, directory, name, kind, patches, selected, judge, timeout=None):
    """Patch the source copy, compile, run `selected`, revert. judge(obs, record) -> (verdict, reason)."""
    directory.mkdir(parents=True)
    source, work = ctx['source'], ctx['work']
    record = dict(id=name, kind=kind, tests=selected, patches=[dict(file=f, before=b, after=a) for f, b, a in patches])
    originals = {}
    try:
        for relative, before, after in patches:
            target = source / relative
            data = target.read_bytes()
            originals.setdefault(relative, data)
            if data.count(before.encode()) != 1:
                record.update(verdict='invalid', reason='anchor-changed',
                              detail='%s: %d occurrences' % (relative, data.count(before.encode())))
                return record
            target.write_bytes(data.replace(before.encode(), after.encode()))
        record['patchedFiles'] = {r: dict(before=sha256(originals[r]), after=sha256((source / r).read_bytes())) for r in originals}
        record['sourcesDigest'] = digest(tree_hashes(source))
        exe = work / (kind + '-' + name + '-bridge')
        code, _ = run_logged(['cc', '-std=c11', '-O2', str(source / 'geometry-web/web_bridge.c'), '-lm', '-o', str(exe)],
                             directory / 'build', source, ctx['env'], 900)
        if code != 0 or not exe.is_file():
            record.update(verdict='invalid', reason='compile-failed', buildExit=code)
            return record
        data = exe.read_bytes()
        record.update(binarySha256=sha256(data), binaryBytes=len(data))
        tests = directory / 'tests'
        argv = [sys.executable, '-B', str(Path(__file__).resolve()), '--child', str(exe), str(tests / 'result.json'), *selected]
        code, timed_out = run_logged(argv, tests, ROOT, ctx['env'], timeout or ctx['timeout'])
        try:
            result = json.loads((tests / 'result.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            result = None
        record['exit'] = code
        record['verdict'], record['reason'] = judge(dict(exit=code, timeout=timed_out, result=result), record)
        record['legacyCriterionKilled'] = legacy_killed(code, read_log(tests))
        if result is not None:
            record['observed'] = dict(
                run=result['run'], errors=len(result['errors']), skipped=len(result['skipped']), reached=result['reached'],
                failures=[dict(test=f['test'], tags=f['tags'], exception=f['exception'], bridgeClosed=f['bridgeClosed'],
                               frames=f['frames']) for f in result['failures']])
        return record
    finally:
        for relative, data in originals.items():
            (source / relative).write_bytes(data)
        record['sourcesDigestAfterRevert'] = digest(tree_hashes(source))
        write(directory / 'record.json', record)


def git_output(*args):
    try:
        return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--out', type=Path)
    parser.add_argument('--timeout', type=int, default=120, help='seconds for one test run')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--selftest', action='store_true')
    parser.add_argument('--child', nargs='+')
    args = parser.parse_args(argv)
    if args.child:
        return child_main(args.child)
    if args.selftest:
        failed = selftest()
        print('\n'.join(failed) if failed else 'selftest: %d verdict rules hold' % len(SELFTEST_ROWS))
        return 1 if failed else 0
    problems = static_problems()
    if args.check:
        print('\n'.join(problems) if problems else
              'check: %d cases and %d controls are bound to live assertions and anchors' % (len(CASES), len(CONTROLS)))
        return 1 if problems else 0
    if os.name != 'posix':
        raise SystemExit('Use GCC on Linux/WSL; no security settings are changed.')
    if not args.out:
        parser.error('--out is required')
    if problems:
        print('\n'.join(problems))
        return 2
    import resource
    resource.setrlimit(resource.RLIMIT_STACK, (16 * 1024 * 1024, resource.RLIM_INFINITY))
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = time.time()
    originals = {str(p.relative_to(ROOT)): p.read_bytes() for p in collect_sources()}
    killers = [TEST_PREFIX + name for name in dict.fromkeys(case[2] for case in CASES)]
    tags = [case[3] for case in CASES]
    env = {k: v for k, v in os.environ.items() if k not in ('GEOMETRY_TEST_BRIDGE', 'GEOMETRY_ENGINEERING_BRIDGE')}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    cc = subprocess.run(['cc', '--version'], capture_output=True, text=True)
    summary = dict(
        schema=SCHEMA, ok=False, startedAt=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(started)),
        git=dict(head=git_output('rev-parse', 'HEAD'),
                 dirty=git_output('status', '--porcelain', '--', 'tests', 'geometry-core', 'geometry-web', 'geometry-app',
                                  'geometry-templates', 'current_geometry.c') != ''),
        environment=dict(cc=(cc.stdout.splitlines() or [''])[0], python=sys.version.split()[0], platform=platform.platform()),
        tool=sha256((ROOT / 'tests/assembly_mutation_check.py').read_bytes()),
        judge={f: sha256((ROOT / f).read_bytes()) for f in JUDGE_FILES},
        sourcesDigest=digest({k: sha256(v) for k, v in originals.items()}), problems=[])
    write(out / 'sources.json', {k: sha256(v) for k, v in originals.items()})

    def progress(record):
        failure = ((record.get('observed') or {}).get('failures') or [{}])[0].get('tags', '')
        print('%-26s %-10s %-20s %s' % (record['id'], record.get('verdict'), record.get('reason', ''), failure or ''), flush=True)

    with tempfile.TemporaryDirectory(prefix='assembly-mutations-') as directory:
        work = Path(directory)
        source = work / 'source'
        for relative, data in originals.items():
            (source / relative).parent.mkdir(parents=True, exist_ok=True)
            (source / relative).write_bytes(data)
        ctx = dict(source=source, work=work, env=env, timeout=args.timeout)
        baseline_digest = digest(tree_hashes(source))

        def pass_phase(name):
            return run_phase(ctx, out / name, name, name, [], killers, lambda obs, record: judge_pass(obs, killers, tags))

        baseline = pass_phase('baseline')
        progress(baseline)
        summary['baseline'] = baseline
        if baseline.get('verdict') != 'pass':
            summary['problems'].append('baseline is not green: %s' % baseline.get('reason'))
            write(out / 'summary.json', summary)
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 2

        def mutant(name, kind, patches, case, expected_reason, timeout=None):
            test, tag = TEST_PREFIX + case[2], case[3]

            def judge(obs, record):
                if record.get('binarySha256') == baseline['binarySha256']:
                    return 'not-killed', 'identical-binary'
                return judge_mutant(obs, [test], test, tag)
            record = run_phase(ctx, out / kind / name, name, kind, patches, [test], judge, timeout)
            record['expectedTest'], record['expectedTag'] = test, tag
            if kind == 'controls':
                record['expectedReason'] = expected_reason
                record['controlOk'] = record.get('verdict') == 'not-killed' and record.get('reason') == expected_reason
            write(out / kind / name / 'record.json', record)
            progress(record)
            return record

        by_name = {case[0]: case for case in CASES}
        summary['cases'] = [mutant(case[0], 'cases', case[1], case, None) for case in CASES]
        summary['controls'] = [mutant(c[0], 'controls', c[1], by_name[c[2]], c[3], *c[4:]) for c in CONTROLS]
        restored = pass_phase('restored')
        progress(restored)
        summary['restored'] = restored

        phases = [baseline, *summary['cases'], *summary['controls'], restored]
        summary['originalSourcesUnchanged'] = all((ROOT / k).read_bytes() == v for k, v in originals.items())
        summary['restoredBinaryMatchesBaseline'] = restored.get('binarySha256') == baseline.get('binarySha256')
        summary['problems'] += ['case %s was not killed: %s' % (r['id'], r.get('reason')) for r in summary['cases']
                                if r.get('verdict') != 'killed']
        summary['problems'] += ['control %s was judged %s/%s, expected not-killed/%s' % (
            r['id'], r.get('verdict'), r.get('reason'), r.get('expectedReason')) for r in summary['controls'] if not r.get('controlOk')]
        if restored.get('verdict') != 'pass':
            summary['problems'].append('restored build is not green: %s' % restored.get('reason'))
        if not summary['restoredBinaryMatchesBaseline']:
            summary['problems'].append('restored binary differs from the baseline binary')
        drifted = [r['id'] for r in phases if r.get('sourcesDigestAfterRevert') != baseline_digest]
        if drifted:
            summary['problems'].append('source tree differs from the baseline after revert in: %s' % ', '.join(drifted))
        if not summary['originalSourcesUnchanged']:
            summary['problems'].append('the checkout sources changed during the run')
    summary['ok'] = not summary['problems']
    summary['seconds'] = round(time.time() - started, 1)
    write(out / 'summary.json', summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in ('baseline', 'cases', 'controls', 'restored')},
                     ensure_ascii=False, indent=2))
    return 0 if summary['ok'] else 1


# ------------------------------------------------------------------ selftest of the verdict rules

TEST = TEST_PREFIX + 'test_x'
TAGGED = dict(test=TEST, tags=['t:a'], exception='builtins.AssertionError', bridgeClosed=False, frames=[])


def _result(failures=(), errors=(), skipped=(), expected=(), unexpected=(), run=1, reached=('t:a',)):
    return dict(run=run, failures=list(failures), errors=list(errors), skipped=list(skipped),
                expectedFailures=list(expected), unexpectedSuccesses=list(unexpected), reached=list(reached))


def _obs(result, exit=1, timeout=False):
    return dict(exit=exit, timeout=timeout, result=result)


SELFTEST_ROWS = [
    ('exact assertion', 'mutant', _obs(_result([TAGGED])), ('killed', 'exact-assertion')),
    ('survived', 'mutant', _obs(_result(), exit=0), ('not-killed', 'survived')),
    ('other assertion of the same test', 'mutant', _obs(_result([dict(TAGGED, tags=[])])), ('not-killed', 'wrong-assertion')),
    ('another tagged assertion', 'mutant', _obs(_result([dict(TAGGED, tags=['t:b'])])), ('not-killed', 'wrong-assertion')),
    ('two tags in one failure', 'mutant', _obs(_result([dict(TAGGED, tags=['t:a', 't:b'])])), ('not-killed', 'wrong-assertion')),
    ('right tag, other test', 'mutant', _obs(_result([dict(TAGGED, test=TEST + '2')])), ('not-killed', 'wrong-test')),
    ('exact assertion plus a second failure', 'mutant', _obs(_result([TAGGED, dict(TAGGED, tags=[])])), ('not-killed', 'extra-failures')),
    ('exact assertion plus an error', 'mutant', _obs(_result([TAGGED], errors=[dict(TAGGED)])), ('not-killed', 'error')),
    ('error only', 'mutant', _obs(_result(errors=[dict(TAGGED, exception='json.JSONDecodeError')])), ('not-killed', 'error')),
    ('skipped', 'mutant', _obs(_result(skipped=[dict(test=TEST, reason='no bridge')]), exit=0), ('not-killed', 'skipped')),
    ('skipped beside the exact failure', 'mutant', _obs(_result([TAGGED], skipped=[dict(test=TEST)])), ('not-killed', 'skipped')),
    ('bridge died', 'mutant', _obs(_result([dict(TAGGED, tags=[], bridgeClosed=True, returncode=-6)])), ('not-killed', 'bridge-closed')),
    ('bridge died carrying the tag', 'mutant', _obs(_result([dict(TAGGED, bridgeClosed=True, returncode=-11)])), ('not-killed', 'bridge-closed')),
    ('unexpected success', 'mutant', _obs(_result(unexpected=[dict(test=TEST)])), ('not-killed', 'unexpected-outcome')),
    ('timeout', 'mutant', _obs(None, exit=None, timeout=True), ('not-killed', 'timeout')),
    ('no result file', 'mutant', _obs(None, exit=1), ('not-killed', 'child-crash')),
    ('killed by a signal', 'mutant', _obs(_result([TAGGED]), exit=-9), ('not-killed', 'child-crash')),
    ('exit 1 without a recorded failure', 'mutant', _obs(_result(), exit=1), ('not-killed', 'child-inconsistent')),
    ('exit 0 with a failure', 'mutant', _obs(_result([TAGGED]), exit=0), ('not-killed', 'child-inconsistent')),
    ('no test ran', 'mutant', _obs(_result(run=0), exit=0), ('not-killed', 'child-inconsistent')),
    ('green', 'pass', _obs(_result(), exit=0), ('pass', 'green')),
    ('green but the tagged assertion never ran', 'pass', _obs(_result(reached=[]), exit=0), ('fail', 'killer-not-reached')),
    ('red baseline', 'pass', _obs(_result([TAGGED])), ('fail', 'failures')),
    ('baseline with a skip', 'pass', _obs(_result(skipped=[dict(test=TEST)]), exit=0), ('fail', 'skipped')),
    ('baseline with an error', 'pass', _obs(_result(errors=[dict(test=TEST)])), ('fail', 'errors')),
    ('baseline timeout', 'pass', _obs(None, exit=None, timeout=True), ('fail', 'timeout')),
    ('baseline ran fewer tests', 'pass', _obs(_result(run=0), exit=0), ('fail', 'child-inconsistent')),
]


def selftest():
    """The rows above through the judges; returns the rows that came out differently, and reasons with no row."""
    failed = []
    for label, role, obs, expected in SELFTEST_ROWS:
        actual = judge_mutant(obs, [TEST], TEST, 't:a') if role == 'mutant' else judge_pass(obs, [TEST], ['t:a'])
        if actual != expected:
            failed.append('%s: %s, expected %s' % (label, actual, expected))
    covered = {expected[1] for _, role, _, expected in SELFTEST_ROWS if role == 'mutant'}
    failed += ['no selftest row for reason %s' % reason for reason in REASONS if reason not in covered and reason != 'identical-binary']
    return failed


if __name__ == '__main__':
    raise SystemExit(main())
