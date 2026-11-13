#!/usr/bin/env python3
"""Validate historical evidence without executing any retained code or commands."""
from collections import Counter
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=unique)


def safe(root, relative):
    path = PurePosixPath(relative)
    require(not path.is_absolute() and all(part not in ('', '.', '..') for part in path.parts), 'Unsafe package path: ' + relative)
    target = root.joinpath(*path.parts)
    require(target.resolve().is_relative_to(root.resolve()), 'Escaping package path: ' + relative)
    require(not target.is_symlink(), 'Unexpected symlink: ' + relative)
    return target


def verify(root, originals=None, predecessors=False, unsealed=False):
    catalog = load(root / 'CONTENT-MANIFEST.json')
    require(catalog['rawFiles'] == 536 and catalog['uniqueBlobs'] == 435, 'Unexpected approved file count')
    require(catalog['rawBytes'] == 212962724 and len(catalog['omitted']) == 22, 'Unexpected approved byte/omission count')
    require(not catalog['binariesIncluded'] and not catalog['sourceCheckoutsIncluded'], 'Unexpected source/binary claim')
    require(not catalog['fullAcceptanceClaimed'] and not catalog['newProductTestsExecutedByPackaging'], 'Unexpected acceptance/execution claim')
    records = catalog['files']
    require(len(records) == catalog['rawFiles'], 'Raw file count mismatch')
    archive_info = catalog['archive']
    archive_path = safe(root, archive_info['file'])
    archive_raw = archive_path.read_bytes()
    require(len(archive_raw) == archive_info['bytes'] and sha(archive_raw) == archive_info['sha256'], 'Archive fingerprint mismatch')
    expected = {}
    for relative, record in records.items():
        safe(root, relative)
        digest = record['sha256']
        require(digest == record['sourceSha256'] == record['targetSha256'], 'Source/target hash disagreement: ' + relative)
        require(record['archiveEntry'] == 'blobs/' + digest, 'Blob mapping disagreement: ' + relative)
        require(record['sourcePath'].replace('\\', '/').endswith('/' + relative), 'Original path mapping disagreement: ' + relative)
        expected[record['archiveEntry']] = {'sha256': digest, 'bytes': record['bytes']}
    require(len(expected) == catalog['uniqueBlobs'], 'Unique blob count mismatch')
    blobs = {}
    with tarfile.open(archive_path, 'r:xz') as archive:
        for member in archive:
            require(member.isfile() and member.name in expected and member.name not in blobs, 'Unexpected/duplicate archive member: ' + member.name)
            require(member.size == expected[member.name]['bytes'], 'Archive member size mismatch: ' + member.name)
            stream = archive.extractfile(member)
            require(stream is not None, 'Missing archive bytes: ' + member.name)
            raw = stream.read(member.size + 1)
            require(len(raw) == member.size and sha(raw) == expected[member.name]['sha256'], 'Archive member bytes mismatch: ' + member.name)
            blobs[member.name] = raw
    require(set(blobs) == set(expected), 'Missing archive members')
    require(sum(len(raw) for raw in blobs.values()) == catalog['uniqueBytes'], 'Unique byte count mismatch')

    def raw(relative):
        return blobs[records[relative]['archiveEntry']]

    def data(relative):
        return json.loads(raw(relative))

    readable_count = 0
    for relative, record in records.items():
        content = raw(relative)
        require(len(content) == record['bytes'] and sha(content) == record['sha256'], 'Raw mapping mismatch: ' + relative)
        if 'readableCopy' in record:
            copy = safe(root, record['readableCopy']).read_bytes()
            require(copy == content and sha(copy) == record['readableSha256'], 'Readable copy differs: ' + relative)
            readable_count += 1
        if originals is not None:
            source = safe(originals, relative).read_bytes()
            require(source == content, 'Original bytes changed: ' + relative)
    require(sum(record['bytes'] for record in records.values()) == catalog['rawBytes'], 'Logical byte count mismatch')
    for relative, record in catalog['omitted'].items():
        require(relative.endswith('/selected-source.tar'), 'Unexpected omission: ' + relative)
        if originals is not None:
            source = safe(originals, relative).read_bytes()
            require(len(source) == record['bytes'] and sha(source) == record['sha256'], 'Omitted archive changed: ' + relative)

    sources = load(root / 'SOURCE-PROVENANCE.json')
    for commit, record in sources['commits'].items():
        commit_raw = safe(root, record['file']).read_bytes()
        require(sha(commit_raw) == record['sha256'] and len(commit_raw) == record['bytes'], 'Commit bytes mismatch')
        require(hashlib.sha1(b'commit ' + str(len(commit_raw)).encode() + b'\0' + commit_raw).hexdigest() == commit, 'Commit object ID mismatch')
        require(commit_raw.splitlines()[0] == ('tree ' + record['tree']).encode(), 'Commit tree mismatch')
    require(len(sources['commits']) == 11, 'Unexpected source commit count')
    require({r['receipt'] for r in sources['receipts']} == set(catalog['completedReceipts']), 'Receipt source coverage mismatch')
    runner_claims = []
    source_file_checks = 0
    for record in sources['receipts']:
        name = record['receipt']
        summary = data(name + '/result/summary.json')
        require(summary['source'] == record['source'] and summary['tree'] == record['tree'], 'Receipt source identity mismatch: ' + name)
        require(record['source'] in sources['commits'] and sources['commits'][record['source']]['tree'] == record['tree'], 'Receipt commit identity mismatch: ' + name)
        before, after = data(record['before']), data(record['after'])
        require(before == after and len(before) == record['sourceFiles'], 'Source closure changed: ' + name)
        require(sha(raw(record['before'])) == record['beforeSha256'] and sha(raw(record['after'])) == record['afterSha256'], 'Source manifest fingerprint mismatch')
        selection_name = 'focused-f8c3e0f2-v3' if name.startswith('diagnostic-') else name
        selected = data(selection_name + '/selected-paths.json')
        require(selected['source'] == record['source'] and selected['tree'] == record['tree'], 'Selected source identity mismatch')
        require(before == {path: item['sha256'] for path, item in selected['paths'].items()}, 'Selected source hashes differ: ' + name)
        source_file_checks += len(before)
        require(summary['source_unchanged'] is True, 'Original source integrity failed: ' + name)
        require(summary['runner_sha256_before'] == summary['runner_sha256_after'], 'Original runner changed: ' + name)
        for runner, digest in summary['runner_sha256_before'].items():
            relative = name + '/' + runner
            require(sha(raw(relative)) == digest, 'Runner digest mismatch: ' + relative)
            runner_claims.append({'receipt': name, 'field': 'runner_sha256_before/' + runner, 'path': relative,
                'expectedSha256': digest, 'retainedSha256': digest})
        if name.startswith('focused-'):
            gate = 'build-gate-' + name.split('-')[1] + '-v1/result/summary.json'
            require(summary['gate_receipt_sha256_before'] == summary['gate_receipt_sha256_after'] == sha(raw(gate)), 'Build gate receipt changed: ' + name)
    runner_provenance = load(root / 'RUNNER-PROVENANCE.json')
    require(runner_claims == runner_provenance['claims'] and not runner_provenance['missing'], 'Runner provenance mismatch')

    for row in catalog['closeouts']:
        closeout = data(row['closeout'])
        require(closeout['source'] == row['source'] and closeout['tree'] == row['tree'], 'Closeout identity mismatch')
        gate = data(row['buildGate'] + '/result/summary.json')
        require(('PASS' if gate['exit'] == 0 else 'FAIL') == row['buildStatus'], 'Build result mismatch')
        require(next((s['stage'] for s in gate['stages'] if s['status'] != 'PASS'), None) == row['failedStage'], 'Failed stage mismatch')
        focused = row['focused']
        if row['focusedStatus'] == 'UNRUN':
            require(focused in catalog['preparedUnrunBundles'] and focused + '/result/summary.json' not in records, 'Prepared bundle incorrectly treated as executed')
            require(row['actualMethods'] == 0 and row['unrunMethods'] == row['plannedMethods'] == data(focused + '/recipe.json')['expected_tests'], 'UNRUN count mismatch')
        else:
            result = data(focused + '/result/test-result.json')
            summary = data(focused + '/result/summary.json')
            require(summary['test_result'] == result, 'Focused summary/result mismatch')
            require(row['focusedStatus'] == ('PASS' if summary['exit'] == 0 else 'FAIL'), 'Focused status mismatch')
            require(row['outcomes'] == dict(Counter(result['outcomes'].values())), 'Focused method outcome mismatch')
            require(row['plannedMethods'] == result['planned_tests'] == len(result['outcomes']), 'Planned method count mismatch')
            require(row['actualMethods'] == result['tests_run'] and row['unrunMethods'] == result['unrun_count'], 'Actual/UNRUN method count mismatch')
            require(row['failureEvents'] == result['failures'] and row['errors'] == result['errors'], 'Failure/error event count mismatch')

    reference_checks = 0
    def check_references(value):
        nonlocal reference_checks
        if isinstance(value, dict):
            for path_key, hash_keys in [('receipt', ['sha256', 'receipt_sha256']), ('gate_receipt', ['gate_receipt_sha256']),
                    ('focused_receipt', ['focused_receipt_sha256']), ('path', ['sha256']), ('excerpts', ['sha256', 'excerpts_sha256'])]:
                path = value.get(path_key)
                if not isinstance(path, str):
                    continue
                normalized = path.replace('\\', '/')
                relative = normalized.split('/p1/', 1)[-1] if '/p1/' in normalized else normalized
                if relative not in records:
                    continue
                for key in hash_keys:
                    if key in value:
                        require(value[key] == records[relative]['sha256'], 'Closeout reference hash mismatch: ' + relative)
                        reference_checks += 1
            for item in value.values():
                check_references(item)
        elif isinstance(value, list):
            for item in value:
                check_references(item)
    for head in catalog['scopeHeads']:
        check_references(data('closeout-' + head + '.json'))

    for version in ('v1', 'v2'):
        name = 'diagnostic-f8c3e0f2-bridge-reload-' + version
        summary = data(name + '/result/summary.json')
        require(summary['compiler_executed'] is False and summary['focused_test_methods_run'] == 0, 'Diagnostic scope mismatch')
        require(summary['bridge_sha256_before'] == summary['bridge_sha256_after'], 'Diagnostic binary hash changed')
        for filename, record in summary['raw_files'].items():
            captured = raw(name + '/result/' + filename)
            require(len(captured) == record['bytes'] and sha(captured) == record['sha256'], 'Diagnostic capture mismatch')
        require(summary['input_scene_sha256_before'] == summary['input_scene_sha256_after'] == sha(raw(name + '/result/input.scene')), 'Diagnostic scene changed')
        require(summary['readback_scene_sha256'] == sha(raw(name + '/result/readback.scene')), 'Diagnostic readback mismatch')
        require(summary['prior_receipt_sha256_before'] == summary['prior_receipt_sha256_after'], 'Diagnostic changed prior receipt')
        for path, digest in summary['prior_receipt_sha256_before'].items():
            relative = path.split('/p1/', 1)[1]
            require(sha(raw(relative)) == digest, 'Diagnostic prior receipt hash mismatch')
        responses = [json.loads(line) for line in raw(name + '/result/stdout.raw').decode('utf-8').splitlines() if line]
        require(responses == summary['responses'], 'Diagnostic summary/raw responses differ')
        if version == 'v1':
            require(summary['commands'][1].startswith('load ') and responses[1] == {'ok': False, 'error': '不認得的橋接指令'}, 'Invalid first diagnostic classification lost')
        else:
            require(summary['commands'][1].startswith('loadfile ') and summary['product_reload_ok'] is False, 'Actual reload failure classification lost')
            require(summary['responses'][1]['code'] == 'SCENE_INVALID' and summary['responses'][1]['error'] == 'line 25: I42: invalid owned record', 'Actual reload error mismatch')

    predecessor_data = load(root / 'PREDECESSORS.json')
    predecessor_files = 0
    if predecessors:
        for name, info in predecessor_data['packages'].items():
            folder = root.parent / name
            require({p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()} == set(info['files']), 'Predecessor file set changed')
            for path, record in info['files'].items():
                original = safe(folder, path).read_bytes()
                require(sha(original) == record['sha256'] and len(original) == record['bytes'], 'Predecessor changed: ' + name + '/' + path)
                predecessor_files += 1
            prior = load(folder / 'CONTENT-MANIFEST.json')
            require(not set(prior['files']) & set(records), 'Duplicated prior logical path')

    sealed_files = 0
    if not unsealed:
        package = load(root / 'PACKAGE-SHA256.json')
        actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
        require(actual == set(package['files']) | {'PACKAGE-SHA256.json'}, 'Package file set mismatch')
        for path, record in package['files'].items():
            content = safe(root, path).read_bytes()
            require(sha(content) == record['sha256'] and len(content) == record['bytes'], 'Sealed package file changed: ' + path)
            sealed_files += 1
    return {'schema': 'geometry-p1-authority-publication-verification/1', 'checkedUtc': datetime.now(timezone.utc).isoformat(),
        'ok': True, 'rawFilesVerified': len(records), 'uniqueBlobsVerified': len(blobs),
        'readableCopiesVerified': readable_count, 'originalFilesByteCompared': len(records) if originals else 0,
        'omittedSourceArchivesHashCompared': len(catalog['omitted']) if originals else 0,
        'sourceCommitsVerified': len(sources['commits']), 'sourceManifestFileHashesChecked': source_file_checks,
        'runnerClaimsVerified': len(runner_claims), 'closeoutReferenceHashesVerified': reference_checks,
        'completedHistoricalReceipts': len(catalog['completedReceipts']), 'preparedUnrunBundles': len(catalog['preparedUnrunBundles']),
        'predecessorFilesVerified': predecessor_files, 'packageFilesVerified': sealed_files,
        'packageSealChecked': not unsealed, 'productTestsExecuted': False, 'compilerExecuted': False,
        'wslExecuted': False, 'historicalFailuresRemainFailures': True, 'currentProductAcceptanceClaimed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', nargs='?', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--originals', type=Path, help='Optional original P1 directory for exact byte comparison')
    parser.add_argument('--predecessors', action='store_true', help='Verify unchanged sibling predecessor packs')
    parser.add_argument('--unsealed', action='store_true', help='Packaging-only check before PACKAGE-SHA256.json is created')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    root = args.package.resolve()
    if args.report:
        require(not args.report.exists(), 'Refusing to overwrite an existing report')
        require(not (root / 'PACKAGE-SHA256.json').exists() or not args.report.resolve().is_relative_to(root), 'Write final verification reports outside the sealed package')
    report = verify(root, args.originals.resolve() if args.originals else None, args.predecessors, args.unsealed)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
