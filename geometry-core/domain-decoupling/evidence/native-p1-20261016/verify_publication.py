#!/usr/bin/env python3
"""Verify portable evidence and optionally compare original source manifests to Git."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def hashes_in(value, label=''):
    if isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value):
        yield label, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from hashes_in(item, label + '/' + key)


def safe_path(root, name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
        raise RuntimeError('Unsafe package-relative path: ' + name)
    resolved = (root / Path(*path.parts)).resolve()
    if not resolved.is_relative_to(root):
        raise RuntimeError('Package path escapes root: ' + name)
    return resolved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('package', type=Path)
    parser.add_argument('--repo', type=Path)
    parser.add_argument('--git-source', action='append', default=[])
    parser.add_argument('--all-git-sources', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    catalog = json.loads((package / 'CONTENT-MANIFEST.json').read_bytes())
    provenance = json.loads((package / 'SOURCE-PROVENANCE.json').read_bytes())
    runners = json.loads((package / 'RUNNER-PROVENANCE.json').read_bytes())
    errors, blobs = [], {}
    if args.report and args.report.exists():
        raise RuntimeError('Preserve prior verification report')
    allowed_paths = {'.gitattributes', 'README.md', 'prepare_publication.py', 'verify_publication.py', 'extract_evidence.py',
                     'CONTENT-MANIFEST.json', 'SOURCE-PROVENANCE.json', 'RUNNER-PROVENANCE.json', 'raw-evidence.tar.xz'}
    allowed_paths.update(record['readableCopy'] for record in catalog['files'].values() if record.get('readableCopy'))
    allowed_paths.update(record['file'] for record in provenance['commits'].values())
    optional_paths = {'VERIFICATION.json', 'finalize_publication.py', 'PACKAGE-SHA256.json'}
    actual_paths = {path.relative_to(package).as_posix() for path in package.rglob('*') if path.is_file()}
    if actual_paths - allowed_paths - optional_paths or allowed_paths - actual_paths:
        errors.append('Unexpected or missing package file paths')
    if any(path.is_symlink() for path in package.rglob('*')):
        errors.append('Package contains symbolic links')
    package_file_path = package / 'PACKAGE-SHA256.json'
    if package_file_path.exists():
        package_files = json.loads(package_file_path.read_bytes())['files']
        if set(package_files) != actual_paths - {'PACKAGE-SHA256.json'}:
            errors.append('Complete package file set differs from frozen checksum manifest')
        for name, record in package_files.items():
            raw = safe_path(package, name).read_bytes()
            if sha(raw) != record['sha256'] or len(raw) != record['bytes']:
                errors.append('Package file differs: ' + name)
    archive_path = safe_path(package, catalog['archive']['file'])
    if archive_path.stat().st_size != catalog['archive']['bytes'] or sha(archive_path.read_bytes()) != catalog['archive']['sha256']:
        errors.append('Raw archive identity mismatch')
    with tarfile.open(archive_path, 'r:xz') as archive:
        for member in archive:
            if not member.isfile() or not member.name.startswith('blobs/') or member.name in blobs:
                raise RuntimeError('Unexpected or duplicate archive member')
            data = archive.extractfile(member).read()
            if member.name != 'blobs/' + sha(data):
                errors.append('Blob content identity mismatch: ' + member.name)
            blobs[member.name] = data
    referenced = set()
    for name, record in catalog['files'].items():
        safe_path(package, name)
        if Path(name).suffix.lower() in ('.exe', '.o', '.obj', '.pdb', '.so', '.dll', '.lib', '.a', '.zip', '.tar', '.xz') or '/mutations/' in name and '/source/' in name:
            errors.append('Binary or repeated mutant checkout included: ' + name)
        referenced.add(record['archiveEntry'])
        raw = blobs[record['archiveEntry']]
        if sha(raw) != record['sha256'] or len(raw) != record['bytes']:
            errors.append('Evidence identity mismatch: ' + name)
        if record.get('readableCopy') and safe_path(package, record['readableCopy']).read_bytes() != raw:
            errors.append('Readable copy differs: ' + name)
    if referenced != set(blobs):
        errors.append('Archive has missing or unreferenced blobs')
    if len(catalog['files']) != catalog['rawFiles'] or len(blobs) != catalog['uniqueBlobs'] or sum(row['bytes'] for row in catalog['files'].values()) != catalog['rawBytes'] or sum(map(len, blobs.values())) != catalog['uniqueBytes']:
        errors.append('Catalog counts do not match actual retained evidence')
    for commit, record in provenance['commits'].items():
        raw = safe_path(package, record['file']).read_bytes()
        actual = hashlib.sha1(b'commit ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if actual != commit or sha(raw) != record['sha256']:
            errors.append('Git commit object differs: ' + commit)
    claimed = {(row['receipt'], row['field'], row['expectedSha256']) for row in runners['claims']}
    expected_claimed = set()
    for name in catalog['completedReceipts']:
        summary = json.loads(blobs[catalog['files'][name + '/summary.json']['archiveEntry']])
        for key, value in summary.items():
            normalized = key.lower().replace('_', '')
            if ('runner' in normalized or normalized == 'producerscriptsha256') and 'sha256' in normalized:
                leaves = list(hashes_in(value, '/' + key))
                if not leaves:
                    errors.append('Unrecognized runner-hash field: ' + name + '/' + key)
                expected_claimed.update((name, field, digest) for field, digest in leaves)
    for name in ('continuation-runner-before.json', 'continuation-runner-after.json', 'next-batch-v1-runner-before.json', 'next-batch-v1-runner-after.json'):
        expected_claimed.update((name, field, digest) for field, digest in hashes_in(json.loads(blobs[catalog['files'][name]['archiveEntry']])))
    if claimed != expected_claimed or len(claimed) != len(runners['claims']):
        errors.append('Runner provenance does not exactly cover every raw receipt and runner manifest claim')
    if runners['missing'] or catalog['missingRunnerClaimCount']:
        errors.append('Package declares unresolved runner identities')
    for claim in runners['claims']:
        if not claim['retainedMatchingFiles'] or any(catalog['files'][name]['sha256'] != claim['expectedSha256'] for name in claim['retainedMatchingFiles']):
            errors.append('Runner bytes unresolved: ' + claim['receipt'] + claim['field'])

    result_checks = []
    source_integrity_checks = []
    recorded_digest_checks = []
    recorded_source_checks = []
    registry_source_claims = []

    def recorded_digest(receipt, field, filename, expected):
        record = catalog['files'].get(filename)
        matched = record is not None and record['sha256'] == expected
        recorded_digest_checks.append({'receipt': receipt, 'field': field, 'file': filename, 'sha256': expected, 'matched': matched})
        if not matched:
            errors.append('Execution-recorded digest differs or file is missing: ' + receipt + '/' + field)

    for name in catalog['completedReceipts']:
        summary = json.loads(blobs[catalog['files'][name + '/summary.json']['archiveEntry']])
        normalized_summary = {key.lower().replace('_', ''): value for key, value in summary.items()}
        exit_value = int(blobs[catalog['files'][name + '/exit.txt']['archiveEntry']].decode('ascii').strip())
        if exit_value != summary['exit']:
            errors.append('Receipt exit file differs from summary: ' + name)
        for field in ('log_sha256', 'logs_sha256'):
            value = summary.get(field)
            if isinstance(value, dict):
                for filename, expected in value.items():
                    recorded_digest(name, field + '/' + filename, name + '/' + filename, expected)
            elif isinstance(value, str):
                filename = {'producer-retry-v2': 'producer.log', 'rectangular-template-c6599522-v1': 'aggregate.log'}.get(name, 'unittest.log')
                recorded_digest(name, field, name + '/' + filename, value)
        for field, directory in (('producer_outputs', 'compatibility-baseline-v1'), ('fixture_sha256', 'compatibility-baseline-v2')):
            for filename, expected in summary.get(field, {}).items():
                recorded_digest(name, field + '/' + filename, directory + '/' + filename, expected)
        if summary.get('native_commands_sha256'):
            recorded_digest(name, 'native_commands_sha256', name + '/native-commands.json', summary['native_commands_sha256'])
        for field in ('binaries', 'adapter_artifacts', 'registry_binary_artifacts'):
            for artifact, value in summary.get(field, {}).items():
                expected = value.get('sidecar_sha256') or value.get('sidecarSha256')
                if expected:
                    recorded_digest(name, field + '/' + artifact + '/sidecarSha256', name + '/' + artifact + '.fingerprint.json', expected)
        if name == 'datum-baseline-a898-v1':
            for field, filename in (('inputSha256', 'datum-baseline-witness/input.json'), ('stdoutSha256', name + '/bridge.stdout'), ('stderrSha256', name + '/bridge.stderr')):
                recorded_digest(name, field, filename, summary[field])
            original_scene = blobs[catalog['files'][name + '/original-test.scene']['archiveEntry']]
            if original_scene != summary['testInputProvenance']['scene'].encode('utf-8'):
                errors.append('Datum original scene differs from recorded test input: ' + name)
            original_sidecar = json.loads(blobs[catalog['files']['baseline-adapters-a898ad6e/bridge.fingerprint.json']['archiveEntry']])
            if summary['bridgeSidecar'] != original_sidecar or summary['bridgeSha256'] != original_sidecar['exe_sha256']:
                errors.append('Datum embedded bridge identity differs from the original baseline sidecar')
            registry_source_claims.extend({'receipt': name, 'source': summary['source'], 'file': filename, 'sha256': expected,
                                           'normalization': 'CRLF-to-LF per original tests/binaries.py'}
                                          for filename, expected in summary['bridgeSidecar']['files'].items())
        plan = next(row for row in provenance['plans'] if row['receipt'] == name)
        before_record = catalog['files'][plan['manifest']]
        before = json.loads(blobs[before_record['archiveEntry']])
        source_claims = []
        source_claims.extend((field, filename, expected) for field, values in (
            ('required_source_sha256', summary.get('required_source_sha256', {})),
            ('recipe/original_source_sha256', summary.get('recipe', {}).get('original_source_sha256', {}))) for filename, expected in values.items())
        source_claims.extend(('recipe/mutation_targets', row['path'], row['sourceSha256']) for row in summary.get('recipe', {}).get('mutation_targets', []))
        for field, filename, expected in source_claims:
            matched = before.get(filename) == expected
            recorded_source_checks.append({'receipt': name, 'field': field, 'file': filename, 'sha256': expected, 'matched': matched})
            if not matched:
                errors.append('Recorded source hash differs from original manifest: ' + name + '/' + field + '/' + filename)
        if summary.get('testInputProvenance'):
            origin = summary['testInputProvenance']
            matching = [row for row in provenance['plans'] if row['source'] == origin['testSource']]
            matched = any(json.loads(blobs[catalog['files'][row['manifest']]['archiveEntry']]).get(origin['testPath']) == origin['testSourceSha256'] for row in matching)
            recorded_source_checks.append({'receipt': name, 'field': 'testInputProvenance/testSourceSha256', 'file': origin['testPath'], 'source': origin['testSource'], 'sha256': origin['testSourceSha256'], 'matched': matched})
            if not matched:
                errors.append('Original datum test provenance differs from its source manifest')
        after_name = name + '/source-after.json'
        if normalized_summary.get('sourcebeforesha256'):
            recorded_digest(name, 'source_before_sha256', plan['manifest'], normalized_summary['sourcebeforesha256'])
        if normalized_summary.get('sourceaftersha256'):
            recorded_digest(name, 'source_after_sha256', after_name, normalized_summary['sourceaftersha256'])
        if after_name in catalog['files']:
            after_record = catalog['files'][after_name]
            before = json.loads(blobs[before_record['archiveEntry']])
            after = json.loads(blobs[after_record['archiveEntry']])
            unchanged = before == after
            if normalized_summary.get('sourceunchanged') is not None and normalized_summary['sourceunchanged'] != unchanged:
                errors.append('Source unchanged claim differs: ' + name)
            source_integrity_checks.append({'receipt': name, 'beforeFileCount': len(before), 'afterFileCount': len(after), 'actualUnchanged': unchanged})
        result = summary.get('test_result')
        result_name = name + '/test-result.json'
        if result_name in catalog['files']:
            retained_result = json.loads(blobs[catalog['files'][result_name]['archiveEntry']])
            if result != retained_result:
                errors.append('Original structured result differs from summary: ' + name)
        log_name = name + '/unittest.log'
        if not isinstance(result, dict) or log_name not in catalog['files']:
            continue
        log = blobs[catalog['files'][log_name]['archiveEntry']].decode('utf-8', errors='replace')
        ran = re.findall(r'^Ran (\d+) tests? in ', log, re.M)
        terminal = re.findall(r'^(OK(?: \([^\n]+\))?|FAILED \([^\n]+\))$', log, re.M)
        if len(ran) != 1 or len(terminal) != 1:
            errors.append('Cannot reconcile original unittest terminal result: ' + name)
            continue
        failures = int((re.search(r'(?:\(|, )failures=(\d+)', terminal[0]) or [None, '0'])[1])
        faults = int((re.search(r'(?:\(|, )errors=(\d+)', terminal[0]) or [None, '0'])[1])
        skipped = int((re.search(r'(?:\(|, )skipped=(\d+)', terminal[0]) or [None, '0'])[1])
        expected_failures = int((re.search(r'(?:\(|, )expected failures=(\d+)', terminal[0]) or [None, '0'])[1])
        unexpected_successes = int((re.search(r'(?:\(|, )unexpected successes=(\d+)', terminal[0]) or [None, '0'])[1])
        actual = {'tests_run': int(ran[0]), 'failures': failures, 'errors': faults, 'skipped': skipped, 'expected_failures': expected_failures, 'unexpected_successes': unexpected_successes}
        expected = {'tests_run': result['tests_run'], 'failures': result['failures'], 'errors': result['errors'], 'skipped': len(result['skipped']), 'expected_failures': result.get('expected_failures', 0), 'unexpected_successes': result.get('unexpected_successes', 0)}
        matched = actual == expected
        if not matched:
            errors.append('Raw failure/count truth differs from summary: ' + name)
        terminal_passed = terminal[0].startswith('OK')
        raw_test_exit = summary.get('test_exit', summary.get('raw_test_exit'))
        if raw_test_exit is not None and raw_test_exit != (0 if terminal_passed else 1):
            errors.append('Raw unittest exit differs from terminal status: ' + name)
        if result.get('successful') is not None and result['successful'] != terminal_passed:
            errors.append('Structured successful flag differs from terminal status: ' + name)
        result_checks.append({'receipt': name, 'rawTerminal': terminal[0], 'rawCounts': actual,
                              'summaryCounts': expected, 'matched': matched,
                              'receiptExit': summary['exit'], 'rawTestExit': summary.get('test_exit', summary.get('raw_test_exit'))})

    source_results, source_cache = [], {}
    plans = provenance['plans'] if args.all_git_sources else [p for p in provenance['plans'] if p['receipt'] in args.git_source]
    if set(args.git_source) - {p['receipt'] for p in plans}:
        raise RuntimeError('Unknown source receipt requested')
    if plans and args.repo is None:
        raise RuntimeError('--repo is required for Git source verification')
    for plan in plans:
        commit = plan['source']
        if commit not in source_cache:
            with tempfile.TemporaryFile() as error_stream:
                process = subprocess.Popen(['git', '-c', 'core.autocrlf=false', '-c', 'core.eol=lf', '-C', str(args.repo), 'archive', '--format=tar', commit], stdout=subprocess.PIPE, stderr=error_stream)
                hashes = {}
                with tarfile.open(fileobj=process.stdout, mode='r|') as archive:
                    for member in archive:
                        if member.isfile():
                            raw = archive.extractfile(member).read()
                            hashes[member.name] = (sha(raw), sha(raw.replace(b'\r\n', b'\n')), sha(raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')))
                # Consume final tar padding too, so a child cannot wait on a full stdout pipe.
                while process.stdout.read(1024 * 1024):
                    pass
                code = process.wait()
                error_stream.seek(0)
                stderr = error_stream.read().decode('utf-8', errors='replace')
                if code != 0:
                    raise RuntimeError('Cannot read source commit ' + commit + ': ' + stderr)
            source_cache[commit] = hashes
        hashes = dict(source_cache[commit])
        for filename, expected in plan['judgeOnlyAddedFiles'].items():
            if filename in hashes:
                raise RuntimeError('Judge overlay overwrites original product: ' + filename)
            raw = subprocess.check_output(['git', '-C', str(args.repo), 'show', plan['judgeSource'] + ':' + filename])
            if sha(raw) != expected:
                raise RuntimeError('Judge overlay hash differs')
            hashes[filename] = (sha(raw), sha(raw), sha(raw))
        manifest = json.loads(blobs[catalog['files'][plan['manifest']]['archiveEntry']])
        mismatches, crlf_variants = [], []
        for filename, expected in manifest.items():
            actual = hashes.get(filename)
            if not actual or expected != actual[0]:
                if actual and plan['allowCrlfCheckoutVariant'] and expected in actual[1:]:
                    crlf_variants.append(filename)
                else:
                    mismatches.append(filename)
        if plan['coverage'] != 'partial-recorded-subset' and set(manifest) != set(hashes):
            mismatches.extend(sorted(set(manifest) ^ set(hashes)))
        source_results.append({'receipt': plan['receipt'], 'source': commit, 'files': len(manifest), 'coverage': plan['coverage'],
                               'matched': not mismatches, 'mismatches': sorted(set(mismatches)), 'declaredCrlfCheckoutVariants': crlf_variants})
        if mismatches:
            errors.append('Source manifest differs: ' + plan['receipt'])
    registry_source_results = []
    for claim in registry_source_claims:
        if claim['source'] not in source_cache:
            continue
        actual = source_cache[claim['source']].get(claim['file'])
        matched = actual is not None and actual[1] == claim['sha256']
        registry_source_results.append(claim | {'matched': matched})
        if not matched:
            errors.append('Registry-normalized source hash differs from Git: ' + claim['file'])
    report = {'schema': 'geometry-p1-publication-verification/1', 'filesVerified': len(catalog['files']), 'uniqueBlobsVerified': len(blobs),
              'runnerClaimsVerified': len(runners['claims']), 'commitObjectsVerified': len(provenance['commits']),
              'rawUnittestReconciliation': result_checks, 'gitSourceChecks': source_results, 'errors': errors,
              'sourceBeforeAfterChecks': source_integrity_checks,
              'executionRecordedDigestChecks': recorded_digest_checks,
              'executionRecordedSourceChecks': recorded_source_checks,
              'registryNormalizedSourceChecks': registry_source_results,
              'newProductTestsExecuted': False, 'exit': 0 if not errors else 1}
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    compact = {key: value for key, value in report.items() if key not in ('rawUnittestReconciliation', 'gitSourceChecks', 'sourceBeforeAfterChecks', 'executionRecordedDigestChecks', 'executionRecordedSourceChecks', 'registryNormalizedSourceChecks')}
    compact['executionRecordedDigestsVerified'] = len(recorded_digest_checks)
    compact['executionRecordedSourceClaimsVerified'] = len(recorded_source_checks)
    compact['rawUnittestResultsMatched'] = all(row['matched'] for row in result_checks)
    compact['gitSourceChecks'] = [{key: value for key, value in row.items() if key not in ('mismatches', 'declaredCrlfCheckoutVariants')} | {'mismatchCount': len(row['mismatches']), 'declaredCrlfCheckoutVariantCount': len(row['declaredCrlfCheckoutVariants'])} for row in source_results]
    print(json.dumps(compact, ensure_ascii=False, indent=2))
    return report['exit']


if __name__ == '__main__':
    raise SystemExit(main())
