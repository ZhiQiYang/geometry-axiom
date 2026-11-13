#!/usr/bin/env python3
"""Validate historical evidence without executing any retained code or commands."""
from collections import Counter
from datetime import datetime, timezone
import argparse
import ast
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
    require(catalog['rawFiles'] == 370 and catalog['uniqueBlobs'] == 295, 'Unexpected approved file count')
    require(catalog['rawBytes'] == 99518011 and catalog['uniqueBytes'] == 79097380 and len(catalog['omitted']) == 10, 'Unexpected approved byte/omission count')
    require(not catalog['binariesIncluded'] and not catalog['sourceCheckoutsIncluded'], 'Unexpected source/binary claim')
    require(not catalog['fullAcceptanceClaimed'] and not catalog['newProductTestsExecutedByPackaging'], 'Unexpected acceptance/execution claim')
    expected_outcomes = {
        '15187e71': {'failed': 4, 'UNRUN': 57},
        '18edda3f': {'passed': 61},
        'de62cd68': {'passed': 37, 'failed': 4, 'UNRUN': 189},
        'f22dcccc': {'passed': 52, 'failed': 2, 'UNRUN': 166},
        'fa5deb70': {'passed': 17, 'failed': 2, 'UNRUN': 257},
    }
    diagnostics = {
        'diagnostic-de62-parameter-v1': ('focused-de62cd68-authority230-v1', ['graph', 'prefix', 'depth']),
        'diagnostic-f22-version-v1': ('focused-f22dcccc-parameters220-v1', ['product']),
    }
    require(set(catalog['scopeHeads']) == set(expected_outcomes) and len(catalog['scopeHeads']) == 5, 'Unexpected closeout scope')
    require(catalog['preparedUnrunBundles'] == [], 'Preparation-only bundles must not be published')
    limitations = catalog['evidenceLimitations']
    for field, expected_value in {
            'publicationVerifiesConsistencyOnly': True, 'completeProvenanceClaimed': False,
            'recoveredSelftestSourceProvesStartLoadedBytes': False, 'watchdogPerMethodLogRetained': False,
            'fa5StdoutRecoverableFromReceipts': False, 'externalWrapperReferencesRemainPredecessor': True,
            'fa5BuildGateHistoricalLauncherAnchorRetained': False}.items():
        require(limitations.get(field) is expected_value, 'Evidence limitation lost: ' + field)
    records = catalog['files']
    require(not any('599f3414' in path for path in list(records) + list(catalog['omitted'])), 'Preparation-only target599 included')
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

    def receipt_relative(path):
        normalized = path.replace('\\', '/')
        return normalized.split('/p1/', 1)[-1] if '/p1/' in normalized else normalized

    def check_retained_hash(path, digest):
        relative = receipt_relative(path)
        retained = records.get(relative, catalog['omitted'].get(relative))
        require(retained is not None and retained['sha256'] == digest, 'Retained reference hash mismatch: ' + relative)

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
    require(len(sources['commits']) == 5 and {commit[:8] for commit in sources['commits']} == set(expected_outcomes), 'Unexpected source commit count/scope')
    require(len(catalog['closeouts']) == 5 and {row['source'] for row in catalog['closeouts']} == set(sources['commits']), 'Closeout source coverage mismatch')
    expected_receipts = set(diagnostics) | {row[key] for row in catalog['closeouts'] for key in ('buildGate', 'focused')}
    require(len(expected_receipts) == len(sources['receipts']) == len(catalog['completedReceipts']) == 12, 'Unexpected completed receipt count')
    require({r['receipt'] for r in sources['receipts']} == set(catalog['completedReceipts']) == expected_receipts, 'Receipt source coverage mismatch')
    runner_claims = []
    source_file_checks = 0
    for record in sources['receipts']:
        name = record['receipt']
        summary = data(name + '/result/summary.json')
        require(summary['source'] == record['source'], 'Receipt source identity mismatch: ' + name)
        require(name in diagnostics or 'tree' in summary, 'Missing normal receipt tree: ' + name)
        require('tree' not in summary or summary['tree'] == record['tree'], 'Receipt tree identity mismatch: ' + name)
        require(record['source'] in sources['commits'] and sources['commits'][record['source']]['tree'] == record['tree'], 'Receipt commit identity mismatch: ' + name)
        prefix = 'original-source-' if name in diagnostics else 'source-'
        require(record['before'] == name + '/result/' + prefix + 'before.json' and record['after'] == name + '/result/' + prefix + 'after.json', 'Unexpected source manifest paths')
        before, after = data(record['before']), data(record['after'])
        require(before == after and len(before) == record['sourceFiles'], 'Source closure changed: ' + name)
        require(sha(raw(record['before'])) == record['beforeSha256'] and sha(raw(record['after'])) == record['afterSha256'], 'Source manifest fingerprint mismatch')
        selection_name = diagnostics[name][0] if name in diagnostics else name
        require(record['selectedBundle'] == selection_name, 'Selected source bundle mismatch: ' + name)
        selected = data(selection_name + '/selected-paths.json')
        require(selected['source'] == record['source'] and selected['tree'] == record['tree'], 'Selected source identity mismatch')
        require(before == {path: item['sha256'] for path, item in selected['paths'].items()}, 'Selected source hashes differ: ' + name)
        source_file_checks += len(before)
        unchanged_field = 'original_source_unchanged' if name in diagnostics else 'source_unchanged'
        require(record['sourceUnchangedField'] == unchanged_field and summary[unchanged_field] is True, 'Original source integrity failed: ' + name)
        require(summary['runner_sha256_before'] == summary['runner_sha256_after'], 'Original runner changed: ' + name)
        for runner, digest in summary['runner_sha256_before'].items():
            relative = receipt_relative(runner) if '/p1/' in runner.replace('\\', '/') else 'watchdog-envelope-v1/watchdog.py' if runner == 'watchdog.py' else name + '/' + runner
            require(sha(raw(relative)) == digest, 'Runner digest mismatch: ' + relative)
            runner_claims.append({'receipt': name, 'field': 'runner_sha256_before/' + runner, 'path': relative,
                'expectedSha256': digest, 'retainedSha256': digest})
        if name.startswith('focused-'):
            gate = 'build-gate-' + name.split('-')[1] + '-v1/result/summary.json'
            require(summary['gate_receipt_sha256_before'] == summary['gate_receipt_sha256_after'] == sha(raw(gate)), 'Build gate receipt changed: ' + name)
    runner_provenance = load(root / 'RUNNER-PROVENANCE.json')
    require(runner_claims == runner_provenance['claims'] and not runner_provenance['missing'], 'Runner provenance mismatch')
    fa5_gate = data('build-gate-fa5deb70-v1/result/summary.json')
    require('build-gate-fa5deb70-v1/launch.ps1' in records and not any(PurePosixPath(key.replace('\\', '/')).name == 'launch.ps1' for key in fa5_gate['runner_sha256_before']), 'Historical fa5 launcher anchor limitation changed')

    for row in catalog['closeouts']:
        closeout = data(row['closeout'])
        require(closeout['source'] == row['source'] and closeout['tree'] == row['tree'], 'Closeout identity mismatch')
        require(row['outcomes'] == expected_outcomes[row['source'][:8]], 'Historical closeout outcomes changed')
        require(row['failureEvents'] == (6 if row['source'].startswith('de62cd68') else row['outcomes'].get('failed', 0)), 'Historical failure events changed')
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

    for name, (focused, case_names) in diagnostics.items():
        summary = data(name + '/result/summary.json')
        require(summary['kind'] == 'diagnostic-only-not-acceptance-or-mutation-kill', 'Diagnostic scope mismatch')
        require(summary['exit'] == 0 and int(raw(name + '/result/exit.txt')) == 0 and int(raw(name + '/launcher-exit.txt')) == 0, 'Diagnostic capture did not complete')
        require(summary['production_objects_recompiled'] is False and summary['plan']['acceptance_or_mutation_kill_claim'] is False, 'Diagnostic acceptance/recompile claim changed')
        require(summary['original_source_unchanged'] and summary['original_build_artifacts_unchanged'] and summary['original_receipts_unchanged'], 'Diagnostic original integrity failed')
        original_build = data(name + '/result/original-build-before.json')
        require(original_build == data(name + '/result/original-build-after.json'), 'Diagnostic original build changed')
        for path, digest in summary['production_objects_used'].items():
            require(original_build[PurePosixPath(path).name] == digest, 'Diagnostic object hash disagrees with build manifest')
        require(summary['original_receipts_sha256_before'] == summary['original_receipts_sha256_after'], 'Diagnostic changed original receipts')
        prior_receipts = summary['original_receipts_sha256_before']
        if name == 'diagnostic-f22-version-v1':
            require(prior_receipts == data(name + '/result/original-receipts-before.json') == data(name + '/result/original-receipts-after.json'), 'Diagnostic receipt snapshots differ')
            require(set(prior_receipts) == {'focus', 'gate', 'closeout'}, 'Unexpected diagnostic receipt groups')
            for group, bundle in [('focus', focused), ('gate', 'build-gate-f22dcccc-v1')]:
                for path, digest in prior_receipts[group].items():
                    check_retained_hash(bundle + '/' + path, digest)
            check_retained_hash('closeout-f22dcccc.json', prior_receipts['closeout'])
            require(summary['original_scene_sha256'] == original_build['version-field-sources-product.scene'], 'Diagnostic original scene hash mismatch')
        else:
            for path, digest in prior_receipts.items():
                check_retained_hash(path, digest)
        require(summary['cases'] == data(name + '/result/cases.json'), 'Diagnostic case records differ')
        require([case['case'] for case in summary['cases']] == case_names, 'Diagnostic case scope changed')
        for case in summary['cases']:
            require(case['exit'] == 1 and case['timeout'] == 30, 'Diagnostic case failure/timeout changed')
            for channel in ('stdout', 'stderr'):
                require(raw(name + '/result/' + case['case'] + '.' + channel) == case[channel].encode('utf-8'), 'Diagnostic raw capture differs')

    analysis = data('fa5-version-output-analysis-v1/analysis.json')
    require(analysis['kind'] == 'read-only-recovery-of-existing-captured-stderr-not-new-execution', 'Reconstruction classification changed')
    require(analysis['source'] == data('closeout-fa5deb70.json')['source'] and analysis['original_receipts_unchanged'], 'Reconstruction source/receipt claim differs')
    require(analysis['C_executed'] is False and analysis['compiler_executed'] is False, 'Reconstruction execution claim changed')
    for path, digest in analysis['original_receipts_sha256'].items():
        check_retained_hash(path, digest)
    details = data('focused-fa5deb70-successor276-v1/result/test-result.json')['failure_details']
    require(len(analysis['records']) == len(details) == 2, 'Unexpected reconstruction count')
    for record, detail in zip(analysis['records'], details):
        prefix, separator, literal = detail['message'].partition(' not found in ')
        require(separator and prefix.startswith("Regex didn't match: "), 'Unexpected original failure format')
        recovered = ast.literal_eval(literal)
        require(isinstance(recovered, str) and recovered == record['stderr'] and detail['test'] == record['test'], 'Reconstructed stderr differs from original receipt')
        captured = raw(receipt_relative(record['stderr_file']))
        require(captured == recovered.encode('utf-8') and sha(captured) == record['stderr_sha256'], 'Reconstructed stderr bytes/hash mismatch')
        require(recovered.endswith(record['assertion'] + '\n'), 'Reconstructed assertion mismatch')
        require(record['stdout_saved_in_original_receipt'] is False and bool(record['stdout_limitation']), 'Missing stdout limitation lost')
    require(bool(analysis['baseline_output_limitation']), 'Missing baseline output limitation lost')

    watchdog_rounds = [('1792188806920264227', 1, False,
        'watchdog-envelope-v1/recovered-selftest-source-868c0864cbf91da304ca37e7ebee140cfe68542fccc3d6f764f0d27a7f8dd9ac.py'),
        ('1792188883156521844', 0, True, 'watchdog-envelope-v1/selftest.py')]
    for run_id, failures, passed, source_path in watchdog_rounds:
        summary = data('watchdog-envelope-v1/selftest-' + run_id + '/selftest-summary.json')
        require(summary['kind'] == 'no-c-synthetic-watchdog-selftest', 'Watchdog classification changed')
        require((summary['tests_run'], summary['failures'], summary['errors'], summary['passed']) == (9, failures, 0, passed), 'Watchdog historical result changed')
        require(summary['compiled_c'] is False and summary['imported_product_tests'] is False, 'Watchdog product execution claim changed')
        require(sha(raw(source_path)) == summary['selftest_sha256'], 'Watchdog retained end-of-run source hash mismatch')
        require(sha(raw('watchdog-envelope-v1/watchdog.py')) == summary['watchdog_sha256'], 'Watchdog runner hash mismatch')

    coverage = data('original-259-cross-sha-coverage-18edda3f.json')
    require(coverage['kind'] == 'cross-SHA-method-coverage-index-not-same-source-verification', 'Cross-source coverage classification changed')
    require(coverage['same_SHA_259_claim'] is False and coverage['current_product_all_259_pass_inference'] is False, 'Cross-source acceptance claim changed')
    require(coverage['unique_methods_with_PASS_evidence'] == 259 and coverage['distinct_evidence_sources'] == len(coverage['rows']) == 8, 'Cross-source coverage count changed')
    require(len({row['source'] for row in coverage['rows']}) == 8, 'Cross-source source count changed')
    method_ids = []
    coverage_receipts_checked = set()

    def check_coverage_receipt(row, content):
        require(sha(content) == row['sha256'], 'Cross-source receipt hash mismatch')
        summary = json.loads(content)
        require(summary['source'] == row['source'], 'Cross-source receipt source mismatch')
        for methods in row['modules_and_test_ids'].values():
            require(all(summary['test_result']['outcomes'][method] == 'passed' for method in methods), 'Cross-source PASS evidence mismatch')
        coverage_receipts_checked.add(row['source'])

    for row in coverage['rows']:
        methods = [method for group in row['modules_and_test_ids'].values() for method in group]
        require(len(methods) == row['selected_pass_methods'], 'Cross-source row count differs')
        method_ids.extend(methods)
        relative = receipt_relative(row['receipt'])
        if relative in records:
            check_coverage_receipt(row, raw(relative))
    require(len(method_ids) == len(set(method_ids)) == 259, 'Cross-source unique method count differs')

    predecessor_data = load(root / 'PREDECESSORS.json')
    require(set(predecessor_data['packages']) == {'native-p1-20261016', 'native-p1-followup-20261016', 'native-p1-authority-20261017'}, 'Unexpected predecessor pack scope')
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
            prior_rows = [(row, receipt_relative(row['receipt'])) for row in coverage['rows'] if receipt_relative(row['receipt']) in prior['files']]
            if prior_rows:
                with tarfile.open(safe(folder, prior['archive']['file']), 'r:xz') as archive:
                    for row, relative in prior_rows:
                        prior_record = prior['files'][relative]
                        require(prior_record['sha256'] == row['sha256'], 'Predecessor coverage mapping differs')
                        stream = archive.extractfile(prior_record['archiveEntry'])
                        require(stream is not None, 'Predecessor coverage blob missing')
                        check_coverage_receipt(row, stream.read())
        require(len(coverage_receipts_checked) == 8, 'Missing cross-source predecessor receipt')

    sealed_files = 0
    if not unsealed:
        package = load(root / 'PACKAGE-SHA256.json')
        actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
        require(actual == set(package['files']) | {'PACKAGE-SHA256.json'}, 'Package file set mismatch')
        for path, record in package['files'].items():
            content = safe(root, path).read_bytes()
            require(sha(content) == record['sha256'] and len(content) == record['bytes'], 'Sealed package file changed: ' + path)
            sealed_files += 1
    return {'schema': 'geometry-p1-closeouts-publication-verification/1', 'checkedUtc': datetime.now(timezone.utc).isoformat(),
        'ok': True, 'rawFilesVerified': len(records), 'uniqueBlobsVerified': len(blobs),
        'readableCopiesVerified': readable_count, 'originalFilesByteCompared': len(records) if originals else 0,
        'omittedSourceArchivesHashCompared': len(catalog['omitted']) if originals else 0,
        'sourceCommitsVerified': len(sources['commits']), 'sourceManifestFileHashesChecked': source_file_checks,
        'runnerClaimsVerified': len(runner_claims), 'closeoutReferenceHashesVerified': reference_checks,
        'completedHistoricalReceipts': len(catalog['completedReceipts']), 'preparedUnrunBundles': len(catalog['preparedUnrunBundles']),
        'predecessorFilesVerified': predecessor_files, 'packageFilesVerified': sealed_files,
        'packageSealChecked': not unsealed, 'productTestsExecuted': False, 'compilerExecuted': False,
        'wslExecuted': False, 'historicalFailuresRemainFailures': True, 'currentProductAcceptanceClaimed': False,
        'crossSourceCoverageReceiptsVerified': len(coverage_receipts_checked),
        'completeProvenanceClaimed': False, 'verificationScope': 'retained evidence consistency',
        'evidenceLimitations': limitations}


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
