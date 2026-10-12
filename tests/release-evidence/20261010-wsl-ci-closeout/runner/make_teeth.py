#!/usr/bin/env python3
"""Teeth helper: build a throw-away clone  <base_sha> + ONE commit that mutates three fast Python tests.  Never pushed.

    python3 make_teeth.py <base_sha>        -> prints the mutant commit SHA on the last line

The clone lives only in ~/ga-ci/teeth-src (WSL ext4); its remote is removed so it cannot be pushed anywhere.
It is created from the runner's own mirror of D:/geometry-axiom; D:/geometry-axiom is never touched.

  M1  tests/test_feedback_store.py::test_ids_increment_per_day  - one assertion made always wrong        (fails EVERY time)
  M2  tests/test_cli_args.py::test_unknown_option               - fails only on its first execution       (NOT in the main baseline)
  M3  tests/test_rule_case_executor.py::test_exited_leader_...  - fails only on its first execution with
                                                                  the ProcessLookupError of the known flake (IS in the main baseline)

Expected rule-2 outcome: M1 stays red (re-runs fail), M2 stays red (re-run passes but not in baseline = no laundering),
M3 is excused as flaky-rerun-pass.  The job as a whole must therefore be red, and the receipt must name M1 and M2.
The first-execution markers live in /tmp/geometry-tests, i.e. inside the job's private mount namespace, so they persist
between the first run and the re-runs of the same job and never leak to other jobs.
"""
import os
import pathlib
import subprocess
import sys

base = sys.argv[1]
home = pathlib.Path(os.environ.get('HOME', '/root'))
mirror = sorted((home / 'ga-ci' / 'mirrors').glob('*.git'))[0]
src = home / 'ga-ci' / 'teeth-src'
env = dict(os.environ, PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin')


def git(*a, cwd=src, check=True):
    return subprocess.run(['git', '-c', 'core.autocrlf=false', *a], cwd=cwd, env=env, check=check, capture_output=True, text=True).stdout.strip()


subprocess.run(['rm', '-rf', str(src)], check=True)
git('clone', '-q', str(mirror), str(src), cwd=home)
git('-c', 'advice.detachedHead=false', 'checkout', '-q', '--detach', base)
git('remote', 'remove', 'origin')


def mutate(rel, old, new):
    p = src / rel
    data = p.read_bytes().decode('utf-8')
    assert data.count(old) == 1, (rel, data.count(old), old[:60])
    p.write_bytes(data.replace(old, new).encode('utf-8'))


# M1: consistent failure
mutate('tests/test_feedback_store.py', '"F-20260924-002", "F-20260924-003"]', '"F-20260924-002", "F-20260924-999"]')

# M2: fails only the first time it ever runs in this job (NOT a baseline failure)
mutate('tests/test_cli_args.py',
       '    def test_unknown_option(self):\n        for option in',
       '    def test_unknown_option(self):\n'
       "        _m = Path('/tmp/geometry-tests/teeth-failonce-m2.marker')\n"
       '        if not _m.exists():\n'
       "            _m.write_text('x')\n"
       "            self.fail('TEETH-ONLY M2: fails on the first execution only')\n"
       '        for option in')

# M3: the known-flaky test fails once with the known error
mutate('tests/test_rule_case_executor.py',
       '    def test_exited_leader_cannot_leave_descendants_or_unbounded_pipe_cleanup(self):\n        child = self.child()\n',
       '    def test_exited_leader_cannot_leave_descendants_or_unbounded_pipe_cleanup(self):\n'
       "        _m = Path('/tmp/geometry-tests/teeth-failonce-m3.marker')\n"
       '        if not _m.exists():\n'
       "            _m.write_text('x')\n"
       "            raise ProcessLookupError(3, 'No such process')\n"
       '        child = self.child()\n')

print(git('--no-pager', 'diff', '--stat'))
git('-c', 'user.name=teeth-only', '-c', 'user.email=teeth-only@invalid', 'commit', '-q', '-am',
    'TEETH-ONLY (never push): M1 consistent assertion failure, M2 fail-once (not baseline), M3 fail-once (baseline flake)')
print(git('rev-parse', 'HEAD'))
