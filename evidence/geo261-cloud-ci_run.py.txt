#!/usr/bin/env python3
"""Orchestrator: clean clone(s) of <sha> in ext4, run the SHA's own CI jobs (<=2 at a time), write receipt.json + README.md.

    wsl_ci.sh <sha> <job-filter>      job-filter: all | native | assembly,documents,... (names from the SHA's yml)

Environment:
    WSL_CI_REPO       source repository to clone from (default /mnt/d/geometry-axiom, read-only use)
    WSL_CI_OUT        output directory (default <this dir>/<sha8>[-label])
    WSL_CI_LABEL      suffix for the default output dir (used by the teeth runs)
    WSL_CI_PARALLEL   concurrent jobs (default 2, same as the workflow's max-parallel)
    WSL_CI_PORT_BASE  first service port handed to jobs (default 18840)
    WSL_CI_NOTE       free text copied into the README (e.g. what was mutated)
"""
from __future__ import annotations

import ast
import concurrent.futures
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import threading
import time

import yaml

HERE = pathlib.Path(__file__).resolve().parent
HOME = pathlib.Path(os.environ.get('HOME', '/root'))
GA = HOME / 'ga-ci'
SAFE_PATH = '/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
ENV = dict(os.environ, PATH=SAFE_PATH, LANG='C.UTF-8', LC_ALL='C.UTF-8', GIT_TERMINAL_PROMPT='0')
LONGEST_FIRST = ['canvas', 'native']
WATCHDOG_FACTOR = 3.0  # rule 1
RERUN_MAX = 2  # rule 2


def run(cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=True, text=True, errors='replace')
    if check and r.returncode != 0:
        raise SystemExit('command failed (%d): %s\n%s' % (r.returncode, ' '.join(cmd), r.stderr[-800:]))
    return r


def git_show(mirror, sha, path):
    r = run(['git', '-C', str(mirror), 'show', '%s:%s' % (sha, path)], check=False)
    return r.stdout if r.returncode == 0 else None


def tool_versions():
    def first(cmd):
        r = subprocess.run(cmd, env=ENV, capture_output=True, text=True)
        return (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else None
    osr = dict(l.split('=', 1) for l in pathlib.Path('/etc/os-release').read_text().splitlines() if '=' in l)
    return dict(chrome=first(['google-chrome', '--version']), node=first(['node', '--version']), npm=first(['npm', '--version']),
                python=first(['python3', '--version']), gcc=first(['gcc', '--version']), git=first(['git', '--version']),
                os=osr.get('PRETTY_NAME', '').strip('"'), kernel=first(['uname', '-r']), cpus=os.cpu_count(),
                mem_mb=int(re.search(r'MemTotal:\s+(\d+)', pathlib.Path('/proc/meminfo').read_text())[1]) // 1024,
                cjk_fonts=first(['bash', '-c', 'fc-list | grep -ci "noto.*cjk"']))


SYS_NOISY = re.compile(r'cloud-init|landscape-sysinfo|landscape-client|unattended-upgrade(?!-shutdown)|apt-get|dpkg|apt\.systemd')
FOREIGN = re.compile(r'tests/run_all\.py|cdp_test\.js|space_model_test\.js|documents_browser_test\.js|google-chrome|/opt/google/chrome/chrome|cc1 |_unittest_runner\.py')


def scan_processes():
    """-> (busy_sys, busy_foreign): boot housekeeping, and compile/test processes that do NOT carry one of our WSL_CI_JOB_TAGs."""
    busy_sys, busy_foreign = [], []

    def ours(pid):
        """Chrome's gpu/renderer children rewrite their own environ (process-title trick), so the tag may be gone from /proc/<pid>/environ:
        a process also counts as ours when an ancestor carries the tag, or when it runs under our /tmp/ga-ci job dirs."""
        seen = 0
        while pid > 1 and seen < 64:
            seen += 1
            try:
                if b'WSL_CI_JOB_TAG=' in pathlib.Path('/proc/%d/environ' % pid).read_bytes():
                    return True
                stat = pathlib.Path('/proc/%d/stat' % pid).read_text()
                pid = int(stat.rsplit(') ', 1)[1].split()[1])
            except (OSError, ValueError, IndexError):
                return False
        return False

    for pid in os.listdir('/proc'):
        if not pid.isdigit() or int(pid) == os.getpid():
            continue
        try:
            cmd = pathlib.Path('/proc/%s/cmdline' % pid).read_bytes().replace(b'\0', b' ').decode('utf-8', 'replace')
            if SYS_NOISY.search(cmd) and 'unattended-upgrade-shutdown' not in cmd:  # the shutdown helper is a permanent daemon
                busy_sys.append(cmd[:80])
            elif FOREIGN.search(cmd):
                if not ours(int(pid)) and '/tmp/ga-ci/' not in cmd:
                    busy_foreign.append(cmd[:100])
        except OSError:
            pass
    return busy_sys, busy_foreign


def quiesce(max_s=900):
    """Rule 3 (exclusive): wait (bounded) until this WSL VM is quiet: no boot-time housekeeping, and no compile/test activity from OTHER
    sessions that share the distro (their load makes timing-sensitive tests flaky).  Never touches their processes.  Recorded."""
    t0 = time.time()
    seen = set()
    while True:
        busy_sys, busy_foreign = scan_processes()
        seen.update(busy_foreign)
        if (not busy_sys and not busy_foreign) or time.time() - t0 > max_s:
            break
        time.sleep(5)
    uptime = float(pathlib.Path('/proc/uptime').read_text().split()[0])
    return dict(waited_seconds=round(time.time() - t0, 1), exclusive_at_start=not busy_sys and not busy_foreign,
                still_busy_system=busy_sys, still_busy_foreign=busy_foreign,
                foreign_activity_seen=sorted(seen)[:10], loadavg=pathlib.Path('/proc/loadavg').read_text().split()[:3], vm_uptime_seconds=round(uptime))


class ForeignSampler(threading.Thread):
    """Rule 3 (exclusive), during the run: sample every 15 s for compile/test processes of other sessions; the result goes into the receipt."""

    def __init__(self):
        super().__init__(daemon=True)
        self.stop_flag = threading.Event()
        self.seen, self.samples, self.load_max = {}, 0, 0.0

    def run(self):
        while not self.stop_flag.wait(15):
            self.samples += 1
            try:
                self.load_max = max(self.load_max, float(pathlib.Path('/proc/loadavg').read_text().split()[0]))
                for cmd in scan_processes()[1]:
                    self.seen[cmd] = self.seen.get(cmd, 0) + 1
            except OSError:
                pass

    def report(self):
        self.stop_flag.set()
        return dict(samples=self.samples, foreign_processes_seen_during_run=dict(sorted(self.seen.items())[:10]), exclusive_during_run=not self.seen,
                    max_loadavg_1min_sampled=round(self.load_max, 2))


def warm_up():
    """Prime the page cache (a cold WSL VM made the first Chrome launch exceed the test's 30 s endpoint wait and the first gcc/unittest
    run time out).  Pure environment preparation: it runs no repository code.  Timings are recorded in the receipt."""
    import shutil
    d = pathlib.Path('/tmp/ga-ci/_warm')
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    out = {}

    def timed(name, cmd, **kw):
        t = time.time()
        try:
            rc = subprocess.run(cmd, env=ENV, capture_output=True, timeout=240, **kw).returncode
        except Exception as e:  # noqa: BLE001 - recorded, never fatal
            rc = repr(e)
        out[name] = dict(rc=rc, seconds=round(time.time() - t, 1))
    for i in (1, 2):
        timed('chrome_%d' % i, ['google-chrome', '--headless=new', '--no-sandbox', '--disable-gpu', '--user-data-dir=%s/profile%d' % (d, i),
                                '--dump-dom', 'about:blank'])
    timed('gcc', ['gcc', '-x', 'c', '-', '-o', str(d / 'a.out')], input=b'int main(void){return 0;}\n')
    timed('node', ['node', '-e', '1'])
    shutil.rmtree(d, ignore_errors=True)
    return out


def job_names(yml_text):
    wf = yaml.safe_load(yml_text)
    names = []
    for key, job in wf['jobs'].items():
        inc = ((job.get('strategy') or {}).get('matrix') or {}).get('include')
        if inc:
            names += [e['suite'] for e in inc]
        else:
            names.append(key)
    return names


def allowed_skips(run_all_text):
    if not run_all_text:
        return None
    tree = ast.parse(run_all_text)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ALLOWED_SKIPS' for t in node.targets):
            return ast.literal_eval(node.value)
    return None


def compare_expected(parsed, expected_text):
    if expected_text is None:
        return dict(available=False)
    exp = json.loads(expected_text)['suites']
    rows = {r['suite']: r for r in parsed.get('rows', [])}
    mism, missing = [], []
    for name, e in exp.items():
        r = rows.get(name)
        if r is None:
            missing.append(name)
        elif e.get('mode') == 'count':
            if r['total'] != str(e['count']):
                mism.append('%s: expected %s, got %s' % (name, e['count'], r['total']))
        elif not (r['passed'] == 'ok' or (r['failed'] != 'FAIL' and 'exit 0' in r['note'])):
            mism.append('%s: exit-code-only suite did not report ok (%s / %s)' % (name, r['passed'], r['note'][:60]))
    extra = sorted(set(rows) - set(exp))
    return dict(available=True, expected_suites=len(exp), expected_items=sum(e.get('count', 0) for e in exp.values() if e.get('mode') == 'count'),
                ran_suites=len(rows), mismatches=mism, missing_in_log=missing, extra_in_log=extra,
                equal=not mism and not missing and not extra)


def classify_native_skips(parsed, allowed):
    out = []
    for r in parsed.get('rows', []):
        if r['skipped'] in ('0', '-'):
            continue
        entries = [e for e in (allowed or []) if e.get('suite') == r['suite']]
        ok = bool(entries) and '在具名允許清單' in r['note'] and any('posix' in e.get('platforms', ()) for e in entries)
        out.append(dict(suite=r['suite'], skipped=r['skipped'], note=r['note'],
                        allowed=ok, allowed_entries=[e.get('test') for e in entries] if ok else []))
    return out


def flaky_summary(fl):
    """Short human lines for the suites excused by rule 2."""
    out = []
    for e in fl.get('suites', []):
        if e.get('excused'):
            tests = [t['id'] for t in e['first_run']['tests']] or e['failed_ids']
            out.append('%s: %s | first run FAILED | re-run(s): %s | failed in main baseline: %s' % (
                e['suite'], '; '.join(tests),
                ', '.join('#%d %s' % (r['attempt'], 'PASS' if r['passed'] else 'FAIL') for r in e['reruns']),
                '; '.join('%s (%s)' % (i, b['first']['receipt']) for i, b in e['baseline'].items() if b)))
    return out


def judge(name, res, extra):
    """-> (verdict, reasons).  verdict in green / red / undetermined.  Rule 2 (flaky-rerun-pass) can turn a native exit 1 into green."""
    reasons = []
    p = res.get('parsed') or {}
    if res.get('status') in ('blocked', 'error') or res.get('status') is None:
        return 'undetermined', ['runner status %s: %s' % (res.get('status'), '; '.join(res.get('notes', [])))]
    fl = res.get('flaky') or {}
    excused = name == 'native' and res['exit_code'] == 1 and bool(fl.get('qualifies'))
    if res['exit_code'] != 0 and not excused:
        if res['exit_code'] == 124:
            reasons.append('exit 124: hard watchdog (CI limit x%s) hit, job aborted' % res.get('watchdog_factor'))
        else:
            reasons.append('exit code %s' % res['exit_code'])
        if fl:
            reasons.append('rule 2 (flaky re-run) did not excuse: %s' % '; '.join(fl.get('reasons') or ['see flaky block']))
        return 'red', reasons
    if name == 'native':
        t = p.get('totals')
        want_exit = 1 if excused else 0
        if not t or p.get('run_all_exit') != want_exit:
            return 'undetermined', ['exit %s but run_all summary missing / not exit %s in log' % (res['exit_code'], want_exit)]
        if excused:
            if not fl.get('totals_consistent') or t['passed'] + t['skipped'] + t['failed'] != t['total']:
                return 'undetermined', ['summary inconsistent for a rule-2 excused run: %s' % t]
        elif t['failed'] or t['passed'] + t['skipped'] != t['total']:
            return 'undetermined', ['summary inconsistent: %s' % t]
        exp = extra.get('expected_comparison', {})
        if exp.get('available') and not exp.get('equal'):
            return 'red', ['suite/item counts differ from tests/run_all.expected.json: %s' % exp]
        bad = [s for s in extra.get('skips', []) if not s['allowed']]
        if bad:
            return 'red', ['skips outside ALLOWED_SKIPS: %s' % bad]
        if excused:
            reasons = ['flaky-rerun-pass: ' + x for x in flaky_summary(fl)]
        return 'green', reasons
    if p.get('kind') is None:
        return 'undetermined', ['exit 0 but no CDP_RESULT/SPACE_RESULT/DOCUMENTS_RESULT line in log']
    if p.get('failed') not in (0,) or not p.get('passed'):
        return 'undetermined' if p.get('failed') is None else 'red', ['result line says passed=%s failed=%s' % (p.get('passed'), p.get('failed'))]
    if p.get('completed') is not True:
        return 'undetermined', ['result line says completed=%s' % p.get('completed')]
    return 'green', reasons


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    sha_in, filt = sys.argv[1], sys.argv[2]
    repo = pathlib.Path(os.environ.get('WSL_CI_REPO', '/mnt/d/geometry-axiom'))
    parallel = int(os.environ.get('WSL_CI_PARALLEL', '2'))
    port_base = int(os.environ.get('WSL_CI_PORT_BASE', '18840'))
    r = run(['git', '-C', str(repo), 'rev-parse', '--verify', '--quiet', sha_in + '^{commit}'], check=False)
    if r.returncode != 0:
        print('SHA %s not found in %s (fetch on the Windows side first: git -C D:/geometry-axiom fetch origin)' % (sha_in, repo))
        return 66
    sha = r.stdout.strip()
    label = os.environ.get('WSL_CI_LABEL', '')
    out = pathlib.Path(os.environ.get('WSL_CI_OUT') or (HERE / (sha[:8] + ('-' + label if label else ''))))
    out.mkdir(parents=True, exist_ok=True)

    mirror = GA / 'mirrors' / (hashlib.sha1(str(repo).encode()).hexdigest()[:10] + '.git')
    if not mirror.exists():
        mirror.parent.mkdir(parents=True, exist_ok=True)
        run(['git', 'clone', '-q', '--mirror', str(repo), str(mirror)])
    else:
        run(['git', '-C', str(mirror), 'fetch', '-q', 'origin'])
    if run(['git', '-C', str(mirror), 'cat-file', '-e', sha + '^{commit}'], check=False).returncode != 0:
        print('SHA %s missing in mirror after fetch' % sha)
        return 66

    yml_text = git_show(mirror, sha, '.github/workflows/integration-tests.yml')
    if yml_text is None:
        print('no .github/workflows/integration-tests.yml at %s' % sha)
        return 66
    all_jobs = job_names(yml_text)
    wanted = all_jobs if filt == 'all' else [j for j in filt.split(',') if j]
    unknown = [j for j in wanted if j not in all_jobs]
    if unknown:
        print('unknown job(s) %s; the SHA\'s workflow defines %s' % (unknown, all_jobs))
        return 64
    order = [j for j in LONGEST_FIRST if j in wanted] + [j for j in wanted if j not in LONGEST_FIRST]
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    runid = '%s-%s' % (sha[:8], stamp)
    runroot = GA / 'runs' / runid
    print('[wsl-ci] sha=%s jobs=%s parallel=%d out=%s' % (sha, order, parallel, out), flush=True)
    baseline_src, baseline_notes = [], []
    bfile = HERE / 'baseline_sources.txt'
    for line in (bfile.read_text(encoding='utf-8').splitlines() if bfile.exists() else []):
        if not line.strip() or line.startswith('#'):
            continue
        bdir, bsha = (line.split() + [''])[:2]
        bpath = HERE / bdir
        try:
            bhead = json.loads((bpath / 'receipt.json').read_text(encoding='utf-8')).get('head_sha', '')
        except (OSError, ValueError):
            bhead = None
        if bpath.resolve() == out.resolve():
            baseline_notes.append('%s skipped: it is the output dir of this very run (a run never excuses itself)' % bdir)
        elif bhead is None:
            baseline_notes.append('%s skipped: no receipt.json (yet)' % bdir)
        elif not bhead.startswith(bsha):
            baseline_notes.append('%s skipped: head_sha %s is not the expected main sha %s' % (bdir, bhead, bsha))
        else:
            baseline_src.append(str(bpath))
    print('[wsl-ci] rule 2 baseline sources: %s %s' % (baseline_src, baseline_notes), flush=True)
    quiet = quiesce()
    print('[wsl-ci] environment quiesce: %s' % quiet, flush=True)
    warm = warm_up()
    print('[wsl-ci] warm-up: %s' % warm, flush=True)
    sampler = ForeignSampler()
    sampler.start()

    def do_job(args):
        i, name = args
        jdir = out / name
        if jdir.exists():
            jdir.rename(out / ('%s.prev-%s' % (name, stamp)))
        work = runroot / name / 'repo'
        work.parent.mkdir(parents=True, exist_ok=True)
        run(['git', '-c', 'core.autocrlf=false', 'clone', '-q', '--no-checkout', str(mirror), str(work)])
        run(['git', '-c', 'core.autocrlf=false', '-c', 'advice.detachedHead=false', 'checkout', '-q', '--detach', sha], cwd=work)
        head = run(['git', 'rev-parse', 'HEAD'], cwd=work).stdout.strip()
        assert head == sha, (head, sha)
        status = run(['git', 'status', '--porcelain'], cwd=work).stdout.strip()
        assert not status, 'work clone not clean: ' + status[:200]
        port = port_base + all_jobs.index(name)
        tmp = pathlib.Path('/tmp/ga-ci') / runid / name
        t = time.time()
        print('[wsl-ci] start %-9s port=%d' % (name, port), flush=True)
        rc = subprocess.run([sys.executable, '-u', str(HERE / 'ci_job.py'), '--repo', str(work), '--job', name, '--out', str(jdir),
                             '--tmp', str(tmp), '--port', str(port), '--tag', '%s-%s' % (runid, name),
                             '--watchdog-factor', str(WATCHDOG_FACTOR), '--rerun-max', str(RERUN_MAX)]
                            + [x for b in baseline_src for x in ('--baseline-src', b)], env=ENV).returncode
        print('[wsl-ci] done  %-9s exit=%d %.0fs' % (name, rc, time.time() - t), flush=True)
        return name, rc

    t_all = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as ex:
        list(ex.map(do_job, list(enumerate(order))))
    exclusivity = dict(at_start=quiet, during_run=sampler.report())

    # ---- receipt (aggregates every job dir currently present, so single-job reruns merge in)
    expected_text = git_show(mirror, sha, 'tests/run_all.expected.json')
    allowed = allowed_skips(git_show(mirror, sha, 'tests/run_all.py'))
    jobs, verdicts = {}, {}
    for name in all_jobs:
        rp = out / name / 'result.json'
        if not rp.exists():
            continue
        res = json.loads(rp.read_text(encoding='utf-8'))
        if res.get('sha') != sha:
            continue
        p = res.get('parsed') or {}
        extra = {}
        if name == 'native':
            extra['expected_comparison'] = compare_expected(p, expected_text)
            extra['skips'] = classify_native_skips(p, allowed)
            extra['allowed_skips_in_sha'] = [dict(suite=e['suite'], test=e['test'], platforms=list(e['platforms'])) for e in (allowed or [])]
        v, why = judge(name, res, extra)
        verdicts[name] = v
        counts = (dict(total=p['totals']['total'], passed=p['totals']['passed'], failed=p['totals']['failed'], skipped=p['totals']['skipped'])
                  if name == 'native' and p.get('totals') else
                  dict(total=None if p.get('passed') is None else p['passed'] + (p.get('failed') or 0), passed=p.get('passed'), failed=p.get('failed'), skipped=None))
        entry = dict(verdict=v, why=why, exit_code=res['exit_code'], status=res['status'], seconds=res['seconds'], counts=counts,
                     ci_timeout_minutes=res.get('ci_timeout_minutes'), over_ci_timeout=res.get('over_ci_timeout'),
                     seconds_first_run=res.get('seconds_first_run'), ci_limit_ratio=res.get('ci_limit_ratio'), watchdog_factor=res.get('watchdog_factor'),
                     steps=[dict(name=s['name'], outcome=s.get('outcome'), exit_code=s.get('exit_code'), seconds=s.get('seconds'), note=s.get('note')) for s in res['steps']],
                     notes=res.get('notes', []), leftover_processes_killed=res.get('leftover_processes_killed', []),
                     log=str((out / name / 'job.log')), result_json=str(rp))
        if name == 'native':
            entry['run_all_exit'] = p.get('run_all_exit')
            entry['run_all_meaning'] = p.get('run_all_meaning')
            entry['failed_suites'] = p.get('failed_suites')
            entry['failure_details'] = p.get('failure_details')
            entry['unittest_fail_lines'] = p.get('unittest_fail_lines')
            entry.update(extra)
            if res.get('flaky'):
                entry['flaky'] = res['flaky']
                if v == 'green' and res['exit_code'] == 1:
                    entry['flaky_rerun_pass'] = [e for e in res['flaky']['suites'] if e.get('excused')]
            entry['counts_note'] = 'from run_all.py table row "合計"; browser gates are separate jobs'
        else:
            entry['kind'] = p.get('kind')
            entry['completed'] = p.get('completed')
            entry['scope'] = p.get('scope')
            entry['skipped_groups'] = p.get('skipped_groups')
            entry['golden'] = p.get('golden')
            entry['failed_assertion_lines'] = p.get('failed_assertion_lines')
            for k in ('uncaught_browser_exceptions', 'exceptions', 'console_errors', 'fatal', 'sections_failed'):
                if p.get(k) not in (None, 0, [], {}):
                    entry[k] = p[k]
            entry['counts_note'] = 'assertion counts from the test\'s own *_RESULT line; skipped is not counted by this harness (see skipped_groups)'
            if entry['counts']['skipped'] is None:
                entry['counts']['skipped'] = None
        jobs[name] = entry
    present = [n for n in all_jobs if n in jobs]
    reds = [n for n in present if verdicts[n] == 'red']
    unds = [n for n in present if verdicts[n] == 'undetermined']
    flaky_pass = [(n, e['suite']) for n in present for e in (jobs[n].get('flaky_rerun_pass') or [])]
    if len(present) == len(all_jobs):
        verdict = ('%d/%d green' % (len(all_jobs), len(all_jobs)) + (' (incl. flaky-rerun-pass: %s)' % ', '.join('%s[%s]' % x for x in flaky_pass) if flaky_pass else ' (no flaky-rerun-pass)')
                   if not reds and not unds else ('red: ' + ', '.join(reds) if reds else 'undetermined: ' + ', '.join(unds)))
        if reds and unds:
            verdict += ' ; undetermined: ' + ', '.join(unds)
    else:
        verdict = 'PARTIAL (%d of %d jobs run: %s): green=%s red=%s undetermined=%s%s' % (
            len(present), len(all_jobs), ', '.join(present), [n for n in present if verdicts[n] == 'green'], reds, unds,
            ' flaky-rerun-pass=%s' % ', '.join('%s[%s]' % x for x in flaky_pass) if flaky_pass else '')
    receipt = dict(schema='wsl-ci-receipt/1', head_sha=sha, label=label or None, generated_at=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
                   source_repo=str(repo), runner_dir=str(HERE), runroot=str(runroot),
                   workflow_sha256=hashlib.sha256(yml_text.encode()).hexdigest(), workflow_jobs=all_jobs,
                   max_parallel=parallel, tools=tool_versions(), environment_quiesce=quiet, warm_up=warm, exclusivity=exclusivity,
                   rules=dict(timeout='hard watchdog = yml timeout-minutes x %s; exceeding the CI limit is flagged, not red; hitting the watchdog (exit 124) is red' % WATCHDOG_FACTOR,
                              flaky='native only: failing suites re-run alone in the same clone, max %d attempts; excused only if a re-run passes AND every failed test id also failed in a MAIN baseline receipt' % RERUN_MAX,
                              exclusive='wait (bounded) for compile/test processes of other sessions before starting; sample every 15 s during the run; both recorded'),
                   rule2_baseline_sources=baseline_src, rule2_baseline_notes=baseline_notes, verdict=verdict, jobs=jobs,
                   note=os.environ.get('WSL_CI_NOTE') or None,
                   wall_seconds_this_invocation=round(time.time() - t_all, 1))
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=1), encoding='utf-8')
    write_readme(out, receipt, sys.argv)
    print('[wsl-ci] VERDICT: ' + verdict)
    print('[wsl-ci] receipt: ' + str(out / 'receipt.json'))
    if reds or unds:
        return 1
    return 0 if len(present) == len(all_jobs) else 3


def write_readme(out, rc, argv):
    L = []
    L.append('# WSL CI-equivalent receipt for %s' % rc['head_sha'])
    L.append('')
    L.append('Generated %s.  **Verdict: %s**' % (rc['generated_at'], rc['verdict']))
    if rc.get('note'):
        L += ['', 'Note: ' + rc['note']]
    L += ['', '## How it was run', '',
          'Command (from Windows):', '',
          '    wsl -d Ubuntu-24.04 -- bash %s/wsl_ci.sh %s %s' % (rc['runner_dir'].replace('\\', '/'), argv[1], argv[2]), '',
          'Environment overrides used: WSL_CI_REPO=%s WSL_CI_LABEL=%s' % (os.environ.get('WSL_CI_REPO', '(default)'), os.environ.get('WSL_CI_LABEL', '(none)')), '',
          'Method: the jobs, env, matrix and `run:` scripts are read from the SHA\'s own `.github/workflows/integration-tests.yml` (sha256 %s)' % rc['workflow_sha256'][:16],
          'and executed verbatim in an ext4 clean clone (one clone per job, `core.autocrlf=false`, detached at the SHA).  Deviations from GitHub:', '',
          '- actions/checkout replaced by the local clone; actions/upload-artifact skipped (nothing to upload to).',
          '- `sudo apt-get` steps skipped only when every package is already installed (recorded per job); otherwise the job is BLOCKED, never run with sudo.',
          '- `/tmp/` paths and the service port are rewritten per job and TMPDIR is set per job so that two jobs run side by side; CDP ports are the yml\'s own.',
          '- CI=true, GITHUB_ACTIONS=true, RUNNER_OS=Linux set to mirror the runner; PATH limited to Linux dirs with /opt/node/bin first.',
          '- A per-job PATH shim `python -> /usr/bin/python3` (GitHub\'s ubuntu image ships python-is-python3; this WSL distro does not and 11 node tests spawn plain `python`).',
          '- Every step runs in a private mount namespace (`unshare -m`) where `/tmp/geometry-tests` (hardcoded by tests/binaries.py) is a per-job dir, because other sessions share this WSL distro and hold `/tmp/geometry-tests/run_all.lock`.',
          '- Before jobs start: wait (bounded) for boot housekeeping / foreign sessions\' test load to end, and prime Chrome/gcc/node page caches (recorded in receipt.json `environment_quiesce`, `warm_up`).',
          '- Up to %d jobs run concurrently on one 12-core WSL VM (the workflow\'s own max-parallel is 2, but on separate runners).' % rc['max_parallel'],
          '- Tool versions differ from GitHub\'s ubuntu-latest image: see receipt.json `tools`.', '',
          '## Referee rules (decided by the main loop; applied mechanically by this runner)', '',
          '1. **Timeout**: each job\'s hard watchdog = the SHA\'s yml `timeout-minutes` x %s (WSL is slower than a CI runner; the CI limit is an infrastructure limit, not a correctness referee).' % WATCHDOG_FACTOR,
          '   Elapsed time is recorded as measured; exceeding the CI limit is flagged "over CI limit (WSL)" and is NOT red by itself.  Hitting the watchdog (exit 124) is red.',
          '2. **Flaky tests** (native job only): when `run_all.py` ends with failing suites, each failing suite is re-run ALONE in the same clone (`run_all.py --only <suite>`, up to %d attempts).' % RERUN_MAX,
          '   Verdict green ("flaky-rerun-pass") only if a re-run passes AND every failed test id of that suite also failed in a MAIN baseline receipt (`rule2_baseline_sources` in receipt.json); everything else stays red.',
          '   Browser jobs have no per-test identity and are never excused (any failure = red).  The first run\'s numbers are never rewritten: the receipt keeps exit code and counts of the first run and lists the re-runs separately.',
          '3. **Exclusive**: before starting, wait (bounded) until no other session\'s compile/test processes are running in this WSL VM; sample for them every 15 s during the run.  Both are recorded in `exclusivity`.',
          '']
    ex = rc.get('exclusivity') or {}
    st, du = ex.get('at_start') or {}, ex.get('during_run') or {}
    L += ['## Rule 1/2/3 evidence', '',
          '- baseline sources used by rule 2: %s %s' % (rc.get('rule2_baseline_sources'), rc.get('rule2_baseline_notes') or ''),
          '- exclusivity at start: %s (waited %ss; still busy foreign=%s system=%s; seen while waiting=%s)' % (
              'YES' if st.get('exclusive_at_start') else 'NO', st.get('waited_seconds'), st.get('still_busy_foreign'), st.get('still_busy_system'), st.get('foreign_activity_seen')),
          '- exclusivity during the run: %s (%s samples; foreign processes seen=%s; max sampled 1-min loadavg=%s)' % (
              'YES' if du.get('exclusive_during_run') else 'NO', du.get('samples'), du.get('foreign_processes_seen_during_run'), du.get('max_loadavg_1min_sampled')),
          '', '## Per-job results (exit code and counts are those of the FIRST full run of each job)', '',
          '| job | verdict | exit | passed | failed | skipped | seconds | CI limit (min) / watchdog (min) | vs CI limit |', '|---|---|---|---|---|---|---|---|---|']
    for n, j in rc['jobs'].items():
        c = j['counts']
        wd = (j['ci_timeout_minutes'] or 0) * (j.get('watchdog_factor') or 0)
        L.append('| %s | %s%s | %s | %s | %s | %s | %s | %s / %.0f | %s |' % (
            n, j['verdict'], ' (flaky-rerun-pass)' if j.get('flaky_rerun_pass') else '', j['exit_code'], c['passed'], c['failed'],
            c['skipped'] if c['skipped'] is not None else 'n/a', j['seconds'], j['ci_timeout_minutes'], wd,
            ('OVER CI limit (WSL) x%s, not red by itself' % j.get('ci_limit_ratio')) if j.get('over_ci_timeout') else 'within (x%s)' % j.get('ci_limit_ratio')))
    for n, j in rc['jobs'].items():
        if j['verdict'] != 'green' or j.get('failure_details') or j.get('failed_assertion_lines') or j.get('flaky'):
            L += ['', '### %s: %s' % (n, j['verdict']), '']
            L += ['- ' + w for w in j['why']]
            for k in ('failed_suites', 'unittest_fail_lines', 'failure_details', 'failed_assertion_lines'):
                if j.get(k):
                    L.append('- %s:' % k)
                    L += ['    - ' + str(x) for x in j[k][:15]]
            fl = j.get('flaky')
            if fl:
                L.append('- rule 2 (flaky re-run): qualifies=%s%s' % (fl['qualifies'], ' ; reasons: ' + '; '.join(fl['reasons']) if fl['reasons'] else ''))
                for e in fl['suites']:
                    L.append('    - %s: first run FAILED (%s) | in main baseline: %s | re-runs: %s | excused=%s%s' % (
                        e['suite'], '; '.join(t['id'] + ' [' + str(t['kind']) + '] ' + str(t['message'])[:80] for t in e['first_run']['tests']) or e['first_run']['note'],
                        {i: (b['first']['receipt'] if b else None) for i, b in e['baseline'].items()},
                        ', '.join('#%d %s (exit %s, %ss)' % (r['attempt'], 'PASS' if r['passed'] else 'FAIL', r.get('exit_code'), r.get('seconds')) for r in e['reruns']),
                        e['excused'], (' | ' + e['why_not_excused']) if e.get('why_not_excused') else ''))
    nat = rc['jobs'].get('native')
    if nat:
        L += ['', '## native: expected-count and skip cross-check', '', '- expected comparison: %s' % json.dumps(nat.get('expected_comparison'), ensure_ascii=False)]
        for s in nat.get('skips', []):
            L.append('- skip: %s x%s allowed=%s (%s)' % (s['suite'], s['skipped'], s['allowed'], s['note']))
    L += ['', 'Logs: `<job>/job.log`; per-job structured data: `<job>/result.json`; aggregate: `receipt.json`.', '']
    (out / 'README.md').write_text('\n'.join(L), encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())
