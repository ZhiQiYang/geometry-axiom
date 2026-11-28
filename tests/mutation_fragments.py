"""Strict, append-only bridge mutation fragments; never execution receipts.

Existing inline definitions remain their exact historical list. New rows have
real native source anchors and fully qualified unittest judges. They cannot
declare equivalent/retired exemptions. File order is deterministic.
"""
from pathlib import Path, PurePosixPath
import json
import re

FIELDS = {'id', 'desc', 'binary', 'file', 'old', 'new', 'tests',
          'expected_assertion', 'reason'}
ID = re.compile(r'[A-Za-z][A-Za-z0-9_]*\Z')
METHOD = re.compile(r'tests\.test_[A-Za-z0-9_]+\.[A-Za-z][A-Za-z0-9_]*\.test_[A-Za-z0-9_]+\Z')


def _safe(root, path):
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('O467_SYMLINK: ' + relative.as_posix())


def fragment_paths(root, *, required=True):
    root = Path(root).resolve()
    directory = root / 'tests/mutants.d'
    _safe(root, directory)
    if not directory.is_dir():
        if not required and not directory.exists():
            return []
        raise ValueError('O467_DIRECTORY_REQUIRED: tests/mutants.d')
    result = []
    for path in sorted(directory.iterdir(), key=lambda value: value.name):
        _safe(root, path)
        if not path.is_file() or path.suffix != '.json':
            raise ValueError('O467_FRAGMENT_PATH: ' + path.name)
        result.append(path)
    return result


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('O467_DUPLICATE_JSON_KEY: ' + key)
        result[key] = value
    return result


def load_fragments(root, legacy=()):
    root = Path(root).resolve()
    seen = set()
    for item in legacy:
        identifier = item['id'].casefold()
        if identifier in seen:
            raise ValueError('O467_DUPLICATE_ID: ' + item['id'])
        seen.add(identifier)
    result = []
    for path in fragment_paths(root):
        row = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_object)
        if type(row) is not dict or set(row) != FIELDS:
            raise ValueError('O467_FRAGMENT_SHAPE: ' + path.name)
        if (any(type(row[key]) is not str or not row[key].strip()
                for key in FIELDS - {'tests'}) or not ID.fullmatch(row['id'])
                or row['binary'] != 'bridge' or row['old'] == row['new']):
            raise ValueError('O467_FRAGMENT_VALUES: ' + path.name)
        if path.name != row['id'] + '.json':
            raise ValueError('O467_FILENAME: ' + path.name)
        folded = row['id'].casefold()
        if folded in seen:
            raise ValueError('O467_DUPLICATE_ID: ' + row['id'])
        seen.add(folded)
        source = row['file']
        if ('\\' in source or ':' in source or PurePosixPath(source).is_absolute()
                or any(part in ('', '.', '..') for part in source.split('/'))
                or PurePosixPath(source).suffix not in ('.c', '.inc', '.h')):
            raise ValueError('O467_SOURCE_PATH: ' + source)
        target = root / source
        _safe(root, target)
        if not target.is_file():
            raise ValueError('O467_SOURCE_PATH: ' + source)
        methods = row['tests']
        if (type(methods) is not list or not methods
                or any(type(method) is not str or not METHOD.fullmatch(method) for method in methods)
                or len(methods) != len(set(methods))):
            raise ValueError('O467_JUDGE_METHODS: ' + row['id'])
        result.append(row)
    return result


def fragment_material(root):
    """Bind names and LF-normalized bytes, including metadata and whitespace.

    Legacy unit-fixture roots may have no fragment directory. Production
    imports call strict load_fragments first, so missing registries fail closed.
    """
    root = Path(root).resolve()
    return b''.join(b'\0' + path.relative_to(root).as_posix().encode('utf-8') + b'\0'
                    + path.read_bytes().replace(b'\r\n', b'\n')
                    for path in fragment_paths(root, required=False))
