"""Read-only completeness check for the actual RuntimeSnapshot input set.

The caller supplies its original recorded Git function, so this helper does not
start hidden subprocesses. No server, product test, build, or benchmark runs here.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def complete_runtime_inventory(repo, expected_sha, git):
    repo = Path(repo).resolve()
    if git('rev-parse', 'HEAD').decode().strip() != expected_sha:
        raise RuntimeError('runtime inventory HEAD 不等於固定來源')
    if git('status', '--porcelain=v1', '--untracked-files=all'):
        raise RuntimeError('runtime inventory 僅接受乾淨固定來源')
    stage = git('ls-files', '--stage', '-z')
    tracked = {}
    for row in stage.split(b'\0'):
        if not row:
            continue
        header, rawpath = row.split(b'\t', 1)
        mode, oid, number = header.decode('ascii').split()
        if number != '0' or rawpath.decode('utf-8') in tracked:
            raise RuntimeError('runtime inventory index 不是唯一 stage0')
        tracked[rawpath.decode('utf-8')] = {'mode': mode, 'blob_oid': oid}
    module_path = repo / 'geometry-web/runtime_version.py'
    module_raw = module_path.read_bytes()
    tree = ast.parse(module_raw.decode('utf-8'))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'source_files')
    loops = [n for n in function.body if isinstance(n, ast.For)
             and isinstance(n.target, ast.Name) and n.target.id == 'directory']
    if len(loops) != 1:
        raise RuntimeError('source_files 宣告 root 的 AST 形狀改變')
    roots = ast.literal_eval(loops[0].iter)
    if not isinstance(roots, tuple) or not all(isinstance(x, str) for x in roots):
        raise RuntimeError('source_files roots 不是原字串 tuple')
    spec = importlib.util.spec_from_file_location('_recorded_runtime_inventory_' + sha256(str(repo).encode())[:16], module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected = {p for p in ('current_geometry.c', '公理層.md') if p in tracked}
    for relative in tracked:
        path = Path(relative)
        parts = path.parts
        if (parts and parts[0] in roots and path.suffix in module.SOURCE_SUFFIXES
                and not set(parts[1:-1]) & module.SOURCE_EXCLUDES):
            expected.add(relative)
        if relative.startswith('geometry-web/vendor/'):
            expected.add(relative)
        if path.parent.as_posix() == 'geometry-web' and path.suffix in ('.js', '.css'):
            expected.add(relative)
    routes = module.static_files(repo)
    for path in routes.values():
        relative = path.relative_to(repo).as_posix()
        if relative not in tracked:
            raise RuntimeError('正式靜態路由不是同 SHA 的 tracked input：' + relative)
        expected.add(relative)
    actual_paths = module.source_files(repo, routes)
    actual = {path.relative_to(repo).as_posix() for path in actual_paths}
    if len(actual_paths) != len(actual) or actual != expected:
        raise RuntimeError('RuntimeSnapshot 輸入集合不完整：' + repr({
            'missing': sorted(expected - actual), 'unexpected': sorted(actual - expected)}))
    rows, contents = [], []
    for path in actual_paths:
        relative = path.relative_to(repo).as_posix()
        body = path.read_bytes()
        identity = module._identity_content(repo, path, body)
        rows.append({'path': relative, **tracked[relative], 'bytes': len(body),
                     'raw_sha256': sha256(body), 'runtime_identity_sha256': sha256(identity)})
        contents.append((path, body))
    return {'schema': 'geometry-runtime-complete-input-inventory/1', 'source_sha': expected_sha,
            'root': str(repo), 'runtime_module_sha256': sha256(module_raw),
            'declared_roots': list(roots), 'tracked_index_sha256': sha256(stage),
            'source_set_complete': True, 'expected_count': len(expected), 'actual_count': len(actual),
            'source_version': module._content_version(repo, contents), 'inputs': rows,
            'policy': 'Actual original source_files/static_files and identity normalization; only outside-root evidence directories may be sparse.'}


def same_runtime_identity(left, right):
    return (left['source_sha'] == right['source_sha'] and left['source_set_complete'] and right['source_set_complete']
            and left['source_version'] == right['source_version']
            and [(r['path'], r['runtime_identity_sha256']) for r in left['inputs']]
            == [(r['path'], r['runtime_identity_sha256']) for r in right['inputs']])
