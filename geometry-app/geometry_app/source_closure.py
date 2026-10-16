"""Ordered source inventory and immutable process-load identity for the host.

Consumers receive individual path/hash pairs and keep their own receipt formats.
This inventory never replaces a model's legacy source or geometry digest.
"""
from hashlib import sha256
from importlib.util import find_spec
from pathlib import Path
import re

from geometry_kernel import __file__ as kernel_file


_FACADE = None
_LOADED = None


def _hash(path, *, text):
    data = path.read_bytes()
    return sha256(data.replace(b"\r\n", b"\n") if text else data).hexdigest()


def source_paths(repository=None):
    """Return sorted (logical relative path, actual path) pairs, including data."""
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


def source_inventory(repository=None):
    return tuple((name, _hash(path, text=True)) for name, path in source_paths(repository))


def initialize(facade_directory):
    global _FACADE, _LOADED
    if _LOADED is None:
        _FACADE = Path(facade_directory).resolve()
        _LOADED = source_inventory()


def current_identity():
    current = source_inventory()
    return {"loaded": _LOADED, "current": current, "fresh": _LOADED is not None and _LOADED == current}


def binary_identity(program, *, wsl_distro=None):
    path = Path(program)
    if wsl_distro is not None:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", wsl_distro) or not str(program).startswith("/"):
            raise ValueError("Invalid WSL adapter identity")
        path = Path("//wsl.localhost") / wsl_distro / str(program).lstrip("/")
    return (str(program), wsl_distro, _hash(path, text=False))
