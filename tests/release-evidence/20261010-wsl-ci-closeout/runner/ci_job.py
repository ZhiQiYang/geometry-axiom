#!/usr/bin/env python3
"""Run ONE job of the repository's own CI workflow (read from the checked-out SHA) inside WSL.

Faithful to the yml: the job's env, matrix substitution and every `run:` step are taken from
<repo>/.github/workflows/integration-tests.yml of the SHA under test.  Mechanical, documented
deviations only:
  * actions/checkout        -> replaced by the already checked-out clean clone
  * actions/upload-artifact -> skipped (nothing to upload to), recorded
  * apt-get/sudo steps      -> skipped only if every package is already installed (recorded);
                               otherwise the job is BLOCKED (no sudo is ever attempted)
  * /tmp/ paths and the service port are rewritten per job so that two jobs can run side by side
    (TMPDIR is also set per job, so os.tmpdir() / tempfile follow).
Referee rules decided by the main loop (also written into every receipt README):
  1. timeout   : hard watchdog = the SHA's yml `timeout-minutes` x 3 (WSL is slower than a CI runner; the CI limit is an
                 infrastructure limit, not a correctness referee).  Elapsed time is recorded as-is; exceeding the CI limit
                 is flagged "over CI limit (WSL)" and is NOT red by itself.  Hitting the x3 watchdog (exit 124) is red.
  2. flaky     : (native job only) when run_all.py ends with failing suites, every failing suite is re-run ALONE in the same
                 clone (`run_all.py --only <suite>`, same private /tmp/geometry-tests, up to --rerun-max = 2 attempts).
                 A failing suite is excused ("flaky-rerun-pass") only if a re-run passes (exit 0, row ok, same test count)
                 AND every failed test id of that suite also failed in a MAIN baseline receipt (--baseline-src).
                 Anything else stays red.  Browser jobs have no per-test identity and are never excused.
  3. exclusive : handled by ci_run.py (waits for other sessions' compile/test processes, records them, samples during the run).
Never pushes, never touches the source repository.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import shlex
import signal
import subprocess
import sys
import time

import yaml

SAFE_PATH = '/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
EXIT_BLOCKED = 78
EXIT_INFRA = 70
EXIT_WATCHDOG = 124


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


class Blocked(Exception):
    pass


def load_spec(repo, name):
    wf = yaml.safe_load((repo / '.github/workflows/integration-tests.yml').read_text(encoding='utf-8'))
    jobs = wf['jobs']
    if name in jobs and 'strategy' not in jobs[name]:
        return name, jobs[name], {}
    for key, job in jobs.items():
        for entry in (((job.get('strategy') or {}).get('matrix') or {}).get('include') or []):
            if entry.get('suite') == name:
                return key, job, entry
    raise Blocked('job %r not found in the SHA\'s workflow' % name)


def subst(text, matrix):
    def rep(m):
        expr = m.group(1).strip()
        mm = re.fullmatch(r'matrix\.(\w+)', expr)
        if mm and mm.group(1) in matrix:
            return str(matrix[mm.group(1)])
        raise Blocked('unhandled expression ${{ %s }}' % expr)
    return re.sub(r'\$\{\{(.*?)\}\}', rep, str(text))


def rewrite(text, jobtmp, old_port, new_port):
    text = re.sub(r'(?<![\w/.\-])/tmp/', jobtmp.rstrip('/') + '/', text)
    if old_port:
        text = re.sub(r'(?<!\d)%s(?!\d)' % re.escape(str(old_port)), str(new_port), text)
    return text


def dpkg_installed(pkg):
    r = subprocess.run(['dpkg-query', '-W', '-f=${Status} ${Version}', pkg], capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.startswith('install ok installed'), r.stdout.strip()


def apt_step(run):
    """Return (installed_report) if the step is a pure apt-get step whose packages are all installed; else raise Blocked."""
    lines = [l.strip() for l in run.splitlines() if l.strip() and not l.strip().startswith('#')]
    other = [l for l in lines if 'apt-get' not in l]
    if other:
        raise Blocked('step mixes apt-get/sudo with other commands; needs manual review: %r' % other[:3])
    pkgs = []
    for l in lines:
        if re.search(r'\binstall\b', l):
            after = l.split('install', 1)[1]
            pkgs += [t for t in shlex.split(after) if not t.startswith('-')]
    if not pkgs:
        raise Blocked('apt-get step without a recognisable install list; needs manual review')
    report, missing = {}, []
    for p in pkgs:
        ok, info = dpkg_installed(p)
        report[p] = info
        if not ok:
            missing.append(p)
    if missing:
        raise Blocked('apt packages missing in WSL (would need sudo, never attempted): %s' % ', '.join(missing))
    return report


def kill_tagged(tag):
    """Kill processes whose environment carries our unique tag (they are provably ours). Returns descriptions."""
    killed = []
    me = os.getpid()
    victims = []
    for entry in os.listdir('/proc'):
        if not entry.isdigit() or int(entry) == me:
            continue
        try:
            env = pathlib.Path('/proc/%s/environ' % entry).read_bytes()
        except OSError:
            continue
        if ('WSL_CI_JOB_TAG=' + tag).encode() in env.split(b'\0'):
            try:
                cmd = pathlib.Path('/proc/%s/cmdline' % entry).read_bytes().replace(b'\0', b' ').decode('utf-8', 'replace')[:120]
            except OSError:
                cmd = '?'
            victims.append((int(entry), cmd))
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid, cmd in victims:
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
            except PermissionError:
                pass
        if sig == signal.SIGTERM and victims:
            time.sleep(2)
    for pid, cmd in victims:
        killed.append('%d %s' % (pid, cmd))
    return killed


# ------------------------------------------------------------------ result parsing

ROW = re.compile(r'^(\S+)\s+(\d+|-)\s+(\S+)\s+(\S+)\s+(\S+)\s+([\d.]+|-)\s*(.*)$')


def parse_native(text):
    out = {}
    rows, in_table = [], False
    for line in text.splitlines():
        if line.startswith('suite ') and '測試數' in line:
            in_table = True
            continue
        if in_table:
            if line.startswith('-----'):
                continue
            if line.startswith('合計'):
                m = re.match(r'^合計\S*\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)', line)
                if m:
                    out['totals'] = dict(total=int(m[1]), passed=int(m[2]), failed=int(m[3]), skipped=int(m[4]), seconds=float(m[5]))
                in_table = False
                continue
            m = ROW.match(line)
            if m:
                rows.append(dict(suite=m[1], total=m[2], passed=m[3], failed=m[4], skipped=m[5], seconds=m[6], note=m[7].strip()))
    out['rows'] = rows
    m = re.findall(r'^exit (\d+)：(.*)$', text, re.M)
    if m:
        out['run_all_exit'] = int(m[-1][0])
        out['run_all_meaning'] = m[-1][1]
    out['suites_ran'] = len([r for r in rows if r['total'] != '-' or r['passed'] == 'ok'])
    detail, grab = [], False
    for line in text.splitlines():
        if line.startswith('失敗明細'):
            grab = True
            continue
        if grab:
            if line.startswith('  '):
                detail.append(line.rstrip())
            else:
                grab = False
    out['failure_details'] = detail[:60]
    out['failed_suites'] = [r['suite'] for r in rows if r['failed'] not in ('0', '-') or r['note'].startswith('環境')]
    out['unittest_fail_lines'] = [l.strip() for l in text.splitlines() if re.match(r'^\s*(FAIL|ERROR):', l)][:30]
    return out


def last_json(text, marker):
    found = None
    for line in text.splitlines():
        i = line.find(marker + ' ')
        if i == 0 or (i > 0 and not line[:i].strip()):
            try:
                found = json.loads(line[i + len(marker) + 1:])
            except ValueError:
                pass
    return found


def parse_browser(text):
    out = {}
    cdp = last_json(text, 'CDP_RESULT')
    space = last_json(text, 'SPACE_RESULT')
    docs = last_json(text, 'DOCUMENTS_RESULT')
    if cdp is not None:
        out.update(kind='cdp', passed=cdp.get('passedAssertions'), failed=cdp.get('failedAssertions'), completed=cdp.get('completed'),
                   skipped_groups=cdp.get('skipped'), scope=(cdp.get('scope') or {}).get('mode'), golden=cdp.get('goldenCompare'),
                   uncaught_browser_exceptions=cdp.get('uncaughtBrowserExceptions'), fatal=cdp.get('fatal'),
                   sections_failed=cdp.get('sectionsFailed'))
    elif space is not None:
        out.update(kind='space', passed=space.get('passed'), failed=space.get('failed'), completed=space.get('completed'),
                   scope=(space.get('scope') or {}).get('mode'), skipped_groups=(space.get('scope') or {}).get('omitted'),
                   exceptions=space.get('exceptions'), console_errors=space.get('consoleErrors'))
    elif docs is not None:
        out.update(kind='documents', passed=docs.get('passedAssertions'), failed=docs.get('failedAssertions'), completed=True)
    bad = [l.strip()[:200] for l in text.splitlines() if '✗' in l][:40]
    out['failed_assertion_lines'] = bad
    return out


# ------------------------------------------------------------------ rule 2: single-suite re-run of failed suites (native job only)

def safe_name(suite):
    return suite.replace(':', '_')


def load_suite_json(logdir, suite):
    try:
        return json.loads((pathlib.Path(logdir) / (safe_name(suite) + '.json')).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def failure_ids(suite, data):
    """Identity of a suite's failures: '<suite>::<unittest test id>'.  '<suite>::*' (suite level only) when no per-test information
    explains the failure (non-unittest suite, import error, setUpClass/tearDown error, counts the listed tests do not explain)."""
    ids = []
    for f in (data or {}).get('failures', []):
        tid = '%s::%s' % (suite, f.get('test'))
        if f.get('test') and tid not in ids:
            ids.append(tid)
    if (not data or data.get('failed', 0) != len(ids) or data.get('import_error') or data.get('blocked_by_error')
            or data.get('extra_errors')):
        ids.append(suite + '::*')
    return ids


SUITE_FILE = re.compile(r'^(py|node|c|core|mutation|extra)_(.+)$')


def baseline_index(sources):
    """{failure id: [evidence]} from MAIN baseline receipt dirs (first runs and re-runs): every run_all-logs/*.json that lists failures,
    plus suite-level failures (suites without such a json) from <dir>/native/result.json."""
    index = {}
    for src in sources:
        src = pathlib.Path(src)
        try:
            sha = json.loads((src / 'receipt.json').read_text(encoding='utf-8')).get('head_sha')
        except (OSError, ValueError):
            sha = None
        have_json = set()
        for jp in sorted(src.glob('**/run_all-logs/*.json')):
            try:
                data = json.loads(jp.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                continue
            m = SUITE_FILE.match(jp.stem)
            if not m or not isinstance(data, dict) or 'failures' not in data:
                continue
            suite = '%s:%s' % (m[1], m[2])
            have_json.add(suite)
            if not data.get('failed'):
                continue
            msgs = {f.get('test'): f.get('message') for f in data.get('failures', [])}
            for i in failure_ids(suite, data):
                index.setdefault(i, []).append(dict(receipt=src.name, sha=sha, file=str(jp.relative_to(src)), message=msgs.get(i.split('::', 1)[1])))
        rj = src / 'native' / 'result.json'
        if rj.exists():
            try:
                parsed = json.loads(rj.read_text(encoding='utf-8')).get('parsed') or {}
            except ValueError:
                parsed = {}
            for suite in parsed.get('failed_suites') or []:
                if suite not in have_json:
                    index.setdefault(suite + '::*', []).append(dict(receipt=src.name, sha=sha, file='native/result.json', message='suite-level failure'))
    return index


def rerun_suite(jobtmp, repo, senv, base_run, suite, attempt, out, first_total, timeout_s=900):
    """Run ONE suite alone (run_all.py --only <suite>) in the same clone, same private /tmp/geometry-tests.  Never raises."""
    safe = safe_name(suite)
    rdir = out / 'reruns'
    rdir.mkdir(parents=True, exist_ok=True)
    # the real step is exactly `python3 tests/run_all.py --build`; anything after --build on that line (harness runs) is replaced as well
    run = re.sub(r'tests/run_all\.py\s+--build[^\n]*', lambda m: 'tests/run_all.py --only %s' % shlex.quote(suite), base_run)
    if run == base_run:
        return dict(attempt=attempt, passed=False, note='cannot derive a single-suite command from the failing step (no "tests/run_all.py --build")')
    logdir = jobtmp / 'geometry-tests' / 'run_all-logs'
    for p in logdir.glob(safe + '.*'):  # the first run's files were already saved; stale files must not be mistaken for this re-run's
        p.unlink()
    script = jobtmp / '_steps' / ('rerun_%s_%d.sh' % (safe, attempt))
    script.write_text(run if run.endswith('\n') else run + '\n', encoding='utf-8', newline='\n')
    rlog = rdir / ('%s.attempt%d.log' % (safe, attempt))
    argv = ['unshare', '-m', '--propagation', 'private', 'bash', str(jobtmp / '_steps' / 'ns_wrap.sh'), str(jobtmp / 'geometry-tests'),
            'bash', '-e', str(script)]
    t = time.time()
    with open(rlog, 'wb') as lf:
        p = subprocess.Popen(argv, cwd=str(repo), env=senv, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            code = p.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()
            code = EXIT_WATCHDOG
    try:
        os.killpg(p.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    seconds = round(time.time() - t, 1)
    dest = rdir / ('%s.attempt%d' % (safe, attempt)) / 'run_all-logs'
    dest.mkdir(parents=True, exist_ok=True)
    import shutil
    for q in logdir.glob(safe + '.*'):
        shutil.copy2(q, dest / q.name)
    text = rlog.read_text(encoding='utf-8', errors='replace')
    parsed = parse_native(text)
    row = next((r for r in parsed.get('rows', []) if r['suite'] == suite), None)
    data = load_suite_json(logdir, suite)
    why = []
    if code != 0:
        why.append('re-run exit %s (run_all: %s)' % (code, parsed.get('run_all_meaning')))
    if row is None:
        why.append('suite row missing in re-run output')
    elif row['failed'] not in ('0', '-') or row['note'].startswith('環境'):
        why.append('suite row not clean: failed=%s note=%s' % (row['failed'], row['note'][:80]))
    if data is not None and (data.get('failed') != 0 or (first_total is not None and data.get('total') != first_total)):
        why.append('json: failed=%s total=%s (first run total %s)' % (data.get('failed'), data.get('total'), first_total))
    return dict(attempt=attempt, passed=not why, exit_code=code, seconds=seconds, why=why, log=str(rlog),
                row=row and dict(total=row['total'], passed=row['passed'], failed=row['failed'], skipped=row['skipped']))


def flaky_analysis(jobtmp, repo, senv, base_run, out, saved_logdir, text, baseline_sources, rerun_max):
    """Rule 2.  Returns the `flaky` block of result.json; `qualifies` is True only if EVERY failing suite is excused."""
    parsed = parse_native(text)
    res = dict(rerun_max=rerun_max, baseline_sources=[str(s) for s in baseline_sources], suites=[], qualifies=False, reasons=[],
               other_problems=[], totals_consistent=None)
    fs = parsed.get('failed_suites') or []
    if parsed.get('run_all_exit') != 1 or not fs:
        res['reasons'].append('no run_all summary with exit 1 and failed suite rows (run_all exit=%s): rule 2 not applicable' % parsed.get('run_all_exit'))
        return res
    # run_all prints these as section headers (line start) or as a table-row note; the exit-1 "meaning" line merely lists the words
    for label, pattern in (('expected-count mismatch section', r'^預期數不符（'), ('expected-count mismatch row note', r'預期數不符：'),
                           ('registry check failure', r'^登記檢查失敗（'), ('unregistered test files', r'^未登記／登記有誤的測試檔（')):
        if re.search(pattern, text, re.M):
            res['other_problems'].append(label)
    index = baseline_index(baseline_sources)
    rows = {r['suite']: r for r in parsed['rows']}
    for suite in fs:
        row = rows[suite]
        data = load_suite_json(saved_logdir, suite)
        ids = failure_ids(suite, data)
        env_problem = row['note'].startswith('環境')
        eligible = (not env_problem) and all(index.get(i) for i in ids)
        first_total = int(row['total']) if row['total'].isdigit() else None
        ent = dict(suite=suite, failed_ids=ids, eligible_by_baseline=eligible,
                   first_run=dict(failed=row['failed'], total=row['total'], note=row['note'][:200],
                                  tests=[dict(id=f.get('test'), kind=f.get('kind'), message=f.get('message')) for f in (data or {}).get('failures', [])]),
                   baseline={i: (dict(occurrences=len(index[i]), first=index[i][0]) if index.get(i) else None) for i in ids},
                   reruns=[], excused=False)
        for attempt in range(1, rerun_max + 1):
            rr = rerun_suite(jobtmp, repo, senv, base_run, suite, attempt, out, first_total)
            ent['reruns'].append(rr)
            if rr['passed']:
                break
        ent['rerun_passed'] = any(r['passed'] for r in ent['reruns'])
        ent['excused'] = eligible and ent['rerun_passed']
        if not eligible:
            ent['why_not_excused'] = ('environment problem row' if env_problem else
                                      'failed test(s) NOT failing in any main baseline receipt: %s' % [i for i in ids if not index.get(i)])
        elif not ent['rerun_passed']:
            ent['why_not_excused'] = 'failure reproduced in %d re-run(s)' % len(ent['reruns'])
        res['suites'].append(ent)
    t = parsed.get('totals') or {}
    counted = [int(rows[s]['failed']) for s in fs if rows[s]['failed'].isdigit()]
    res['totals_consistent'] = bool(t) and len(counted) == len(fs) and t.get('failed') == sum(counted)
    if not res['totals_consistent']:
        res['reasons'].append('failed counts of the failing rows do not add up to the run_all total (%s vs %s)' % (counted, t.get('failed')))
    if res['other_problems']:
        res['reasons'].append('run_all reported other problems besides failing suites: %s' % res['other_problems'])
    bad = [e['suite'] for e in res['suites'] if not e['excused']]
    if bad:
        res['reasons'].append('not excused: %s' % bad)
    res['qualifies'] = not res['reasons']
    return res


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--job', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--tmp', required=True)
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--watchdog-factor', type=float, default=3.0, help='hard watchdog = yml timeout-minutes x this (rule 1: 3)')
    ap.add_argument('--baseline-src', action='append', default=[], help='receipt dir of a MAIN baseline run (rule 2); repeatable')
    ap.add_argument('--rerun-max', type=int, default=2, help='max single-suite re-runs per failed suite (rule 2)')
    a = ap.parse_args()

    repo, out, jobtmp = pathlib.Path(a.repo), pathlib.Path(a.out), pathlib.Path(a.tmp)
    out.mkdir(parents=True, exist_ok=True)
    jobtmp.mkdir(parents=True, exist_ok=True)
    (jobtmp / '_steps').mkdir(exist_ok=True)
    wrap = jobtmp / '_steps' / 'ns_wrap.sh'
    wrap.write_text('\n'.join(['#!/bin/bash', 'mkdir -p "$1" /tmp/geometry-tests',
                               'mount --bind "$1" /tmp/geometry-tests || exit 97', 'shift', 'exec "$@"', '']), encoding='utf-8')
    shim = jobtmp / '_shim'
    shim.mkdir(exist_ok=True)
    if not (shim / 'python').exists():
        (shim / 'python').symlink_to('/usr/bin/python3')  # GitHub's ubuntu image ships python-is-python3; WSL Ubuntu does not
    logp = out / 'job.log'
    logs_saved = []

    def save_run_all_logs():
        """Copy the private run_all-logs to <out>/run_all-logs exactly once (before any re-run touches them)."""
        if logs_saved:
            return
        logs_saved.append(True)
        src = jobtmp / 'geometry-tests' / 'run_all-logs'  # the private /tmp/geometry-tests of this job
        if src.is_dir():
            import shutil
            shutil.copytree(src, out / 'run_all-logs', dirs_exist_ok=True)

    result = dict(job=a.job, sha=None, started=now(), steps=[], notes=[], status='error', exit_code=EXIT_INFRA)
    t0 = time.time()

    def log(msg):
        with open(logp, 'ab') as f:
            f.write((msg + '\n').encode('utf-8'))

    try:
        result['sha'] = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
        key, job, matrix = load_spec(repo, a.job)
        result['workflow_job_key'] = key
        result['matrix'] = matrix
        timeout_min = int(subst(job.get('timeout-minutes', 360), matrix))
        result['ci_timeout_minutes'] = timeout_min
        raw_env = {k: subst(v, matrix) for k, v in (job.get('env') or {}).items()}
        m = re.search(r':(\d+)/', raw_env.get('GEOMETRY_TEST_URL', ''))
        old_port = m.group(1) if m else None
        env = dict(PATH=str(shim) + ':' + SAFE_PATH, HOME=os.environ.get('HOME', '/root'), LANG='C.UTF-8', LC_ALL='C.UTF-8',
                   TMPDIR=str(jobtmp), CI='true', GITHUB_ACTIONS='true', RUNNER_OS='Linux', GITHUB_SHA=result['sha'],
                   GITHUB_WORKSPACE=str(repo), WSL_CI_JOB_TAG=a.tag, TERM='dumb')
        for k, v in raw_env.items():
            env[k] = rewrite(v, str(jobtmp), old_port, a.port)
        result['env'] = {k: env[k] for k in raw_env}
        result['notes'].append("PATH has a per-job shim dir with python -> /usr/bin/python3 (GitHub's ubuntu image has python-is-python3, this WSL distro does not; tests spawn plain 'python')")
        result['port_rewrite'] = [old_port, a.port] if old_port else None
        log('##[wsl-ci] job=%s key=%s sha=%s repo=%s' % (a.job, key, result['sha'], repo))
        log('##[wsl-ci] ci timeout %d min (hard watchdog %.0f min); jobtmp=%s port=%s->%s' % (timeout_min, timeout_min * a.watchdog_factor, jobtmp, old_port, a.port))
        deadline = t0 + timeout_min * 60 * a.watchdog_factor
        failed = False
        fail_ctx = None
        for idx, step in enumerate(job['steps']):
            name = step.get('name') or step.get('uses') or ('step%d' % idx)
            rec = dict(index=idx, name=name)
            result['steps'].append(rec)
            if 'uses' in step:
                if step['uses'].startswith('actions/checkout'):
                    rec.update(outcome='replaced', note='clean local clone at the SHA under test')
                elif step['uses'].startswith('actions/upload-artifact'):
                    rec.update(outcome='skipped', note='artifact upload not applicable outside GitHub')
                else:
                    raise Blocked('unknown action %s' % step['uses'])
                log('##[wsl-ci] step %d %s -> %s (%s)' % (idx, name, rec['outcome'], rec['note']))
                continue
            if failed:
                rec.update(outcome='not-run', note='earlier step failed')
                continue
            cond = step.get('if')
            if cond is not None and str(cond).strip() not in ('success()',):
                raise Blocked('run step %r has unhandled condition %r' % (name, cond))
            run = rewrite(subst(step['run'], matrix), str(jobtmp), old_port, a.port)
            if re.search(r'\bsudo\b|\bapt(-get)?\b', run):
                try:
                    report = apt_step(run)
                except Blocked:
                    rec.update(outcome='blocked')
                    raise
                rec.update(outcome='skipped-already-installed', packages=report)
                log('##[wsl-ci] step %d %s -> skipped, packages already installed: %s' % (idx, name, json.dumps(report, ensure_ascii=False)))
                continue
            script = jobtmp / '_steps' / ('step%d.sh' % idx)
            script.write_text(run if run.endswith('\n') else run + '\n', encoding='utf-8', newline='\n')
            inner = ['bash', '--noprofile', '--norc', '-eo', 'pipefail', str(script)] if step.get('shell') == 'bash' else ['bash', '-e', str(script)]
            # tests/binaries.py hardcodes /tmp/geometry-tests (binaries, run_all.lock, logs) off Windows.  Other sessions share this WSL
            # distro, so each job gets a PRIVATE mount namespace in which that path is a per-job directory.  Nothing outside the
            # namespace (the real /tmp/geometry-tests, other sessions' locks and binaries) is touched.
            argv = ['unshare', '-m', '--propagation', 'private', 'bash', str(jobtmp / '_steps' / 'ns_wrap.sh'), str(jobtmp / 'geometry-tests')] + inner
            senv = dict(env)
            for k, v in (step.get('env') or {}).items():
                senv[k] = rewrite(subst(v, matrix), str(jobtmp), old_port, a.port)
            log('##[group]Run %s' % name)
            log(run.rstrip())
            log('##[endgroup]')
            s0 = time.time()
            with open(logp, 'ab') as lf:
                p = subprocess.Popen(argv, cwd=str(repo), env=senv, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
                try:
                    code = p.wait(timeout=max(1, deadline - time.time()))
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(p.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    p.wait()
                    code = EXIT_WATCHDOG
                    result['notes'].append('watchdog killed step %d after %.1f min (CI limit %d min)' % (idx, (time.time() - s0) / 60, timeout_min))
            try:
                os.killpg(p.pid, signal.SIGKILL)  # stragglers of this step's process group (ours by construction)
            except (ProcessLookupError, PermissionError):
                pass
            rec.update(outcome='success' if code == 0 else 'failure', exit_code=code, seconds=round(time.time() - s0, 1), argv=inner[:-1], private_tmp_namespace=True)
            log('##[wsl-ci] step %d %s -> exit %d in %.1fs' % (idx, name, code, time.time() - s0))
            if code != 0:
                failed = True
                result['exit_code'] = code
                fail_ctx = (run, senv)
        if not failed:
            result['exit_code'] = 0
        result['seconds_first_run'] = round(time.time() - t0, 1)
        if failed and a.job == 'native' and fail_ctx and result['exit_code'] == 1:
            # rule 2: the originals must be saved BEFORE any re-run overwrites the per-suite logs of the private /tmp/geometry-tests
            save_run_all_logs()
            text_now = logp.read_text(encoding='utf-8', errors='replace')
            log('##[wsl-ci] rule 2: native failed with exit 1; re-running each failing suite alone (max %d attempts)' % a.rerun_max)
            result['flaky'] = flaky_analysis(jobtmp, repo, fail_ctx[1], fail_ctx[0], out, out / 'run_all-logs', text_now,
                                             [pathlib.Path(x) for x in a.baseline_src], a.rerun_max)
            log('##[wsl-ci] rule 2 result: qualifies=%s reasons=%s' % (result['flaky']['qualifies'], result['flaky']['reasons']))
        result['status'] = 'completed'
    except Blocked as e:
        result.update(status='blocked', exit_code=EXIT_BLOCKED)
        result['notes'].append('BLOCKED: %s' % e)
        log('##[wsl-ci] BLOCKED: %s' % e)
    except Exception as e:  # infrastructure error of this runner, never a test verdict
        result.update(status='error', exit_code=EXIT_INFRA)
        result['notes'].append('runner error: %r' % (e,))
        log('##[wsl-ci] runner error: %r' % (e,))
    finally:
        leftovers = kill_tagged(a.tag)
        result['leftover_processes_killed'] = leftovers
        if leftovers:
            log('##[wsl-ci] killed leftover processes carrying tag %s: %s' % (a.tag, leftovers))
        result['seconds'] = round(time.time() - t0, 1)
        result['ended'] = now()
        if a.job == 'native':
            save_run_all_logs()
        text = logp.read_text(encoding='utf-8', errors='replace') if logp.exists() else ''
        if a.job == 'native':
            result['parsed'] = parse_native(text)
        else:
            result['parsed'] = parse_browser(text)
        main_seconds = result.get('seconds_first_run', result['seconds'])  # re-runs do not count against the CI limit
        result['over_ci_timeout'] = main_seconds > result.get('ci_timeout_minutes', 10 ** 6) * 60
        result['ci_limit_ratio'] = round(main_seconds / (result['ci_timeout_minutes'] * 60), 2) if result.get('ci_timeout_minutes') else None
        result['watchdog_factor'] = a.watchdog_factor
        (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
    return result['exit_code']


if __name__ == '__main__':
    sys.exit(main())
