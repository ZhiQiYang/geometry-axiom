"""Freeze completed PF3 original evidence without running Git or products."""
from __future__ import annotations

import ast
import datetime
import hashlib
import json
from pathlib import Path
import stat
import tarfile

BASE = Path(__file__).resolve().parent
REPO = Path('/tmp/g261-next323')
RAW = Path('/tmp/g261-next323-pf3-full-01')
OUTER = Path('/workspace/geo323-work/pf3-full-01')
PRODUCT = 'e9fffc1cb036b6e4538a23f4dd12a9e10c5136f9'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def cases_from_original_tool(path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    names = {}
    cases = None
    for statement in tree.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id in ('HOST', 'REFERENCE', 'SOURCE'):
            names[target.id] = ast.literal_eval(statement.value)
        if target.id == 'CASES':
            cases = statement.value
    class Constants(ast.NodeTransformer):
        def visit_Name(self, node):
            require(node.id in names, 'Unknown original CASES constant: ' + node.id)
            return ast.copy_location(ast.Constant(names[node.id]), node)
    require(cases is not None, 'Original CASES missing')
    return ast.literal_eval(Constants().visit(cases))


def main():
    # Read only small terminal records first. Pending and failed executions are
    # never relabeled green or replaced by this archival preparation.
    receipt_path = OUTER / 'receipt.json'
    summary_path = RAW / 'summary.json'
    receipt = json.loads(receipt_path.read_text())
    if receipt.get('actual_process_returncode') is None or not summary_path.exists():
        print(json.dumps({'status': 'pending', 'frozen': False,
                          'original_outer_exit': receipt.get('actual_process_returncode')}))
        return 2
    summary = json.loads(summary_path.read_text())
    if receipt['actual_process_returncode'] != 0:
        failure = BASE / 'FAILURE_METADATA.json'
        if not failure.exists():
            write(failure, {'status': 'original execution failed; no successful archive frozen',
                            'original_outer_exit': receipt['actual_process_returncode'],
                            'receipt': str(receipt_path), 'receipt_sha256': sha(receipt_path),
                            'summary': str(summary_path), 'summary_sha256': sha(summary_path)})
        print(json.dumps({'status': 'original failure preserved', 'metadata': str(failure)}))
        return 1
    require(receipt['sha'] == PRODUCT and receipt['head_after'] == PRODUCT, 'PF3 source SHA mismatch')
    require(receipt['status_before'] == receipt['status_after'] == '', 'Original source was not clean')
    empty = hashlib.sha256(b'').hexdigest()
    require(receipt['patch_sha256'] == receipt['patch_after_sha256'] == empty, 'Original patch not empty')
    require(receipt['command'][-4:] == ['--out', str(RAW), '--jobs', '1'], 'Original complete jobs=1 command mismatch')
    require(isinstance(summary, dict) and summary.get('originalSourcesUnchanged') is True,
            'Original complete summary missing unchanged verdict')
    sources = json.loads((RAW / 'sources.json').read_text())
    # Read the original input copy from this run, not a later working-tree head.
    original_root = RAW / 'baseline/source'
    tool = original_root / 'tests/pf3_mutation_check.py'
    require(sha(tool) == sources['tests/pf3_mutation_check.py'], 'Tool differs from original source receipt')
    cases = cases_from_original_tool(tool)
    require(len(cases) == 19 and len(summary['mutations']) == 19, 'Original nineteen cases required')
    names = [case[0] for case in cases]
    require([row['id'] for row in summary['mutations']] == names, 'Original case order differs')
    for label in ('baseline', 'restored'):
        row = summary[label]
        require(row['id'] == label and row['verdict'] == 'pass' and row['exit'] == 0 and
                row['counts'] == {'run': 20, 'failures': 0, 'errors': 0, 'skipped': 0},
                label + ' original 20-test baseline/restore missing')
    require(all(row['verdict'] == 'killed' and row['exit'] == 1 and
                row['counts'] == {'run': 1, 'failures': 1, 'errors': 0, 'skipped': 0}
                for row in summary['mutations']), 'Original negative verdict/count mismatch')
    frozen = BASE / 'frozen'
    require(not frozen.exists(), 'Refusing to overwrite a frozen archive')
    frozen.mkdir()
    generated = frozen / 'metadata'
    generated.mkdir()
    selected = []
    excluded = []
    omitted = []
    aliases = set()
    def add(alias, path):
        require(not path.is_symlink() and stat.S_ISREG(path.stat().st_mode), 'Only regular original files: ' + str(path))
        require(alias not in aliases and not Path(alias).is_absolute() and '..' not in Path(alias).parts,
                'Duplicate or unsafe archive path: ' + alias)
        aliases.add(alias)
        selected.append({'path': alias, 'origin': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)})
    def tree(alias, path):
        for item in sorted(path.rglob('*')):
            if item.is_file():
                add(str(Path(alias) / item.relative_to(path)), item)
    add('pf3/sources.json', RAW / 'sources.json')
    add('pf3/summary.json', summary_path)
    originals = {}
    for relative in sorted({change[0] for case in cases for change in case[1]}):
        path = original_root / relative
        body = path.read_bytes()
        require(hashlib.sha256(body).hexdigest() == sources[relative], 'Original P source differs: ' + relative)
        originals[relative] = body
        add('original-targets/' + relative, path)
    bindings = []
    complete = [('baseline', [], 'all', ''), *cases, ('restored', [], 'all', '')]
    for name, changes, selection, marker in complete:
        directory = RAW / name
        build = json.loads((directory / 'build/execution.json').read_text())
        tests = json.loads((directory / 'tests/execution.json').read_text())
        result = json.loads((directory / 'result.json').read_text())
        require(build['exit'] == 0 and tests['exit'] == (0 if name in ('baseline', 'restored') else 1),
                'Original build/test exit mismatch: ' + name)
        if marker:
            require(marker in (directory / 'tests/stderr').read_text(), 'Original required marker absent: ' + name)
        tree('pf3/' + name + '/build', directory / 'build')
        tree('pf3/' + name + '/tests', directory / 'tests')
        add('pf3/' + name + '/result.json', directory / 'result.json')
        binary_root = directory / 'binaries'
        for path in sorted(binary_root.rglob('*')):
            if not path.is_file():
                continue
            alias = str(Path('pf3') / name / 'binaries' / path.relative_to(binary_root))
            with path.open('rb') as stream:
                body_magic = stream.read(4)
            binary = body_magic == b'\x7fELF' or path.suffix.lower() in ('.o', '.obj', '.exe', '.so', '.a', '.dll')
            actual_hash = sha(path)
            if path.parent == binary_root and path.name in result['artifacts']:
                require(actual_hash == result['artifacts'][path.name], 'Original artifact hash changed: ' + str(path))
            if binary:
                excluded.append({'path': str(path), 'archive_alias_if_included': alias,
                                 'bytes': path.stat().st_size, 'sha256': actual_hash,
                                 'reason': 'rebuildable executable or object; original fingerprints and execution logs included'})
            else:
                add(alias, path)
        by_path = {}
        for relative, before, after in changes:
            expected = by_path.get(relative, originals[relative])
            require(expected.count(before.encode()) == 1, 'Original mutation anchor mismatch: ' + name)
            by_path[relative] = expected.replace(before.encode(), after.encode())
        for relative, expected in by_path.items():
            path = directory / 'source' / relative
            actual = path.read_bytes()
            require(actual == expected, 'Actual mutated source differs from original changes: ' + str(path))
            add('mutated-sources/' + name + '/' + relative, path)
            bindings.append({'case': name, 'selection': selection, 'requiredMarker': marker,
                             'relative_path': relative, 'product_sha': PRODUCT,
                             'original_sha256': sources[relative], 'mutated_sha256': hashlib.sha256(actual).hexdigest(),
                             'mutated_bytes': len(actual), 'actual_matches_original_tool_changes': True})
        omitted.append({'path': str(directory / 'source'), 'reason': 'rebuildable source copy from public P + original sources.json',
                        'recursive_content_read': False, 'explicit_mutated_targets_preserved': sorted(by_path)})
    tree('outer', OUTER)
    for name in ('run_recorded.py', 'test_entry.py'):
        add('tools/' + name, Path('/workspace/geo323-work') / name)
    add('tools/reap_children.py', Path('/workspace/geo261-environment/reap_children.py'))
    for relative in sorted(key for key in sources if key.startswith('tests/') and
                           (key.endswith('.py') or key == 'tests/pf3_algorithm.c')):
        path = original_root / relative
        require(sha(path) == sources[relative], 'Original judge input differs: ' + relative)
        add('original-tool-inputs/' + relative, path)
    write(generated / 'MUTATED_SOURCE_BINDINGS.json', bindings)
    write(generated / 'EXCLUDED_BINARY_INVENTORY.json', excluded)
    write(generated / 'OMITTED_SOURCE_TREES.json', omitted)
    write(generated / 'SCOPE.json', {
        'schema': 'geo323-PF3-original-complete-evidence/1', 'product_sha': PRODUCT,
        'original_outer_exit': receipt['actual_process_returncode'],
        'baseline_tests': 20, 'mutations': 19, 'killed': 19, 'restored_tests': 20,
        'source_inputs': len(sources), 'originalSourcesUnchanged': True,
        'prepared_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'Archives only the original completed full PF3 run; no Git/product/test/publisher executed here.',
        'binary_and_source_exclusions_are_not_new_executions': True,
        'tool_roles': {
            'pf3_mutation_check.py': 'original run input copied before mutation; hash matches sources.json',
            'run_recorded.py': 'original outer recorder path',
            'reap_children.py': 'original outer reaper path',
            'test_entry.py': 'shared diagnostic helper retained as reference; not present in the PF3 command',
        },
    })
    for path in sorted(generated.iterdir()):
        add('metadata/' + path.name, path)
    write(frozen / 'SELECTION.json', selected)
    archive = frozen / 'pf3-full-original.raw.tar.gz'
    with tarfile.open(archive, 'x:gz', compresslevel=6, format=tarfile.PAX_FORMAT) as tar:
        for row in selected:
            require(sha(Path(row['origin'])) == row['sha256'], 'Original changed during archival preparation')
            tar.add(row['origin'], arcname=row['path'], recursive=False)
    require(archive.stat().st_size < 90_000_000, 'Split archival evidence; do not truncate raw')
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        require(len(members) == len(selected), 'Archive member count mismatch')
        for member, row in zip(members, selected):
            body = tar.extractfile(member).read()
            require(member.isfile() and member.name == row['path'] and len(body) == row['bytes'] and
                    hashlib.sha256(body).hexdigest() == row['sha256'], 'Archive member byte/hash mismatch')
    inventory = {'archive': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha(archive),
                 'members': [{key: row[key] for key in ('path', 'bytes', 'sha256')} for row in selected]}
    write(frozen / 'pf3-full-original.inventory.json', inventory)
    (frozen / 'SHA256SUMS').write_text(''.join(sha(path) + '  ' + path.relative_to(frozen).as_posix() + '\n'
        for path in sorted(frozen.rglob('*')) if path.is_file() and path.name != 'SHA256SUMS'), encoding='utf-8')
    print(json.dumps({'status': 'frozen original completed evidence', 'archive': str(archive),
                      'archive_bytes': archive.stat().st_size, 'archive_sha256': inventory['sha256'],
                      'members': len(selected), 'mutated_source_files': len(bindings),
                      'excluded_binaries_or_objects': len(excluded)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
