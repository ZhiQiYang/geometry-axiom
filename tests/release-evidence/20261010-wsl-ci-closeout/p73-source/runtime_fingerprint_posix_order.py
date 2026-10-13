"""Recompute geometry-web/runtime_version.py source_version(root) for a checked-out tree.

Why a wrapper: the WSL runs printed this value as `"version": "..."` (the geometry-runtime/1 probe).  runtime_version.source_files()
sorts Path objects, and WindowsPath sorts case-insensitively while the Linux runs sorted case-sensitively, so a plain call on Windows
gives a different digest.  This wrapper loads runtime_version.py FROM THE TREE UNDER TEST and re-sorts with case-sensitive parts.

usage:  python -I runtime_fingerprint_posix_order.py <checkout dir>
        (checkout with: git -c core.autocrlf=false -c core.eol=lf checkout --detach <sha>)
expected:  6615db613a75fbad43116d85251782b5083479df -> 290ebaee1760b3983e98fc4da27bc9154d3a151e2723e24265c4c129aaa2f070
           798d838741d545f029f68dba69679f83d9cebc27 -> f7ba23a02f82b85f5d66b39e7e1a3ed966ebf793e08fea2b41e7ee3f66d59548
"""
import importlib.util, pathlib, sys
root = pathlib.Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location('rv_under_test', root / 'geometry-web' / 'runtime_version.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
files = sorted(m.source_files(root), key=lambda p: p.parts)
print(m._content_version(root, ((p, p.read_bytes()) for p in files)))
