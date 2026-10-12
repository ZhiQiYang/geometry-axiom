#!/usr/bin/env python3
"""Native test binaries: one registry, a source fingerprint per exe, freshness check, guarded build.

Why this exists
---------------
* A stale exe makes a whole test file go red (looks like the program broke); a test that silently
  falls back to some old default exe goes green on stale code.  Neither is visible without a
  freshness check.
* On this machine Smart App Control (SAC) blocks *newly appearing* unsigned exes.  The cure is
  "never recompile when the sources did not change": every exe gets a sidecar
  ``<exe>.fingerprint.json`` and ``build`` only touches exes that are stale or missing.

Usage
-----
    python tests/binaries.py status            # fresh / stale / missing per exe
    python tests/binaries.py build [name ...]  # rebuild only stale/missing ones; fresh ones: "reused"
    python tests/binaries.py list              # registry (sources, flags, env variables)

Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory> off Windows),
never into the repo.  Exit code of ``status``: 0 all fresh, 1 otherwise.  Exit code of ``build``:
0 all fresh afterwards, 1 a compile failure, 2 environment block (SAC / locked exe / no compiler) or another
``build`` already running (``build.lock`` in the output directory; two builds at once would clobber each other's exe).

Fingerprint = sha256(compile command string, then sorted [relative path, sha256(content with
CRLF->LF)]).  The file set is deliberately generous: the exe's own source + current_geometry.c +
every .c/.h/.inc under geometry-core/ and geometry-web/ (vendor/ excluded) + root-level .h/.inc.
Repo-root ``_mutant_*.c`` files (another tool's scratch) are never scanned.
"""
from __future__ import annotations

import argparse
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
IS_WIN = os.name == 'nt'
OUT_DIR = (Path(tempfile.gettempdir()) / 'geometry-tests') if IS_WIN else Path('<isolated-test-directory>')
SIDECAR_SUFFIX = '.fingerprint.json'
SAC_WAIT_SECONDS = int(os.environ.get('GEOMETRY_BIN_SAC_WAIT', '15'))
SAC_RETRIES = 3
VCVARS_FALLBACK = r'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
EXTRA_SCAN_SKIP_DIRS = {'vendor', 'node_modules', '__pycache__', '.git'}


class Binary:
    def __init__(self, name, exe, source, win_flags, win_link, posix_flags, envs, win_only=False,
                 include=None, generated=None, smoke=None):
        self.name = name
        self.exe = exe + ('.exe' if IS_WIN else '')
        self.source = source            # repo-relative path, or None when `generated` supplies the text
        self.win_flags = win_flags      # cl flags before the source file
        self.win_link = win_link        # cl flags after /link
        self.posix_flags = posix_flags  # cc flags (before the source)
        self.envs = envs                # environment variables that point at this exe
        self.win_only = win_only
        self.include = include          # extra include dir (repo-relative) or None
        self.generated = generated      # callable -> (label, text) for a generated source
        self.smoke = smoke              # 'core' | 'bridge' | 'integrity' | 'model' | 'gdi' | 'engjson'

    @property
    def path(self):
        return OUT_DIR / self.exe

    @property
    def sidecar(self):
        return OUT_DIR / (self.exe + SIDECAR_SUFFIX)

    def applicable(self):
        return IS_WIN or not self.win_only

    def command_string(self):
        """Machine-independent description of the compile command (what goes into the fingerprint)."""
        src = self.source or ('<generated:%s>' % self.generated()[0])
        if IS_WIN:
            parts = ['cl', *self.win_flags, src]
            if self.include:
                parts.append('/I' + self.include)
            if self.win_link:
                parts += ['/link', *self.win_link]
            return ' '.join(parts) + ' -> ' + self.exe
        parts = [os.environ.get('CC', 'cc'), *self.posix_flags]
        if self.include:
            parts += ['-I', self.include]
        parts += [src, '-lm'] if self.name != 'engjson' else [src]
        return ' '.join(parts) + ' -> ' + self.exe


def _engjson_harness():
    """The C helper that tests/test_engineering_json.py embeds as HARNESS (extracted, never imported)."""
    tree = ast.parse((ROOT / 'tests/test_engineering_json.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'HARNESS' for t in node.targets):
            return 'tests/test_engineering_json.py#HARNESS', ast.literal_eval(node.value)
    raise RuntimeError('HARNESS not found in tests/test_engineering_json.py')


_STACK = ['/STACK:16777216']
REGISTRY = [
    # core: /U_WIN32 (headless geometry layer, same as tests/_cl.bat, geometry-web/build.bat and what tests/mutate.py judges
    # with).  The GUI flavour (tests/_clw.bat) was blocked by SAC on every attempt on this machine (WinError 4551, 4 builds,
    # 20+ minutes) while this one launches at once; run_tests / test_cli_args / polydraft only use --no-window.
    Binary('core', 'core', 'current_geometry.c', ['/nologo', '/utf-8', '/O2', '/W3', '/U_WIN32'], _STACK,
           ['-std=c11', '-O2'], ['GEOMETRY_TEST_CORE'], smoke='core'),
    Binary('bridge', 'bridge', 'geometry-web/web_bridge.c', ['/nologo', '/utf-8', '/O2', '/W3', '/U_WIN32'], _STACK,
           ['-std=c11', '-O2'], ['GEOMETRY_TEST_BRIDGE', 'GEOMETRY_ENGINEERING_BRIDGE'], smoke='bridge'),
    Binary('integrity', 'integrity', 'tests/test_core_integrity.c', ['/nologo', '/utf-8', '/O2', '/W3'], _STACK,
           ['-std=c11', '-O2'], [], smoke='integrity'),
    Binary('gdi', 'gdi-contract', 'tests/gdi_contract_harness.c',
           ['/nologo', '/utf-8', '/Od', '/W3', '/TC', '/I.'], _STACK + ['user32.lib', 'gdi32.lib', 'comdlg32.lib'],
           [], ['GEOMETRY_TEST_GDI_HARNESS'], win_only=True, smoke='gdi'),
    Binary('model-base', 'model-base', 'geometry-core/model_base.c', ['/nologo', '/utf-8', '/O2', '/W3', '/U_WIN32'],
           _STACK, ['-std=c11', '-O2'], ['GEOMETRY_MODEL_BASE'], smoke='model'),
    # A sixth helper: test_engineering_json.py used to compile this per run (and hit SAC every time).
    Binary('engjson', 'engineering-json-test', None, ['/nologo', '/utf-8', '/O2', '/W4', '/wd4505'], [],
           ['-std=c11', '-O2', '-Wall', '-Wextra', '-Wno-unused-function'], ['GEOMETRY_TEST_ENGINEERING_JSON'],
           include='geometry-core', generated=_engjson_harness, smoke='engjson'),
]
BY_NAME = {b.name: b for b in REGISTRY}


# ---------------------------------------------------------------- process lock

class LockBusy(Exception):
    pass


class ProcessLock:
    """Advisory lock on ``OUT_DIR/<name>.lock`` held for the life of the process (released by the OS on exit or crash,
    so a dead run never leaves a stale lock).  ``with ProcessLock('build'):`` raises LockBusy when someone else holds it.
    Two locks exist: ``build`` (binaries.py build) and ``run_all`` (tests/run_all.py)."""

    def __init__(self, name):
        self.name = name
        self.path = OUT_DIR / ('%s.lock' % name)
        self._fh = None

    def __enter__(self):
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        fh = open(self.path, 'a+b')
        try:
            if IS_WIN:
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            raise LockBusy('另一個「%s」正在執行（鎖檔 %s 被占用）；等它結束再跑，或確認沒有殘留行程。' % (self.name, self.path))
        self._fh = fh
        return self

    def __exit__(self, *exc):
        fh, self._fh = self._fh, None
        if fh is not None:
            try:
                if IS_WIN:
                    import msvcrt
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                fh.close()
            except OSError:
                pass
        return False


# ---------------------------------------------------------------- fingerprint

def _normalized_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def _identity_signature(st):
    """Fields ``stat`` and ``fstat`` can both report for one unchanged file.

    Device, inode, size and mtime catch replacement and an ordinary write.
    The last field has to be the same clock on both calls. On Windows, CPython
    reports creation time in ``stat().st_ctime`` and a different time in
    ``fstat().st_ctime``. ``st_birthtime_ns`` (Python 3.12+) matches across
    those calls when the runtime provides it; otherwise Windows keeps
    ``st_ctime``. Other platforms always keep ``st_ctime``, which still moves
    on a metadata update.
    """
    if os.name == 'nt':
        birth = getattr(st, 'st_birthtime_ns', None)
        stamp = birth if isinstance(birth, int) else st.st_ctime_ns
    else:
        stamp = st.st_ctime_ns
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, stamp


def _observed_signature(st):
    """Fields from one stat API, compared only with another result of that API.

    ``fstat().st_ctime`` moves on an in-place same-size write even after mtime
    is restored. Birth time and ``stat().st_ctime`` do not. Comparing this
    snapshot with a later ``fstat`` keeps that change-time check without
    requiring ``stat().st_ctime == fstat().st_ctime``.
    """
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns,
            getattr(st, 'st_birthtime_ns', None))


def _binary_identity(path: Path):
    """Hash raw bytes (same domain as mutate.py), rejecting a changing file."""
    before = path.stat()
    before_sig = _identity_signature(before)
    h = hashlib.sha256()
    with path.open('rb') as fh:
        opened = os.fstat(fh.fileno())
        if _identity_signature(opened) != before_sig:
            raise OSError('binary changed before hashing')
        opened_obs = _observed_signature(opened)
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
        if _observed_signature(os.fstat(fh.fileno())) != opened_obs:
            raise OSError('binary changed during hashing')
    if _identity_signature(path.stat()) != before_sig:
        raise OSError('binary replaced during hashing')
    return {'exe_size': before.st_size, 'exe_mtime_ns': before.st_mtime_ns,
            'exe_sha256': h.hexdigest()}


def _identity_matches(record, identity):
    return isinstance(record, dict) and all(record.get(k) == v for k, v in identity.items())


def _write_json_atomic(path: Path, data):
    """Publish one complete credential; failed writes never leave a partial sidecar."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                         dir=path.parent, suffix='.tmp', delete=False) as fh:
            temporary = Path(fh.name)
            json.dump(data, fh, ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _scan_shared():
    """Files every native binary depends on (by #include of the core)."""
    files = [ROOT / 'current_geometry.c']
    for pattern in ('*.h', '*.inc'):
        files += sorted(ROOT.glob(pattern))
    for top, patterns in (('geometry-core', ('*.c', '*.h', '*.inc')), ('geometry-web', ('*.c', '*.h', '*.inc'))):
        base = ROOT / top
        for pattern in patterns:
            for f in base.rglob(pattern):
                rel_parts = f.relative_to(base).parts[:-1]
                if any(part in EXTRA_SCAN_SKIP_DIRS for part in rel_parts):
                    continue
                files.append(f)
    return files


def compute_fingerprint(b: Binary):
    """Return (fingerprint, {relative path: sha256}, command string)."""
    hashes = {}
    for f in _scan_shared():
        if f.is_file():
            hashes[f.relative_to(ROOT).as_posix()] = _normalized_sha(f)
    if b.source:
        hashes[b.source] = _normalized_sha(ROOT / b.source)
    else:
        label, text = b.generated()
        hashes[label] = hashlib.sha256(text.replace('\r\n', '\n').encode('utf-8')).hexdigest()
    command = b.command_string()
    h = hashlib.sha256()
    h.update(command.encode('utf-8'))
    h.update(b'\0')
    for rel in sorted(hashes):
        h.update(('%s\0%s\n' % (rel, hashes[rel])).encode('utf-8'))
    return h.hexdigest(), hashes, command


# ---------------------------------------------------------------- status

def resolve_executable(value) -> Path:
    """Keep existing local-file/PATH precedence, then pin the chosen absolute target.

    Hashing and subprocess callers must use this same path; a child cwd or PATH
    must not re-resolve a relative/bare override to different bytes.
    """
    value = os.fspath(value)
    chosen = value if Path(value).is_file() else (shutil.which(value) or value)
    return Path(chosen).resolve()


class Info:
    def __init__(self, binary, state, reason, fingerprint=None, path=None):
        self.binary = binary
        self.name = binary.name
        self.state = state          # fresh | stale | missing | n/a
        self.reason = reason
        self.path = Path(path) if path is not None else binary.path
        self.fingerprint = fingerprint

    def as_dict(self):
        return {'name': self.name, 'state': self.state, 'reason': self.reason, 'path': str(self.path)}


def inspect_one(b: Binary, path=None) -> Info:
    """Check registry or explicit binary path against this binary's current sources."""
    requested = path if path is not None else b.path
    try:
        path = resolve_executable(requested)
    except (OSError, RuntimeError) as exc:
        return Info(b, 'stale', '無法解析 binary 路徑：%s' % exc, path=Path(requested).absolute())
    sidecar = path.with_name(path.name + SIDECAR_SUFFIX)
    def info(state, reason, fingerprint=None):
        return Info(b, state, reason, fingerprint, path)
    if not b.applicable():
        return info('n/a', '僅 Windows')
    try:
        fingerprint, hashes, _ = compute_fingerprint(b)
    except (OSError, RuntimeError, SyntaxError) as exc:
        return info('stale', '無法計算來源指紋：%s' % exc)
    if not path.is_file():
        return info('missing', '找不到 %s' % path, fingerprint)
    if not sidecar.is_file():
        if path == b.path and _pending_matches(b, fingerprint):
            return info('stale', '已由 binaries.py 編好但尚未通過 SAC 評估（環境阻擋中；再跑 build 只重試啟動，不重編）', fingerprint)
        return info('stale', '沒有 sidecar（這支 exe 不是 binaries.py 建的，來源是否相符無從證明）', fingerprint)
    try:
        side = json.loads(sidecar.read_text(encoding='utf-8'))
        if not isinstance(side, dict) or not isinstance(side.get('files'), dict):
            raise ValueError('sidecar 必須是含 files 物件的 JSON 物件')
    except (OSError, ValueError) as exc:
        return info('stale', 'sidecar 讀不了：%s' % exc, fingerprint)
    if side.get('fingerprint') != fingerprint:
        old = side.get('files') or {}
        changed = sorted({k for k in set(old) | set(hashes) if old.get(k) != hashes.get(k)})
        detail = ''
        if changed:
            detail = '；變動：' + ', '.join(changed[:4]) + (' 等 %d 個檔' % len(changed) if len(changed) > 4 else '')
        if side.get('command') != b.command_string() and not changed:
            detail = '；編譯指令改了'
        return info('stale', '來源指紋不符（exe 建於 %s，指紋 %s… ≠ 現在 %s…）%s' % (
            side.get('built_at', '?'), str(side.get('fingerprint'))[:10], fingerprint[:10], detail), fingerprint)
    try:
        identity = _binary_identity(path)
    except OSError as exc:
        return info('stale', '無法核對 binary SHA-256：%s' % exc, fingerprint)
    if side.get('exe_sha256') != identity['exe_sha256']:
        return info('stale', 'exe SHA-256 與 sidecar 不符或缺失（舊版 sidecar 須重建）', fingerprint)
    if not _identity_matches(side, identity):
        return info('stale', 'exe 的大小／mtime 與 sidecar 記錄不符（建好之後被別處覆寫過）', fingerprint)
    return info('fresh', '來源與 binary SHA-256 相符（建於 %s）' % side.get('built_at', '?'), fingerprint)


def inspect_all(names=None):
    selected = _select(names)
    return {b.name: inspect_one(b) for b in selected}


def require_fresh(name, path):
    """Explicit test overrides use the same source/content oracle as registry reuse."""
    info = inspect_one(BY_NAME[name], path)
    if info.state != 'fresh':
        raise RuntimeError('%s 不是 fresh：%s（%s）' % (path, info.state, info.reason))
    return str(info.path)


def _select(names):
    if not names:
        return list(REGISTRY)
    out = []
    for n in names:
        if n not in BY_NAME:
            raise SystemExit('未知的二進位名稱 %r；可用：%s' % (n, ', '.join(BY_NAME)))
        out.append(BY_NAME[n])
    return out


def env_vars(infos=None, only_fresh=True):
    """{ENV_VAR: exe path} for every registered binary (only fresh ones by default)."""
    infos = infos or inspect_all()
    env = {}
    for name, info in infos.items():
        if info.state == 'n/a':
            continue
        if only_fresh and info.state != 'fresh':
            continue
        for var in info.binary.envs:
            env[var] = str(info.path)
    return env


# ---------------------------------------------------------------- build

class BuildResult:
    def __init__(self, name, status, detail=''):
        self.name = name
        self.status = status    # reused | built | compile-failed | blocked | locked | no-compiler | n/a
        self.detail = detail

    @property
    def ok(self):
        return self.status in ('reused', 'built', 'n/a')

    @property
    def environmental(self):
        return self.status in ('blocked', 'locked', 'no-compiler')


def find_vcvars():
    override = os.environ.get('GEOMETRY_VCVARS')
    if override and Path(override).is_file():
        return override
    if Path(VCVARS_FALLBACK).is_file():
        return VCVARS_FALLBACK
    vswhere = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    if vswhere.is_file():
        try:
            install = subprocess.check_output([str(vswhere), '-latest', '-products', '*', '-requires',
                                               'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
                                               '-property', 'installationPath'], text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
        candidate = Path(install) / 'VC/Auxiliary/Build/vcvars64.bat'
        if candidate.is_file():
            return str(candidate)
    return None


def _is_locked(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        with open(path, 'ab'):
            return False
    except OSError:
        return True


def _materialize_source(b: Binary) -> Path:
    if b.source:
        return ROOT / b.source
    label, text = b.generated()
    target = OUT_DIR / 'src'
    target.mkdir(parents=True, exist_ok=True)
    src = target / 'engineering-json-test.c'
    src.write_text(text, encoding='utf-8')
    return src


def _compile(b: Binary, src: Path):
    """Run the compiler. Returns (returncode, combined output, compiler-missing flag)."""
    obj_dir = OUT_DIR / 'obj' / b.name
    obj_dir.mkdir(parents=True, exist_ok=True)
    if IS_WIN:
        vcvars = find_vcvars()
        if not vcvars:
            return None, '找不到 vcvars64.bat（可用環境變數 GEOMETRY_VCVARS 指定）', True
        flags = ' '.join(b.win_flags)
        include = ' /I"%s"' % (ROOT / b.include) if b.include else ''
        link = (' /link ' + ' '.join(b.win_link)) if b.win_link else ''
        script = OUT_DIR / ('_binaries_build_%s.bat' % b.name)
        # /Fo gets a full .obj file name: a trailing backslash before the closing quote would eat the quote.
        script.write_text('@echo off\r\ncall "%s" >nul 2>&1\r\ncd /d "%s"\r\ncl %s%s /Fe:"%s" /Fo:"%s" "%s"%s\r\n' % (
            vcvars, ROOT, flags, include, b.path, obj_dir / (src.stem + '.obj'), src, link), encoding='utf-8')
        cmd = ['cmd', '/d', '/c', str(script)]
    else:
        cc = os.environ.get('CC', 'cc')
        cmd = [cc, *b.posix_flags]
        if b.include:
            cmd += ['-I', str(ROOT / b.include)]
        cmd += [str(src), '-o', str(b.path)]
        if b.name != 'engjson':
            cmd.append('-lm')
    try:
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors='replace', timeout=900)
    except FileNotFoundError:
        return None, '找不到編譯器 %s' % cmd[0], True
    except subprocess.TimeoutExpired:
        return 124, '編譯逾時（900 秒）', False
    return run.returncode, (run.stdout or '') + (run.stderr or ''), False


def _smoke_once(b: Binary):
    """Launch the exe briefly so SAC evaluates it.  Only the *launch* matters, not the exit code."""
    # Recheck each SAC retry too: a source/binary change during the wait must
    # stop the next launch, even if size and mtime were preserved.
    if not _pending_matches(b, compute_fingerprint(b)[0]):
        raise OSError('source/binary identity changed before smoke')
    work = OUT_DIR / 'smoke' / b.name
    work.mkdir(parents=True, exist_ok=True)
    exe = str(b.path)
    kind = b.smoke
    kwargs = dict(cwd=work, capture_output=True, timeout=30)
    if kind == 'core':
        cmd, extra = [exe, '--no-window', '--help'], {}
    elif kind == 'bridge':
        cmd, extra = [exe], {'input': b'reset\n'}
    elif kind == 'model':
        scene = work / 'empty.scene'
        scene.write_bytes(b'')
        cmd, extra = [exe, str(scene)], {}
    elif kind == 'engjson':
        empty = work / 'empty.bin'
        empty.write_bytes(b'')
        cmd, extra = [exe, 'hash', str(empty)], {}
    else:  # integrity, gdi: run them as they are
        cmd, extra = [exe], {}
    try:
        subprocess.run(cmd, **kwargs, **extra)
    except subprocess.TimeoutExpired:
        pass  # it started; that is all SAC cares about


def smoke_with_sac_retry(b: Binary, log=print):
    """Return None when the exe launches, else the error text (SAC block survived all retries)."""
    last = None
    for attempt in range(SAC_RETRIES + 1):
        try:
            _smoke_once(b)
            return None
        except OSError as exc:
            last = '%s (winerror=%s)' % (exc, getattr(exc, 'winerror', None))
            blocked = getattr(exc, 'winerror', None) == 4551 or isinstance(exc, PermissionError)
            if not blocked:
                return last
            if attempt < SAC_RETRIES:
                log('  %s：被 SAC 擋（%s）；%d 秒後重試 (%d/%d)' % (b.name, last, SAC_WAIT_SECONDS, attempt + 1, SAC_RETRIES))
                time.sleep(SAC_WAIT_SECONDS)
    return last


def _pending_path(b: Binary) -> Path:
    return OUT_DIR / (b.exe + '.pending.json')


def _pending_matches(b: Binary, fingerprint: str) -> bool:
    """True when the exe on disk is one *we* compiled from exactly these sources but SAC has not released yet."""
    try:
        pend = json.loads(_pending_path(b).read_text(encoding='utf-8'))
        identity = _binary_identity(b.path)
    except (OSError, ValueError):
        return False
    return (isinstance(pend, dict) and pend.get('fingerprint') == fingerprint
            and _identity_matches(pend, identity))


def _looks_blocked(err: str) -> bool:
    return 'winerror=4551' in err or 'Permission' in err or 'denied' in err.lower() or '拒絕存取' in err


def build_one(b: Binary, log=print, force=False) -> BuildResult:
    try:
        return _build_one(b, log, force)
    except (OSError, ValueError, RuntimeError, SyntaxError) as exc:
        b.sidecar.unlink(missing_ok=True)
        _pending_path(b).unlink(missing_ok=True)
        return BuildResult(b.name, 'compile-failed', '無法建立可信 binary 記錄：%s' % exc)


def _build_one(b: Binary, log=print, force=False) -> BuildResult:
    if not b.applicable():
        return BuildResult(b.name, 'n/a', '僅 Windows')
    info = inspect_one(b)
    if info.state == 'fresh' and not force:
        return BuildResult(b.name, 'reused', '沿用（%s）' % info.reason)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if _is_locked(b.path):
        return BuildResult(b.name, 'locked', '%s 被行程鎖住或不可寫；先結束使用它的行程（bridge／serve.py）再重建' % b.path)
    fingerprint, hashes, command = compute_fingerprint(b)
    started = time.time()
    # The exe is about to change (or be re-judged): a sidecar describing an older state must never survive.
    if b.sidecar.exists():
        b.sidecar.unlink()
    if not force and _pending_matches(b, fingerprint):
        # Compiled from these very sources earlier, SAC blocked it.  Recompiling would only create yet another
        # brand-new binary for SAC to evaluate; just try to launch this one again.
        log('  %s：上次已編好但被 SAC 擋，來源沒變；不重編，只重試啟動' % b.name)
    else:
        _pending_path(b).unlink(missing_ok=True)
        src = _materialize_source(b)
        before = b.path.stat().st_mtime_ns if b.path.exists() else None
        log('  %s：%s（%s）…' % (b.name, '重建' if info.state == 'stale' else '建置', info.reason))
        code, output, no_compiler = _compile(b, src)
        if no_compiler:
            return BuildResult(b.name, 'no-compiler', output)
        exists = b.path.is_file()
        after = b.path.stat().st_mtime_ns if exists else None
        # cl prints the source name before linking, so "saw the file name" proves nothing (LNK1104 looks like
        # success): only exit code + a really-updated exe count.
        if code != 0 or not exists or (before is not None and after == before):
            tail = '\n'.join(output.strip().splitlines()[-8:])
            why = '回傳碼 %s' % code
            if exists and before is not None and after == before:
                why += '，且 exe 的 mtime 沒有更新'
            if 'LNK1104' in output:
                why += '（LNK1104：exe 被鎖住）'
            return BuildResult(b.name, 'compile-failed', '%s\n%s' % (why, tail))
        identity = _binary_identity(b.path)
        if compute_fingerprint(b)[0] != fingerprint:
            return BuildResult(b.name, 'compile-failed', '建置期間來源指紋改變；未啟動、未寫 sidecar')
        _write_json_atomic(_pending_path(b), {'fingerprint': fingerprint, **identity})
    # Never smoke an old/tampered pending binary, nor bless bytes changed by the smoke.
    pending = json.loads(_pending_path(b).read_text(encoding='utf-8'))
    if compute_fingerprint(b)[0] != fingerprint or not _pending_matches(b, fingerprint):
        _pending_path(b).unlink(missing_ok=True)
        return BuildResult(b.name, 'compile-failed', '啟動前來源／binary 指紋改變；未寫 sidecar')
    err = smoke_with_sac_retry(b, log)
    if err:
        if _looks_blocked(err):
            return BuildResult(b.name, 'blocked', 'SAC 擋住新二進位（重試 %d 次仍被擋；未寫 sidecar；再跑 build 只會重試啟動、不會重編）：%s' % (SAC_RETRIES, err))
        _pending_path(b).unlink(missing_ok=True)
        return BuildResult(b.name, 'compile-failed', '編得出來但無法啟動：%s' % err)
    if compute_fingerprint(b)[0] != fingerprint or not _identity_matches(pending, _binary_identity(b.path)):
        _pending_path(b).unlink(missing_ok=True)
        return BuildResult(b.name, 'compile-failed', '啟動期間來源／binary 指紋改變；未寫 sidecar')
    _write_json_atomic(b.sidecar, {
        'name': b.name, 'fingerprint': fingerprint, 'command': command,
        'built_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        'build_seconds': round(time.time() - started, 1),
        'exe': b.exe, **{k: pending[k] for k in ('exe_size', 'exe_mtime_ns', 'exe_sha256')},
        'files': hashes,
    })
    _pending_path(b).unlink(missing_ok=True)
    return BuildResult(b.name, 'built', '建好 %s' % b.path)


def build(names=None, log=print, force=False):
    """Build only what is stale/missing. Returns {name: BuildResult}."""
    return {b.name: build_one(b, log, force) for b in _select(names)}


# ---------------------------------------------------------------- CLI

def _mtime(path: Path):
    try:
        return datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    except OSError:
        return '-'


def cmd_status(args):
    infos = inspect_all(args.names)
    bad = 0
    print('輸出目錄：%s' % OUT_DIR)
    for name, info in infos.items():
        label = {'fresh': 'fresh  ', 'stale': 'STALE  ', 'missing': 'MISSING', 'n/a': 'n/a    '}[info.state]
        print('%-10s %s  %s' % (name, label, info.reason))
        if info.state in ('fresh', 'stale'):
            print('%-10s         exe mtime %s' % ('', _mtime(info.path)))
        if info.state in ('stale', 'missing'):
            bad += 1
    if bad:
        print('\n%d 支不是 fresh；修法：python tests/binaries.py build' % bad)
    return 1 if bad else 0


def cmd_build(args):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with ProcessLock('build'):
            results = build(args.names, force=args.force)
    except LockBusy as exc:
        print('錯誤：%s' % exc)
        return 2
    worst = 0
    for name, r in results.items():
        tag = {'reused': '沿用', 'built': '已建', 'n/a': '略過', 'compile-failed': '編譯失敗',
               'blocked': '環境阻擋', 'locked': '環境阻擋(exe 被鎖)', 'no-compiler': '環境阻擋(無編譯器)'}[r.status]
        print('%-10s %-14s %s' % (name, tag, r.detail.splitlines()[0] if r.detail else ''))
        for extra in r.detail.splitlines()[1:]:
            print('%-10s %-14s   %s' % ('', '', extra))
        if r.status == 'compile-failed':
            worst = max(worst, 1) if worst != 2 else 2
        elif r.environmental:
            worst = 2
    if worst == 0:
        print('\n全部 fresh 或略過。')
    return worst


def cmd_list(args):
    for b in REGISTRY:
        print('%-10s %s' % (b.name, b.path))
        print('%-10s   來源 %s' % ('', b.source or '(由 tests/test_engineering_json.py 的 HARNESS 產生)'))
        print('%-10s   指令 %s' % ('', b.command_string()))
        print('%-10s   環境變數 %s' % ('', ', '.join(b.envs) or '(無；直接執行)'))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = parser.add_subparsers(dest='cmd', required=True)
    for name, fn in (('status', cmd_status), ('build', cmd_build), ('list', cmd_list)):
        p = sub.add_parser(name)
        p.add_argument('names', nargs='*', help='只處理這幾支（core bridge integrity gdi model-base engjson）')
        if name == 'build':
            p.add_argument('--force', action='store_true', help='連 fresh 的也重編（會製造新二進位，可能再撞 SAC）')
        p.set_defaults(fn=fn)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    return args.fn(args)


if __name__ == '__main__':
    sys.exit(main())
