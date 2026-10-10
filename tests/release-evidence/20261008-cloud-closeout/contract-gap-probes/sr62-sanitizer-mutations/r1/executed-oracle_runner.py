#!/usr/bin/env python3
"""Run unchanged copied unittest bodies against one explicitly pinned private binary.

Only transport discovery and transport receipts are adapted. No oracle, fixture,
expected value or unittest result is edited. This is an instrumented harness,
not a registry-fresh production binary; tests._bridge explicitly permits such
private direct BridgeSession paths without a registry sidecar.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import traceback
import unittest


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--binary-sha256', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--test', action='append', required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    binary = args.binary.resolve()
    if sha(binary) != args.binary_sha256:
        raise RuntimeError('private binary hash changed')
    sys.path.insert(0, str(args.source.resolve()))
    from tests import _bridge
    if not Path(_bridge.__file__).resolve().is_relative_to(args.source.resolve()):
        raise RuntimeError('wrong imported source root')
    _bridge.find_bridge = lambda: str(binary)
    base_session = _bridge.BridgeSession
    sessions = []
    current = {'test': None}

    class RecordedSession(base_session):
        def __init__(self, bridge=None, *, stop_timeout=10, cwd=None, env=None):
            self.record = {'test': current['test'], 'binarySha256': args.binary_sha256,
                           'session': len(sessions), 'commands': [], 'cleanupErrors': []}
            sessions.append(self.record)
            self.folder = args.out / ('session-%03d' % self.record['session'])
            self.folder.mkdir()
            # The same BridgeSession protocol, with named files opened before
            # launch so an outer timeout cannot discard anonymous stderr.
            self.bridge = _bridge._checked_explicit(bridge) if bridge is not None else _bridge.find_bridge()
            self.stop_timeout = stop_timeout
            self._stopped = False
            self.stderr = (self.folder / 'stderr.raw').open('w+b')
            self._stdout_capture = (self.folder / 'stdout.raw').open('w', encoding='utf-8')
            self._live_capture = (self.folder / 'transport-live.jsonl').open('w', encoding='utf-8')
            try:
                self.process = subprocess.Popen([self.bridge], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=self.stderr, text=True, encoding='utf-8', cwd=cwd, env=env)
            except BaseException:
                for handle in (self.stderr, self._stdout_capture, self._live_capture):
                    handle.close()
                raise
            self.record['pid'] = self.process.pid
            self._live_capture.write(json.dumps({'started': self.record}) + '\n')
            self._live_capture.flush()

        def command(self, text):
            row = {'command': text}
            self.record['commands'].append(row)
            self._live_capture.write(json.dumps({'command': text}, ensure_ascii=False) + '\n')
            self._live_capture.flush()
            if text.startswith('loadfile '):
                path = Path(text[len('loadfile '):])
                if path.is_file():
                    data = path.read_bytes()
                    name = 'load-%04d.scene' % len(self.record['commands'])
                    (self.folder / name).write_bytes(data)
                    row['loadedInput'] = {'path': name, 'sha256': hashlib.sha256(data).hexdigest()}
            try:
                self.process.stdin.write(text + '\n')
                self.process.stdin.flush()
                raw = self.process.stdout.readline()
                self._stdout_capture.write(raw)
                self._stdout_capture.flush()
                if not raw:
                    raise AssertionError('bridge closed: ' + self.stderr_text())
                response = json.loads(raw)
                row['response'] = response
                self._live_capture.write(json.dumps({'response': response}, ensure_ascii=False) + '\n')
                self._live_capture.flush()
                return response
            except BaseException:
                row['error'] = traceback.format_exc()
                raise

        send = command

        def stop(self):
            if self._stopped:
                return
            self._stopped = True
            try:
                self.process.stdin.close()
                try:
                    self.process.wait(timeout=self.stop_timeout)
                except subprocess.TimeoutExpired:
                    self.record['stopTimeout'] = True
                    self.process.kill()
                    self.process.wait()
                self.record['exitCode'] = self.process.returncode
            except BaseException:
                self.record['cleanupErrors'].append(traceback.format_exc())
                if self.process.poll() is None:
                    self.process.kill()
                    self.process.wait()
                self.record['exitCode'] = self.process.returncode
            finally:
                try:
                    self.stderr.seek(0)
                    raw = self.stderr.read()
                    self.record['stderrSha256'] = hashlib.sha256(raw).hexdigest()
                    self.record['sanitizerDiagnostic'] = bool(re.search(
                        rb'AddressSanitizer|LeakSanitizer|UndefinedBehaviorSanitizer|runtime error:', raw))
                    remaining = self.process.stdout.read()
                    (self.folder / 'stdout-tail.raw').write_text(remaining)
                    self.record['unexpectedStdoutTail'] = bool(remaining.strip())
                except BaseException:
                    self.record['cleanupErrors'].append(traceback.format_exc())
                for handle in (self.process.stdout, self.stderr, self._stdout_capture, self._live_capture):
                    try:
                        handle.close()
                    except BaseException:
                        self.record['cleanupErrors'].append(traceback.format_exc())
                (self.folder / 'transport.json').write_text(json.dumps(self.record, ensure_ascii=False, indent=2) + '\n')
            if (self.record.get('exitCode') != 0 or self.record.get('sanitizerDiagnostic')
                    or self.record.get('stopTimeout') or self.record.get('unexpectedStdoutTail')
                    or self.record['cleanupErrors']):
                raise RuntimeError('private native process failed health/cleanup: ' + str(self.folder))

        close = stop

    _bridge.BridgeSession = RecordedSession
    details = []

    class Result(unittest.TextTestResult):
        def startTest(self, test):
            current['test'] = test.id()
            super().startTest(test)

        def detail(self, kind, test, err):
            frames = [{'file': frame.filename, 'line': frame.lineno, 'function': frame.name}
                      for frame in traceback.extract_tb(err[2])]
            details.append({'kind': kind, 'test': test.id(), 'exception': err[0].__name__,
                            'frames': frames, 'traceback': ''.join(traceback.format_exception(*err))})

        def addFailure(self, test, err):
            self.detail('failure', test, err)
            super().addFailure(test, err)

        def addError(self, test, err):
            self.detail('error', test, err)
            super().addError(test, err)

        def addSubTest(self, test, subtest, err):
            if err:
                self.detail('failure' if issubclass(err[0], test.failureException) else 'error', subtest, err)
            super().addSubTest(test, subtest, err)

    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in args.test)
    result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
    unhealthy = [r['session'] for r in sessions if r.get('exitCode') != 0 or r.get('sanitizerDiagnostic')
                 or r.get('stopTimeout') or r.get('unexpectedStdoutTail') or r['cleanupErrors']]
    report = {'schema': 'geometry-sgr62-original-oracle/1', 'tests': args.test,
              'testsRun': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'skipped': result.skipped, 'unexpectedSuccesses': len(result.unexpectedSuccesses),
              'expectedFailures': len(result.expectedFailures), 'details': details,
              'sessions': len(sessions), 'unhealthySessions': unhealthy,
              'binary': str(binary), 'binarySha256': sha(binary),
              'sanitizerEnvironment': {key: os.environ.get(key) for key in ['ASAN_OPTIONS', 'UBSAN_OPTIONS']}}
    (args.out / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    clean = result.wasSuccessful() and not result.skipped and not result.expectedFailures and not unhealthy
    return 0 if clean else 1


if __name__ == '__main__':
    raise SystemExit(main())
