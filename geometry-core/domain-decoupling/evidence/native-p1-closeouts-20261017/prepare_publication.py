#!/usr/bin/env python3
"""Package the frozen closed-receipt allowlist; never run retained product code.

This uses the preceding evidence package's SHA-256 blob archive schema. The
selection is the 370 closed files in catalog f3f79809, not a directory glob.
The separate 599 preparation section is deliberately never read or selected.
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

PLAN_SHA = 'f3f798090b191811eb2386226cbf7d6c1234df255e89ee865732f382191c4455'
HEADS = ['15187e71', '18edda3f', 'de62cd68', 'f22dcccc', 'fa5deb70']
PREDECESSORS = ['native-p1-20261016', 'native-p1-followup-20261016',
                'native-p1-authority-20261017']
DIAGNOSTICS = {'diagnostic-de62-parameter-v1': 'focused-de62cd68-authority230-v1',
               'diagnostic-f22-version-v1': 'focused-f22dcccc-parameters220-v1'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def file_record(path):
    raw = path.read_bytes()
    return {'sha256': sha(raw), 'bytes': len(raw)}


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    evidence, repo, output = args.evidence.resolve(), args.repo.resolve(), args.out.resolve()
    if (output / 'CONTENT-MANIFEST.json').exists() or (output / 'raw-evidence.tar.xz').exists():
        raise ValueError('Refusing to replace a prepared publication')
    assert output.parent == repo / 'geometry-core/domain-decoupling/evidence'
    assert output.name == 'native-p1-closeouts-20261017'
    output.mkdir(parents=True, exist_ok=True)
    raw_plan = args.plan.read_bytes()
    assert sha(raw_plan) == PLAN_SHA, 'Frozen selection catalog changed'
    plan = json.loads(raw_plan)
    assert plan['closedSourcePrefixes'] == HEADS
    selected, omitted = plan['files'], plan['omitted']
    assert len(selected) == 370 and len(omitted) == 10
    assert sum(r['bytes'] for r in selected.values()) == 99518011
    assert not any('599' in name for name in [*selected, *omitted])
    base_head = git(repo, 'rev-parse', 'HEAD').decode().strip()

    predecessor_records, old_paths = {}, {}
    for name in PREDECESSORS:
        old = repo / 'geometry-core/domain-decoupling/evidence' / name
        seal = json.loads((old / 'PACKAGE-SHA256.json').read_bytes())
        files = dict(seal['files'])
        files['PACKAGE-SHA256.json'] = file_record(old / 'PACKAGE-SHA256.json')
        assert set(files) == {p.relative_to(old).as_posix() for p in old.rglob('*') if p.is_file()}
        for path, record in files.items():
            assert file_record(old / path) == {'sha256': record['sha256'], 'bytes': record['bytes']}, path
        predecessor_records[name] = {'files': files, 'fileCount': len(files)}
        prior = json.loads((old / 'CONTENT-MANIFEST.json').read_bytes())
        assert file_record(old / 'CONTENT-MANIFEST.json')['sha256'] == plan['predecessors'][name]['catalogSha256']
        assert files['PACKAGE-SHA256.json']['sha256'] == plan['predecessors'][name]['sealSha256']
        for path, record in prior['files'].items():
            old_paths[path] = {'pack': name, **record}
    assert not set(selected) & set(old_paths), 'Already published logical paths'

    records, blobs = {}, {}
    for relative, planned in selected.items():
        path = evidence / relative
        assert path.resolve() == Path(planned['sourcePath']).resolve()
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes()
        digest = sha(raw)
        assert {'sha256': digest, 'bytes': len(raw)} == {k: planned[k] for k in ('sha256', 'bytes')}, relative
        records[relative] = {'sourcePath': str(path), 'sourceSha256': digest, 'sha256': digest,
            'bytes': len(raw), 'archiveEntry': 'blobs/' + digest, 'targetSha256': digest}
        blobs.setdefault(digest, raw)
        parts = Path(relative).parts
        readable = len(parts) == 1 and ((path.name.startswith('closeout-') and path.suffix == '.json') or path.name.startswith('readonly-'))
        readable = readable or (len(parts) >= 3 and parts[1] == 'result' and path.name in
            {'summary.json', 'test-result.json', 'unittest.log', 'exit.txt', 'cases.json',
             'stdin.raw', 'stdout.raw', 'stderr.raw', 'input.scene', 'readback.scene'})
        readable = readable or relative.startswith('fa5-version-output-analysis-v1/')
        readable = readable or (relative.startswith('watchdog-envelope-v1/') and
            (path.name == 'selftest-summary.json' or path.name.startswith('recovered-selftest-source-')))
        if readable:
            target = output / 'readable' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            records[relative].update(readableCopy=target.relative_to(output).as_posix(), readableSha256=sha(target.read_bytes()))
    assert len(blobs) == 295 and sum(map(len, blobs.values())) == 79097380

    def data(relative):
        return json.loads(blobs[records[relative]['sha256']])

    completed, rows, commits, tree_checks = [], [], {}, []
    source_archive_members = 0
    for planned_row in plan['closeouts']:
        closeout = data(planned_row['closeout'])
        commit, tree = closeout['source'], closeout['tree']
        assert (commit, tree) == (planned_row['source'], planned_row['tree'])
        raw_commit = git(repo, 'cat-file', 'commit', commit)
        assert hashlib.sha1(b'commit ' + str(len(raw_commit)).encode() + b'\0' + raw_commit).hexdigest() == commit
        assert raw_commit.splitlines()[0] == ('tree ' + tree).encode()
        target = output / 'source-commits' / (commit + '.commit')
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(raw_commit)
        commits[commit] = {'tree': tree, 'file': target.relative_to(output).as_posix(), **file_record(target)}

        command = ['git', 'ls-tree', '-r', '-l', '-z', commit]
        tree_paths = {}
        for entry in git(repo, *command[1:]).split(b'\0'):
            if not entry:
                continue
            info, raw_name = entry.split(b'\t', 1)
            mode, kind, blob, size = info.split()
            assert kind == b'blob', (commit, raw_name, kind)
            tree_paths[raw_name.decode('utf-8')] = {'git_mode': mode.decode(), 'git_blob': blob.decode(), 'bytes': int(size)}
        full_name = planned_row['focused'] + '/full-git-object-manifest.json'
        full = data(full_name)
        assert (full['source'], full['tree']) == (commit, tree)
        assert full['paths'] == tree_paths, full_name
        selected_checks = []
        for bundle in (planned_row['gate'], planned_row['focused']):
            full_bundle = data(bundle + '/full-git-object-manifest.json')
            assert full_bundle['paths'] == tree_paths
            manifest_name = bundle + '/selected-paths.json'
            manifest = data(manifest_name)
            assert (manifest['source'], manifest['tree']) == (commit, tree)
            for path, record in manifest['paths'].items():
                assert {k: record[k] for k in ('git_mode', 'git_blob', 'bytes')} == tree_paths[path], (bundle, path)
            omitted_name = bundle + '/selected-source.tar'
            archive_record = omitted[omitted_name]
            archive_path = evidence / omitted_name
            assert file_record(archive_path) == {k: archive_record[k] for k in ('sha256', 'bytes')}
            with tarfile.open(archive_path, 'r:') as archive:
                members = archive.getmembers()
                assert {m.name for m in members} == set(manifest['paths'])
                assert len(members) == len(manifest['paths'])
                for member in members:
                    assert member.isfile(), member.name
                    raw = archive.extractfile(member).read()
                    item = manifest['paths'][member.name]
                    assert len(raw) == item['bytes'] and sha(raw) == item['sha256']
                    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == item['git_blob']
                    source_archive_members += 1
            selected_checks.append({'manifest': manifest_name, 'sha256': records[manifest_name]['sha256'],
                'pathsChecked': len(manifest['paths']), 'omittedArchive': omitted_name,
                'sourceArchiveMemberBytesChecked': len(manifest['paths'])})
        tree_checks.append({'source': commit, 'tree': tree, 'command': command, 'manifest': full_name,
            'manifestSha256': records[full_name]['sha256'], 'pathsChecked': len(tree_paths),
            'allManifestEntriesEqualGitTree': True, 'selectedManifests': selected_checks})

        gate, focused = planned_row['gate'], planned_row['focused']
        gate_summary, summary = data(gate + '/result/summary.json'), data(focused + '/result/summary.json')
        result = data(focused + '/result/test-result.json')
        outcomes = dict(Counter(result['outcomes'].values()))
        assert outcomes == planned_row['outcomes']
        assert result == summary['test_result']
        assert gate_summary['exit'] == 0 and all(s['status'] == 'PASS' for s in gate_summary['stages'])
        row = {**planned_row, 'buildGate': gate, 'buildStatus': planned_row['gateStatus'], 'failedStage': None,
            'unrunMethods': result['unrun_count']}
        del row['gate']
        del row['gateStatus']
        assert row['actualMethods'] == result['tests_run'] and row['plannedMethods'] == result['planned_tests']
        assert row['failureEvents'] == result['failures'] and row['errors'] == result['errors']
        assert row['focusedStatus'] == ('PASS' if summary['exit'] == 0 else 'FAIL')
        rows.append(row)
        completed += [gate, focused]

    completed += list(DIAGNOSTICS)
    source_records, runner_records = [], []
    for name in completed:
        summary = data(name + '/result/summary.json')
        selected_bundle = DIAGNOSTICS.get(name, name)
        diagnostic = name in DIAGNOSTICS
        basename = 'original-source-' if diagnostic else 'source-'
        before, after = name + '/result/' + basename + 'before.json', name + '/result/' + basename + 'after.json'
        unchanged_field = 'original_source_unchanged' if diagnostic else 'source_unchanged'
        assert data(before) == data(after) and summary[unchanged_field] is True
        selected_map = data(selected_bundle + '/selected-paths.json')
        assert data(before) == {p: r['sha256'] for p, r in selected_map['paths'].items()}
        source_records.append({'receipt': name, 'source': summary['source'], 'tree': commits[summary['source']]['tree'],
            'before': before, 'after': after, 'beforeSha256': records[before]['sha256'],
            'afterSha256': records[after]['sha256'], 'sourceFiles': len(data(before)),
            'selectedBundle': selected_bundle, 'sourceUnchangedField': unchanged_field,
            'selectionScope': 'Exact selected source closure, not the whole repository'})
        assert summary['runner_sha256_before'] == summary['runner_sha256_after']
        for runner, digest in summary['runner_sha256_before'].items():
            relative = 'watchdog-envelope-v1/watchdog.py' if runner == 'watchdog.py' else name + '/' + runner
            if '/p1/' in runner.replace('\\', '/'):
                relative = runner.replace('\\', '/').split('/p1/', 1)[1]
            assert records[relative]['sha256'] == digest, (relative, digest)
            runner_records.append({'receipt': name, 'field': 'runner_sha256_before/' + runner,
                'path': relative, 'expectedSha256': digest, 'retainedSha256': records[relative]['sha256']})

    archive_path = output / 'raw-evidence.tar.xz'
    with lzma.open(archive_path, 'wb', preset=6) as compressed:
        with tarfile.open(fileobj=compressed, mode='w|') as archive:
            for digest, raw in sorted(blobs.items()):
                entry = tarfile.TarInfo('blobs/' + digest)
                entry.size, entry.mtime, entry.mode = len(raw), 0, 0o644
                archive.addfile(entry, io.BytesIO(raw))

    for name, record in records.items():
        assert file_record(evidence / name) == {k: record[k] for k in ('sha256', 'bytes')}, name
    for name, record in omitted.items():
        assert file_record(evidence / name) == {k: record[k] for k in ('sha256', 'bytes')}, name
    assert git(repo, 'rev-parse', 'HEAD').decode().strip() == base_head
    assert sha(args.plan.read_bytes()) == PLAN_SHA
    save(output / 'PREDECESSORS.json', {'schema': 'geometry-p1-immutable-predecessors/1',
        'packages': predecessor_records, 'logicalDuplicateCount': 0, 'unchanged': True})
    save(output / 'SOURCE-PROVENANCE.json', {'commits': commits, 'receipts': source_records,
        'gitTreeVerification': tree_checks, 'omittedSourceArchiveMembersByteChecked': source_archive_members,
        'note': 'Raw Git commits bind source/tree identities. Read-only Git trees matched all full-object manifests and selected path mode/blob/size records; omitted source archive member bytes matched each selected SHA-256 and Git blob SHA-1. No source or product code was executed by packaging.'})
    save(output / 'RUNNER-PROVENANCE.json', {'claims': runner_records, 'missing': [],
        'externalLauncher': {'path': '/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_locked3.sh',
            'previouslyPublished': 'native-p1-20261016', 'catalogPath': 'runtime/wsl_locked3.sh',
            'sha256': old_paths['runtime/wsl_locked3.sh']['sha256'],
            'scope': 'Prior published wrapper bytes only; not a new execution-time hash attestation.'},
        'limitations': ['fa5 build-gate launch.ps1 bytes are retained, but its runner manifest did not hash launch.ps1; no historical execution-start anchor is invented.',
            'Recovered first watchdog selftest bytes match its end-of-run disk hash only, not proof of execution-start loaded bytes.']})
    catalog = {'schema': 'geometry-p1-portable-evidence/1', 'capturedUtc': datetime.now(timezone.utc).isoformat(),
        'originalRoot': str(evidence), 'publicationBaseHead': base_head, 'selectionPlanSha256': PLAN_SHA,
        'scopeHeads': HEADS, 'completedReceipts': completed, 'preparedUnrunBundles': [], 'closeouts': rows,
        'files': records, 'omitted': omitted, 'rawFiles': len(records), 'rawBytes': sum(r['bytes'] for r in records.values()),
        'uniqueBlobs': len(blobs), 'uniqueBytes': sum(map(len, blobs.values())),
        'archive': {'file': archive_path.name, **file_record(archive_path)},
        'originalEvidenceUnchanged': True, 'fullAcceptanceClaimed': False, 'binariesIncluded': False,
        'sourceCheckoutsIncluded': False, 'newProductTestsExecutedByPackaging': False,
        'missingRunnerClaimCount': 0, 'predecessors': 'PREDECESSORS.json', 'appendOnly': True,
        'excludedActiveSource': '599 preparation and all later 599 execution results; publish separately after closure',
        'evidenceLimitations': {'publicationVerifiesConsistencyOnly': True, 'completeProvenanceClaimed': False,
            'recoveredSelftestSourceProvesStartLoadedBytes': False, 'watchdogPerMethodLogRetained': False,
            'fa5StdoutRecoverableFromReceipts': False, 'externalWrapperReferencesRemainPredecessor': True,
            'fa5BuildGateHistoricalLauncherAnchorRetained': False},
        'watchdogSelftests': plan['watchdogSelftests'], 'watchdogTestItems': plan['watchdogTestItems'],
        'receiptMeaning': 'Historical original PASS/FAIL/UNRUN outcomes remain bound to their original source SHA. Diagnostic wrapper exit 0 means capture completion only. Packaging consistency does not certify current product acceptance.'}
    save(output / 'CONTENT-MANIFEST.json', catalog)
    print(json.dumps({k: catalog[k] for k in ('scopeHeads', 'rawFiles', 'rawBytes', 'uniqueBlobs', 'uniqueBytes', 'archive')}, indent=2))
    print(json.dumps({'readableCopies': sum('readableCopy' in r for r in records.values()),
        'runnerClaims': len(runner_records), 'sourceReceipts': len(source_records),
        'sourceArchiveMembersChecked': source_archive_members, 'priorPackageFilesChecked': sum(p['fileCount'] for p in predecessor_records.values())}))


if __name__ == '__main__':
    main()
