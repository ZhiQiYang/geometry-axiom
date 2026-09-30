"""Shared plumbing for the tests that drive the native bridge (geometry-web/web_bridge.c).

Every bridge-backed test file used to carry its own copy of "find an exe -> start a child -> send a line -> read one
JSON line -> stop".  This module is the one copy.

    from tests import _bridge            # works for `python tests/x.py` and `python -m unittest tests.x`
    path = _bridge.find_bridge()         # unittest.SkipTest (with a how-to-build hint) when there is no trustworthy exe
    with _bridge.BridgeSession() as s:   # or BridgeSession(path); s.command('reset') -> parsed JSON (s.send is an alias)
        s.line('surface 1 ...')          # == s.command('line surface 1 ...')
    p = _bridge.run_once('reset\\ndump\\n')  # one-shot batch (stdin in, CompletedProcess out)

Which exe (find_bridge), first match wins:
  1. $GEOMETRY_TEST_BRIDGE (run_all.py sets it to a fresh exe).  Explicit, so it is used as given, but it must exist.
  2. $GEOMETRY_ENGINEERING_BRIDGE: the old name of the same variable; still read, prints a deprecation notice once.
  3. tests/binaries.py: the bridge it built, only when its source fingerprint is fresh.  On non-Windows a stale or
     missing one is (re)built with `cc` into /tmp/geometry-tests (binaries.build_one, under the build lock).
     On Windows it is never built here (Smart App Control blocks newly appearing exes): stale/missing -> SkipTest.
There is deliberately NO fallback to geometry-web/web_bridge.exe: that file is not checked against the sources, and a
green run on a stale exe is worse than a red one.  Nothing is ever printed for a *good* lookup other than step 2's notice.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import binaries  # noqa: E402

ENV_PRIMARY = 'GEOMETRY_TEST_BRIDGE'
ENV_LEGACY = 'GEOMETRY_ENGINEERING_BRIDGE'   # deprecated alias, kept so existing shells/scripts keep working
BUILD_HINT = ('python tests/binaries.py build（只重編 stale/missing 的；Windows 上 Smart App Control 會擋新編的 exe，'
              '所以不會在測試裡自動編），或用 %s 指向你自己編好的 bridge' % ENV_PRIMARY)

_resolved = {}          # (primary env, legacy env) -> ('ok', path) | ('skip', message); one lookup per process
_warned_legacy = False


def _exists(value: str) -> bool:
    # a launcher may be a bare command name (e.g. a WSL wrapper on PATH), not only a file path
    return Path(value).is_file() or shutil.which(value) is not None


def _lookup():
    global _warned_legacy
    primary = os.environ.get(ENV_PRIMARY)
    if primary:
        if _exists(primary):
            return 'ok', primary
        return 'skip', '%s=%s 指向的檔案不存在；%s' % (ENV_PRIMARY, primary, BUILD_HINT)
    legacy = os.environ.get(ENV_LEGACY)
    if legacy:
        if not _warned_legacy:
            _warned_legacy = True
            print('[tests/_bridge] %s 已棄用，請改設 %s（同一支 bridge；目前暫時沿用舊名）。' % (ENV_LEGACY, ENV_PRIMARY),
                  file=sys.stderr)
        if _exists(legacy):
            return 'ok', legacy
        return 'skip', '%s=%s 指向的檔案不存在；%s' % (ENV_LEGACY, legacy, BUILD_HINT)

    info = binaries.inspect_one(binaries.BY_NAME['bridge'])
    if info.state == 'n/a':
        return 'skip', 'bridge 在這個平台不適用：%s' % info.reason
    if info.state != 'fresh' and not binaries.IS_WIN:
        cc = shutil.which(os.environ.get('CC', 'cc'))
        if not cc:
            return 'skip', 'bridge %s（%s），且找不到 C 編譯器 cc；設 %s 指向已編好的 bridge' % (
                info.state, info.reason, ENV_PRIMARY)
        try:
            with binaries.ProcessLock('build'):
                result = binaries.build_one(binaries.BY_NAME['bridge'], log=lambda *_: None)
        except binaries.LockBusy as exc:
            return 'skip', 'bridge %s（%s），而且無法自己建：%s' % (info.state, info.reason, exc)
        if not result.ok:
            return 'skip', 'bridge 建置失敗（%s）：%s' % (result.status, (result.detail or '').splitlines()[0] if result.detail else '')
        info = binaries.inspect_one(binaries.BY_NAME['bridge'])
    if info.state == 'fresh':
        return 'ok', str(info.path)
    return 'skip', 'bridge 不是 fresh：%s（%s）；修法：%s' % (info.state, info.reason, BUILD_HINT)


def find_bridge() -> str:
    """Path of the bridge exe to test against; raises unittest.SkipTest (never falls back to geometry-web/web_bridge.exe)."""
    key = (os.environ.get(ENV_PRIMARY), os.environ.get(ENV_LEGACY))
    if key not in _resolved:
        _resolved[key] = _lookup()
    kind, value = _resolved[key]
    if kind == 'skip':
        raise unittest.SkipTest(value)
    return value


class BridgeSession:
    """One bridge child process speaking the line protocol: one command line in, one JSON line out.

    stderr goes to an anonymous temp file (read back for the failure message when the child dies mid-conversation).
    stop() closes stdin so the bridge exits by itself; if it has not exited after `stop_timeout` seconds it is killed
    (on Windows Popen.kill() *is* TerminateProcess, i.e. terminate())."""

    def __init__(self, bridge=None, *, stop_timeout=10, cwd=None, env=None):
        self.bridge = str(bridge) if bridge is not None else find_bridge()
        self.stop_timeout = stop_timeout
        self._stopped = False
        self.stderr = tempfile.TemporaryFile(mode='w+b')
        try:
            self.process = subprocess.Popen([self.bridge], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=self.stderr, text=True, encoding='utf-8', cwd=cwd, env=env)
        except BaseException:
            self.stderr.close()
            raise

    def stderr_text(self) -> str:
        self.stderr.seek(0)
        return self.stderr.read().decode('utf-8', errors='replace')

    def command(self, text):
        self.process.stdin.write(text + '\n')
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            raise AssertionError('bridge closed: ' + self.stderr_text())
        return json.loads(line)

    send = command

    def line(self, text):
        """`line <text>`: the transactional command form most tests use."""
        return self.command('line ' + text)

    def stop(self):
        if self._stopped:
            return
        self._stopped = True
        self.process.stdin.close()
        try:
            self.process.wait(timeout=self.stop_timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process.stdout.close()
        self.stderr.close()

    close = stop

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.stop()
        return False


def run_once(data, *, text=True, timeout=20, bridge=None):
    """Feed all of `data` to a fresh bridge on stdin and collect everything (subprocess.CompletedProcess).

    text=True: `data` is str, output decoded as UTF-8.  text=False: bytes in, bytes out (for deliberately invalid UTF-8)."""
    kwargs = dict(input=data, capture_output=True, timeout=timeout)
    if text:
        kwargs.update(text=True, encoding='utf-8')
    return subprocess.run([str(bridge) if bridge is not None else find_bridge()], **kwargs)
