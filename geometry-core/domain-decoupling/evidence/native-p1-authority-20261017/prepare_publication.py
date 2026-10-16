#!/usr/bin/env python3
"""Copy historical evidence bytes; never execute retained runners or product code.

The approved selection is explicit: eleven source closeouts through 12422c69,
their same-prefix supporting records, and both f8c reload attempts. Source tar
archives are hashed and omitted. Repeated text is stored once by SHA-256.
"""
from collections import Counter
from datetime import datetime, timezone
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path
import subprocess
import tarfile

HEADS = ['72d6835c', 'a8831ca0', '808b8e69', '042dac48', 'f8c3e0f2',
         '5fe3bfd5', '4cb65713', '3e774212', '344935de', '4004a1cf', '12422c69']
PREDECESSORS = ['native-p1-20261016', 'native-p1-followup-20261016']
TEXT_SUFFIXES = {'.json', '.ps1', '.txt', '.sh', '.py', '.log', '.scene', '.raw'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def file_record(path):
    raw = path.read_bytes()
    return {'sha256': sha(raw), 'bytes': len(raw)}


def select(evidence):
    selected, omitted = {}, {}
    for child in sorted(evidence.iterdir()):
        if not any(head in child.name for head in HEADS):
            continue
        candidates = sorted(child.rglob('*')) if child.is_dir() else [child]
        for path in candidates:
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            relative = path.relative_to(evidence).as_posix()
            if path.is_symlink():
                raise ValueError('Symlink is outside the sealed selection: ' + relative)
            if path.name == 'selected-source.tar':
                omitted[relative] = {'sourcePath': str(path), **file_record(path),
                    'reason': 'Complete selected-source archive omitted to avoid duplicating source trees; exact original hash and size retained.'}
            else:
                if path.suffix not in TEXT_SUFFIXES:
                    raise ValueError('Unexpected evidence format: ' + relative)
                raw = path.read_bytes()
                try:
                    raw.decode('utf-8')
                except UnicodeDecodeError:
                    if not raw.startswith((b'\xff\xfe', b'\xfe\xff')):
                        raise ValueError('Non-text artifact: ' + relative)
                    raw.decode('utf-16')
                selected[relative] = path
    return selected, omitted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    evidence, repo, output = args.evidence.resolve(), args.repo.resolve(), args.out.resolve()
    if (output / 'CONTENT-MANIFEST.json').exists() or (output / 'raw-evidence.tar.xz').exists():
        raise ValueError('Refusing to replace a prepared publication')
    output.mkdir(parents=True, exist_ok=True)
    selected, omitted = select(evidence)
    assert len(selected) == 536 and len(omitted) == 22
    assert sum(p.stat().st_size for p in selected.values()) == 212962724
    predecessor_records, old_paths = {}, {}
    for name in PREDECESSORS:
        old = repo / 'geometry-core/domain-decoupling/evidence' / name
        package = json.loads((old / 'PACKAGE-SHA256.json').read_bytes())
        files = dict(package['files'])
        files['PACKAGE-SHA256.json'] = file_record(old / 'PACKAGE-SHA256.json')
        assert set(files) == {p.relative_to(old).as_posix() for p in old.rglob('*') if p.is_file()}
        for path, record in files.items():
            assert file_record(old / path) == {'sha256': record['sha256'], 'bytes': record['bytes']}, path
        predecessor_records[name] = {'files': files, 'fileCount': len(files)}
        prior = json.loads((old / 'CONTENT-MANIFEST.json').read_bytes())
        for path, record in prior['files'].items():
            old_paths[path] = {'pack': name, **record}
    assert not set(selected) & set(old_paths), 'Already published logical paths'

    records, blobs = {}, {}
    for relative, path in selected.items():
        raw = path.read_bytes()
        digest = sha(raw)
        record = {'sourcePath': str(path), 'sourceSha256': digest, 'sha256': digest,
                  'bytes': len(raw), 'archiveEntry': 'blobs/' + digest, 'targetSha256': digest}
        records[relative] = record
        blobs.setdefault(digest, raw)
        parts = Path(relative).parts
        readable = (len(parts) == 1 and (path.name.startswith('closeout-') and path.suffix == '.json' or path.name.startswith('readonly-')))
        readable = readable or (len(parts) == 3 and parts[1] == 'result' and path.name in
            {'summary.json', 'test-result.json', 'unittest.log', 'exit.txt', 'stdin.raw', 'stdout.raw', 'stderr.raw', 'input.scene', 'readback.scene'})
        if readable:
            target = output / 'readable' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            record['readableCopy'] = target.relative_to(output).as_posix()
            record['readableSha256'] = sha(target.read_bytes())
    assert len(blobs) == 435
    archive_path = output / 'raw-evidence.tar.xz'
    with lzma.open(archive_path, 'wb', preset=6) as compressed:
        with tarfile.open(fileobj=compressed, mode='w|') as archive:
            for digest, raw in sorted(blobs.items()):
                entry = tarfile.TarInfo('blobs/' + digest)
                entry.size, entry.mtime, entry.mode = len(raw), 0, 0o644
                archive.addfile(entry, io.BytesIO(raw))

    def data(relative):
        return json.loads(blobs[records[relative]['sha256']])

    completed, prepared, rows, source_records, runner_records = [], [], [], [], []
    commits = {}
    for head in HEADS:
        closeout_path = 'closeout-' + head + '.json'
        closeout = data(closeout_path)
        commit, tree = closeout['source'], closeout['tree']
        raw_commit = subprocess.check_output(['git', '-C', str(repo), 'cat-file', 'commit', commit])
        assert hashlib.sha1(b'commit ' + str(len(raw_commit)).encode() + b'\0' + raw_commit).hexdigest() == commit
        assert raw_commit.splitlines()[0] == ('tree ' + tree).encode()
        target = output / 'source-commits' / (commit + '.commit')
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(raw_commit)
        commits[commit] = {'tree': tree, 'file': target.relative_to(output).as_posix(), **file_record(target)}
        gate, focused = 'build-gate-' + head + '-v1', 'focused-' + head + '-v3'
        gate_summary = data(gate + '/result/summary.json')
        completed.append(gate)
        gate_status = 'PASS' if gate_summary['exit'] == 0 else 'FAIL'
        failed_stage = next((s['stage'] for s in gate_summary['stages'] if s['status'] != 'PASS'), None)
        result_path = focused + '/result/test-result.json'
        if result_path in records:
            result = data(result_path)
            outcomes = dict(Counter(result['outcomes'].values()))
            focused_summary = data(focused + '/result/summary.json')
            completed.append(focused)
            focused_status = 'PASS' if focused_summary['exit'] == 0 else 'FAIL'
            planned, ran, unrun = result['planned_tests'], result['tests_run'], result['unrun_count']
            failures, errors = result['failures'], result['errors']
        else:
            prepared.append(focused)
            focused_status = 'UNRUN'
            planned = data(focused + '/recipe.json')['expected_tests']
            ran, unrun, failures, errors, outcomes = 0, planned, 0, 0, {'UNRUN': planned}
        rows.append({'source': commit, 'tree': tree, 'closeout': closeout_path,
            'buildGate': gate, 'buildStatus': gate_status, 'failedStage': failed_stage,
            'focused': focused, 'focusedStatus': focused_status, 'plannedMethods': planned,
            'actualMethods': ran, 'outcomes': outcomes, 'unrunMethods': unrun,
            'failureEvents': failures, 'errors': errors})

    completed += ['diagnostic-f8c3e0f2-bridge-reload-v1', 'diagnostic-f8c3e0f2-bridge-reload-v2']
    for name in completed:
        summary = data(name + '/result/summary.json')
        before, after = name + '/result/source-before.json', name + '/result/source-after.json'
        assert data(before) == data(after), name
        source_records.append({'receipt': name, 'source': summary['source'], 'tree': summary['tree'],
            'before': before, 'after': after, 'beforeSha256': records[before]['sha256'],
            'afterSha256': records[after]['sha256'], 'sourceFiles': len(data(before)),
            'selectionScope': 'Exact selected source closure, not the whole repository'})
        original_before, original_after = summary['runner_sha256_before'], summary['runner_sha256_after']
        assert original_before == original_after, name
        for runner, digest in original_before.items():
            relative = name + '/' + runner
            assert records[relative]['sha256'] == digest, (relative, digest)
            runner_records.append({'receipt': name, 'field': 'runner_sha256_before/' + runner,
                'path': relative, 'expectedSha256': digest, 'retainedSha256': records[relative]['sha256']})
    assert len(completed) == 22 and len(prepared) == 2
    assert all(file_record(path) == {'sha256': records[name]['sha256'], 'bytes': records[name]['bytes']} for name, path in selected.items())
    assert all(file_record(Path(record['sourcePath'])) == {'sha256': record['sha256'], 'bytes': record['bytes']} for record in omitted.values())
    save(output / 'PREDECESSORS.json', {'schema': 'geometry-p1-immutable-predecessors/1', 'packages': predecessor_records,
        'logicalDuplicateCount': 0, 'unchanged': True})
    save(output / 'SOURCE-PROVENANCE.json', {'commits': commits, 'receipts': source_records,
        'note': 'Raw Git commit objects bind source/tree identities. Retained selected-path/source-before/source-after manifests bind source hashes. Complete selected-source tar files and compiled binaries are omitted; no source or product code is executed by packaging.'})
    save(output / 'RUNNER-PROVENANCE.json', {'claims': runner_records, 'missing': [],
        'externalLauncher': {'path': '/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_locked3.sh',
            'previouslyPublished': 'native-p1-20261016', 'catalogPath': 'runtime/wsl_locked3.sh',
            'sha256': old_paths['runtime/wsl_locked3.sh']['sha256'],
            'scope': 'Prior published wrapper bytes only; not a new execution-time hash attestation.'}})
    catalog = {'schema': 'geometry-p1-portable-evidence/1', 'capturedUtc': datetime.now(timezone.utc).isoformat(),
        'originalRoot': str(evidence), 'publicationBaseHead': subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip(),
        'scopeHeads': HEADS, 'completedReceipts': completed, 'preparedUnrunBundles': prepared, 'closeouts': rows,
        'files': records, 'omitted': omitted, 'rawFiles': len(records), 'rawBytes': sum(r['bytes'] for r in records.values()),
        'uniqueBlobs': len(blobs), 'uniqueBytes': sum(map(len, blobs.values())),
        'archive': {'file': archive_path.name, **file_record(archive_path)},
        'originalEvidenceUnchanged': True, 'fullAcceptanceClaimed': False, 'binariesIncluded': False,
        'sourceCheckoutsIncluded': False, 'newProductTestsExecutedByPackaging': False,
        'missingRunnerClaimCount': 0, 'predecessors': 'PREDECESSORS.json', 'appendOnly': True,
        'excludedActiveSource': '15187',
        'receiptMeaning': 'Historical original PASS/FAIL/UNRUN outcomes remain bound to their original source SHA. Packaging consistency does not certify current product acceptance.'}
    save(output / 'CONTENT-MANIFEST.json', catalog)
    print(json.dumps({key: value for key, value in catalog.items() if key not in ('files', 'omitted', 'closeouts')}, indent=2))


if __name__ == '__main__':
    main()
