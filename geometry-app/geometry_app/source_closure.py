"""Ordered source inventory and immutable process-load identity for the host.

Consumers receive individual path/hash pairs and keep their own receipt formats.
This inventory never replaces a model's legacy source or geometry digest.
"""
from hashlib import sha256
from importlib.util import find_spec
import os
from pathlib import Path
import re
import time

from geometry_kernel import __file__ as kernel_file


_FACADE = None
_LOADED = None
# Process-local reuse of complete inventories and binary digests (GEO-261 cost).
# An entry is reused only while every watched directory and every listed file
# still reports the stat signature captured with it; any difference recomputes
# the whole result. A signature whose timestamps are within _RACY_NS of the
# capture is never stored, so a later write inside the same timestamp tick
# cannot hide behind unchanged metadata.
_INVENTORIES = {}
_BINARIES = {}
_RACY_NS = 3_000_000_000
_now_ns = time.time_ns


if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class _FileBasicInfo(ctypes.Structure):
        _fields_ = (("creation", ctypes.c_longlong), ("access", ctypes.c_longlong),
                    ("write", ctypes.c_longlong), ("change", ctypes.c_longlong),
                    ("attributes", wintypes.DWORD))

    _KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _CreateFileW = _KERNEL32.CreateFileW
    _CreateFileW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                             wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    _CreateFileW.restype = wintypes.HANDLE
    _GetFileInformationByHandleEx = _KERNEL32.GetFileInformationByHandleEx
    _GetFileInformationByHandleEx.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
    _GetFileInformationByHandleEx.restype = wintypes.BOOL
    _CloseHandle = _KERNEL32.CloseHandle
    _CloseHandle.argtypes = (wintypes.HANDLE,)
    _INVALID_HANDLE = ctypes.c_void_p(-1).value

    def _change_time_ns(path):
        """NTFS ChangeTime in Unix ns. Windows st_ctime is creation time, so a
        same-size rewrite that restores mtime is visible only here."""
        # FILE_READ_ATTRIBUTES, share read/write/delete, OPEN_EXISTING, BACKUP_SEMANTICS.
        handle = _CreateFileW(str(path), 0x80, 0x7, None, 3, 0x02000000, None)
        if handle is None or handle == _INVALID_HANDLE:
            return None
        try:
            info = _FileBasicInfo()
            if not _GetFileInformationByHandleEx(handle, 0, ctypes.byref(info), ctypes.sizeof(info)):
                return None
            return (info.change - 116444736000000000) * 100
        finally:
            _CloseHandle(handle)
else:
    _change_time_ns = None


def _hash(path, *, text):
    data = path.read_bytes()
    return sha256(data.replace(b"\r\n", b"\n") if text else data).hexdigest()


def _layout(repository=None):
    """The package roots and repository that source_paths scans, as a hashable key."""
    if repository is not None:
        repository = Path(repository).resolve()
        packages = (("geometry-core/geometry_kernel", repository / "geometry-core/geometry_kernel"),
                    ("geometry-core/modeling", repository / "geometry-core/modeling"),
                    ("geometry-app/geometry_app", repository / "geometry-app/geometry_app"),
                    ("geometry-templates/woodworking/geometry_woodworking", repository / "geometry-templates/woodworking/geometry_woodworking"))
    else:
        template = find_spec("geometry_woodworking")
        template_path = None if template is None or not template.submodule_search_locations else Path(next(iter(template.submodule_search_locations)))
        packages = (("geometry-core/geometry_kernel", Path(kernel_file).parent),
                    ("geometry-core/modeling", _FACADE),
                    ("geometry-app/geometry_app", Path(__file__).resolve().parent),
                    ("geometry-templates/woodworking/geometry_woodworking", template_path))
        repository = _FACADE.parent.parent if _FACADE is not None and (_FACADE.parent / "model_base.c").is_file() else None
    return packages, repository


def _collect(packages, repository):
    entries = {}
    for logical, directory in packages:
        if directory is None or not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".json"} and "__pycache__" not in path.parts:
                entries[logical + "/" + path.relative_to(directory).as_posix()] = path
    if repository is not None:
        primary = repository / "current_geometry.c"
        if primary.is_file():
            entries["current_geometry.c"] = primary
        for relative in ("geometry-core", "geometry-app", "geometry-templates"):
            directory = repository / relative
            if directory.is_dir():
                for path in directory.rglob("*"):
                    if path.is_file() and path.suffix in {".c", ".h", ".inc"}:
                        entries[path.relative_to(repository).as_posix()] = path
    return tuple(sorted(entries.items()))


def source_paths(repository=None):
    """Return sorted (logical relative path, actual path) pairs, including data."""
    return _collect(*_layout(repository))


def _watched_directories(packages, repository):
    """Every directory whose entries source_paths can list, or None if not watchable.

    Adding, removing or renaming an entry changes its directory's signature.
    Links are not watched exactly, so any link disables reuse.
    """
    tops = []
    for _, directory in packages:
        if directory is None or not directory.is_dir():
            return None
        tops.append(directory)
    found = []
    if repository is not None:
        found.append(repository)  # direct entries: current_geometry.c and the code roots
        tops += [repository / name for name in ("geometry-core", "geometry-app", "geometry-templates")
                 if (repository / name).is_dir()]
    seen = set()
    stack = list(tops)
    while stack:
        directory = stack.pop()
        if str(directory) in seen:
            continue
        seen.add(str(directory))
        found.append(directory)
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if entry.is_symlink() or (hasattr(entry, "is_junction") and entry.is_junction()):
                        return None
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
        except OSError:
            return None
    return tuple(found)


def _file_signature(path):
    status = os.stat(path)
    change = status.st_ctime_ns if _change_time_ns is None else _change_time_ns(path)
    if change is None:
        return None
    return (status.st_dev, status.st_ino, status.st_size, status.st_mtime_ns, change)


def _directory_signature(path):
    status = os.stat(path)
    return (status.st_dev, status.st_ino, status.st_mtime_ns,
            status.st_ctime_ns if os.name != "nt" else status.st_mtime_ns)


def _signatures(directories, files):
    try:
        observed = (tuple(_directory_signature(path) for path in directories),
                    tuple(_file_signature(path) for path in files))
    except OSError:
        return None
    return None if any(signature is None for signature in observed[1]) else observed


def _settled(signatures, now):
    limit = now - _RACY_NS
    directories, files = signatures
    return (all(signature[2] < limit and signature[3] < limit for signature in directories)
            and all(signature[3] < limit and signature[4] < limit for signature in files))


def _memo_valid(memo):
    directories, files, signatures, _ = memo
    return _signatures(directories, files) == signatures


def source_inventory(repository=None):
    packages, root = _layout(repository)
    key = (packages, root)
    memo = _INVENTORIES.get(key)
    if memo is not None and _memo_valid(memo):
        return memo[3]
    now = _now_ns()
    directories = _watched_directories(packages, root)
    paths = _collect(packages, root)
    files = tuple(path for _, path in paths)
    before = None if directories is None else _signatures(directories, files)
    inventory = tuple((name, _hash(path, text=True)) for name, path in paths)
    if before is not None and _settled(before, now) and _signatures(directories, files) == before:
        _INVENTORIES[key] = (directories, files, before, inventory)
    else:
        _INVENTORIES.pop(key, None)
    return inventory


def initialize(facade_directory):
    global _FACADE, _LOADED
    if _LOADED is None:
        _FACADE = Path(facade_directory).resolve()
        _LOADED = source_inventory()


def current_identity():
    current = source_inventory()
    return {"loaded": _LOADED, "current": current, "fresh": _LOADED is not None and _LOADED == current}


def _binary_signature(path):
    try:
        return _file_signature(path)
    except OSError:
        return None


def _binary_memo_valid(path, memo):
    return _binary_signature(path) == memo[0]


def binary_identity(program, *, wsl_distro=None):
    path = Path(program)
    if wsl_distro is not None:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", wsl_distro) or not str(program).startswith("/"):
            raise ValueError("Invalid WSL adapter identity")
        path = Path("//wsl.localhost") / wsl_distro / str(program).lstrip("/")
    key = (str(program), wsl_distro, str(path))
    memo = _BINARIES.get(key)
    if memo is not None and _binary_memo_valid(path, memo):
        return (str(program), wsl_distro, memo[1])
    now = _now_ns()
    before = _binary_signature(path)
    digest = _hash(path, text=False)
    if (before is not None and before[3] < now - _RACY_NS and before[4] < now - _RACY_NS
            and _binary_signature(path) == before):
        _BINARIES[key] = (before, digest)
    else:
        _BINARIES.pop(key, None)
    return (str(program), wsl_distro, digest)
