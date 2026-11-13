"""Cross-check original failed suites, diagnostic measurements and predecessor bytes."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath

RUN6 = 'native-candidate-6f1fd92f-v1'
DIAG6 = 'section-runs-diagnostic-6f1fd92f-v1'
RUN14 = 'native-candidate-14ab395d-v1'
DIAG14 = 'timeout-diagnostic-14ab395d-v1'
SOURCE6 = '6f1fd92f6886d6512c355baba4435e297b4e9664'
SOURCE14 = '14ab395d56ce1dcabe43e65b5311776a8d3e6221'
OLD_SEAL = 'e828215b3d6c250bf2d088c1dd4be78247b47b4e70769f580ba525968759efc9'


def verify_followup(package, catalog, blobs, provenance, errors):
    checks = []
    files = catalog['files']

    def check(condition, label, **details):
        checks.append({'check': label, 'matched': bool(condition), **details})
        if not condition:
            errors.append('Followup evidence mismatch: ' + label)

    def raw(name):
        return blobs[files[name]['archiveEntry']]

    def data(name):
        return json.loads(raw(name))

    def sha(value):
        return hashlib.sha256(value).hexdigest()

    def digest(name, expected, label):
        check(name in files and sha(raw(name)) == expected, label, file=name, sha256=expected)

    def source_manifest(name):
        return data(name + '/source-before.json')

    check(catalog['completedReceipts'] == [RUN6, DIAG6, RUN14, DIAG14], 'exact four completed receipts')
    check(catalog.get('appendOnly') is True and catalog.get('newProductTestsExecutedByPackaging') is False,
          'append-only packaging does not execute product tests')
    check(catalog.get('fullAcceptanceClaimed') is False and catalog.get('binariesIncluded') is False
          and catalog.get('sourceCheckoutsIncluded') is False, 'no full acceptance or binary/checkout inclusion')
    for name in files:
        try:
            raw(name).decode('utf-8')
        except UnicodeDecodeError:
            check(False, 'retained non-text original file: ' + name)
        if Path(name).suffix == '.bin':
            check(Path(name).name in ('stdout.bin', 'stderr.bin'), 'only captured text .bin outputs: ' + name)
    summaries = {name: data(name + '/summary.json') for name in catalog['completedReceipts']}
    expected_sources = {RUN6: SOURCE6, DIAG6: SOURCE6, RUN14: SOURCE14, DIAG14: SOURCE14}
    check({p['receipt']: p['source'] for p in provenance['plans']} == expected_sources, 'exact source-linked receipt plans')
    for name, summary in summaries.items():
        check(summary['source'] == expected_sources[name], name + '/source commitment')
        manifest = source_manifest(name)
        check(summary['source_files'] == len(manifest) == 15978, name + '/complete source count')
        check(summary['source_unchanged'] is True and data(name + '/source-after.json') == manifest,
              name + '/source before-after equality')
        check(summary['runner_sha256_before'] == summary['runner_sha256_after'] and summary['runners_unchanged'] is True,
              name + '/runner before-after equality')
        launcher = name + '-launcher-exit.txt'
        check(int(raw(launcher)) == int(raw(name + '/exit.txt')) == summary.get('exit', summary.get('capture_exit')),
              name + '/launcher and receipt exits')
        check(summary['full_suite_executed'] is False, name + '/no full suite')
    check(source_manifest(DIAG6) == source_manifest(RUN6), '6f1 diagnostic uses original source closure')
    check(source_manifest(DIAG14) == source_manifest(RUN14), '14ab diagnostic uses original source closure')

    for name, expected_run, expected_outcomes, unrun in (
        (RUN6, 83, {'passed': 81, 'not-started': 18, 'failed': 2, 'error': 2}, 18),
        (RUN14, 101, {'passed': 98, 'failed': 1, 'error': 2}, 0),
    ):
        summary = summaries[name]
        result = data(name + '/test-result.json')
        discovery = data(name + '/test-discovery.json')
        outcomes = result['outcomes']
        discovered = set(discovery['tests'])
        actual_methods = {test for test in discovered if outcomes.get(test) not in (None, 'not-started')}
        setup_errors = set(outcomes) - discovered
        check(len(discovered) == len(discovery['tests']) == summary['recipe']['expected_tests'] == 101,
              name + '/original discovery count')
        check(discovery['modules'] == result['discovered_modules'] == summary['recipe']['module_counts'],
              name + '/module discovery and recipe equality')
        check(result['tests_run'] == len(actual_methods) == expected_run and len(discovered - actual_methods) == unrun,
              name + '/executed versus unexecuted methods', executed=expected_run, unexecuted=unrun)
        check(all(test.startswith('setUpClass (') and outcomes[test] == 'error' for test in setup_errors),
              name + '/extra outcomes are setup errors', setupErrors=sorted(setup_errors))
        check(dict(Counter(outcomes.values())) == expected_outcomes,
              name + '/original per-method outcome truth', outcomes=dict(Counter(outcomes.values())))
        check(result['successful'] is False and result['skipped'] == [] and summary['exit'] == 1 and summary['test_exit'] == 1,
              name + '/failed acceptance remains failed')
        check(len(result['failed_tests']) == result['failures'] and len(result['error_tests']) == result['errors'],
              name + '/failure and error lists preserve counts')
        union = {}
        for group, member_modules in summary['recipe']['groups'].items():
            expected = {test: status for test, status in outcomes.items()
                        if any(test.startswith(module + '.') or module + '.' in test for module in member_modules)}
            record = result['groups'][group]
            check(record['outcomes'] == expected and record['counts'] == dict(Counter(expected.values()))
                  and record['expected'] == summary['recipe']['group_counts'][group]
                  and record['discovered'] == sum(discovery['modules'][module] for module in member_modules)
                  and record['failureDetails'] == [row for row in result['failure_details'] if row['test'] in expected],
                  name + '/group/' + group)
            union.update(expected)
        check(union == outcomes, name + '/groups cover every outcome')
        artifact = data(name + '/native-build-artifacts.json')
        commands = data(name + '/native-build-inputs/build-log.json')
        check(len(commands) == result['compiler_commands'] and len(artifact) == result['build_artifact_count'],
              name + '/build counts', commands=len(commands), artifacts=len(artifact))
        prefix = name + '/native-build-inputs/'
        retained_inputs = {p[len(prefix):]: record for p, record in files.items() if p.startswith(prefix)}
        for path, record in retained_inputs.items():
            check(artifact.get(path) == {'sha256': record['sha256'], 'bytes': record['bytes']},
                  name + '/build input/' + path)

    for name in (DIAG6, DIAG14):
        summary = summaries[name]
        artifacts = data(name + '/build-artifacts.json')
        commands = data(name + '/build-log.json')
        check(len(commands) == summary['compiler_commands'] and all(row['exit'] == 0 for row in commands),
              name + '/diagnostic compilation command records', count=len(commands))
        check(len(artifacts) == summary['build_artifacts'], name + '/diagnostic artifact count', count=len(artifacts))
        prefix = name + '/build-inputs/'
        retained_inputs = {p[len(prefix):]: record for p, record in files.items() if p.startswith(prefix)}
        for path, record in retained_inputs.items():
            check(artifacts.get(path) == {'sha256': record['sha256'], 'bytes': record['bytes']},
                  name + '/build input/' + path)
        check(summary['capture_exit'] == 0 and summary['unittest_methods_executed'] == 0
              and summary['mutations_executed'] is False, name + '/diagnostic completion is not a suite')

    diagnostic = summaries[DIAG6]
    digest(DIAG6 + '/stdout.bin', diagnostic['stdout_sha256'], '6f1 original diagnostic stdout identity')
    digest(DIAG6 + '/stderr.log', diagnostic['stderr_sha256'], '6f1 original diagnostic stderr identity')
    check(raw(DIAG6 + '/stdout.bin').decode('utf-8') == diagnostic['stdout_text']
          and raw(DIAG6 + '/stderr.log').decode('utf-8') == diagnostic['stderr_text'],
          '6f1 diagnostic recorded text matches raw output')
    check(diagnostic['observed_exit'] == 1 and diagnostic['command'][-1] == 'runs', '6f1 diagnostic observed product failure')
    original6_artifacts = data(RUN6 + '/native-build-artifacts.json')
    diag6_artifacts = data(DIAG6 + '/build-artifacts.json')
    check(diagnostic['binary_sha256'] == diagnostic['original_binary_sha256']
          == original6_artifacts['section-profile-client']['sha256'] == diag6_artifacts['section-profile-client']['sha256']
          and diagnostic['binary_matches_original'] is True, '6f1 diagnostic original binary hash chain')

    diagnostic = summaries[DIAG14]
    check(diagnostic['acceptance_result'] is None and diagnostic['diagnostic_error'] is None,
          '14ab timing diagnostic has no acceptance result')
    check([row['label'] for row in diagnostic['results']] == ['rollback', 'imports'], 'exact two timing observations')
    original14_artifacts = data(RUN14 + '/native-build-artifacts.json')
    diag14_artifacts = data(DIAG14 + '/build-artifacts.json')
    for row in diagnostic['results']:
        label = row['label']
        prefix = DIAG14 + '/' + label + '/'
        check(data(prefix + 'measurement.json') == row, '14ab measurement equals summary/' + label)
        for field, filename in (('stdout_sha256', 'stdout.bin'), ('stderr_sha256', 'stderr.bin'),
                                ('nm_stdout_sha256', 'nm.stdout.txt'), ('nm_stderr_sha256', 'nm.stderr.txt')):
            digest(prefix + filename, row[field], label + '/' + field)
        for stream in ('stdout', 'stderr'):
            check(len(raw(prefix + stream + '.bin')) == row[stream + '_bytes'], label + '/' + stream + ' byte count')
        binary = PurePosixPath(row['command'][0]).name
        check(row['binary_sha256_before'] == row['binary_sha256_after'] == row['original_binary_sha256']
              == original14_artifacts[binary]['sha256'] == diag14_artifacts[binary]['sha256']
              and row['binary_matches_original'] is True, label + '/original binary hash chain')
        check(row['watchdog_seconds'] == 120 and row['watchdog_expired'] is False and row['observed_exit'] == 0
              and row['acceptance_result'] is None and row['command'][1] == label
              and row['original_unittest_limit_seconds'] == (20 if label == 'rollback' else 30),
              label + '/separate diagnostic and original timeout limits')
        check(all(isinstance(row[key], (int, float)) and row[key] >= 0 for key in
                  ('elapsed_seconds', 'user_seconds', 'system_seconds', 'max_rss_kib')),
              label + '/raw clock and resource measurements retained')
        nm_lines = raw(prefix + 'nm.stdout.txt').decode('utf-8').splitlines()
        actual_symbols = [line for line in nm_lines if line.split()[-1:] == ['g_world']]
        check(row['nm_exit'] == 0 and row['g_world_symbols'] == actual_symbols, label + '/g_world symbol evidence')
    original_map = {p[len(RUN14) + 1:]: record['sha256'] for p, record in files.items() if p.startswith(RUN14 + '/')}
    before = data(DIAG14 + '/original-receipt-before.json')
    after = data(DIAG14 + '/original-receipt-after.json')
    check(before == after == original_map and len(original_map) == 140 and diagnostic['original_receipt_unchanged'] is True,
          '14ab original receipt every file remains unchanged', files=len(original_map))
    for field, filename in (('original_receipt_before_sha256', 'original-receipt-before.json'),
                            ('original_receipt_after_sha256', 'original-receipt-after.json')):
        digest(DIAG14 + '/' + filename, diagnostic[field], '14ab timing/' + field)
    original_errors = data(RUN14 + '/test-result.json')['failure_details']
    timeout_details = [row for row in original_errors if row['classification'] == 'process-timeout']
    check(len(timeout_details) == 2 and any('after 20 seconds' in row['message'] for row in timeout_details)
          and any('after 30 seconds' in row['message'] for row in timeout_details), '14ab original two timeout traces retained')
    check(files[DIAG14 + '/build-inputs/candidate-product.scene']['sha256']
          == files[RUN14 + '/native-build-inputs/candidate-product.scene']['sha256'], 'imports scene equals original test scene')

    extraction = data('14ab-readonly-diagnostics/default-scene.provenance.json')
    failures = [row for row in original_errors if row['test'].endswith('.test_reset_and_default_replace_complete_world_and_keep_old_history_policy')]
    check(len(failures) == 1 and extraction['original_failure'] == failures[0], 'default dump original failure provenance')
    prefix = "'surface' not found in "
    check(failures[0]['message'].startswith(prefix), 'default dump literal extraction shape')
    actual = ast.literal_eval(failures[0]['message'][len(prefix):]).encode('utf-8')
    retained = raw('14ab-readonly-diagnostics/default-scene.actual-dump.txt')
    check(actual == retained and extraction['source'] == SOURCE14 and extraction['new_product_executions'] == 0
          and extraction['original_result_unchanged'] is True, 'default dump exact extraction, not new execution')
    check(sha(retained) == extraction['dump_sha256'] and len(retained) == extraction['dump_bytes']
          and retained.count(b'\n') == extraction['dump_newline_count'], 'default dump extracted bytes/counts')
    digest(RUN14 + '/test-result.json', extraction['original_result_sha256'], 'default dump original result hash')

    predecessor = json.loads((package / 'PREDECESSOR.json').read_bytes())
    check(predecessor['siblingDirectory'] == 'native-p1-20261016'
          and predecessor['publishedCommit'] == '3de118155ae4ee4233db473e67ea39caf1769396'
          and predecessor['completedReceiptCount'] == 24 and predecessor['fileCount'] == 203
          and predecessor['newReceiptCount'] == 4 and predecessor['sourceRuns'] == 2
          and predecessor['diagnosticRuns'] == 2 and predecessor['defaultDumpIsExtractionOnly'] is True,
          'fixed predecessor and append-only scope')
    check(predecessor['files']['PACKAGE-SHA256.json']['sha256'] == OLD_SEAL, 'predecessor original sealed identity')
    old = package.parent / predecessor['siblingDirectory']
    actual_paths = {p.relative_to(old).as_posix() for p in old.rglob('*') if p.is_file()}
    check(actual_paths == set(predecessor['files']), 'predecessor exact unchanged file set')
    original_seal_raw = (old / 'PACKAGE-SHA256.json').read_bytes()
    original_seal = json.loads(original_seal_raw)['files']
    original_seal['PACKAGE-SHA256.json'] = {'sha256': sha(original_seal_raw), 'bytes': len(original_seal_raw)}
    check(predecessor['files'] == original_seal and sha(original_seal_raw) == OLD_SEAL,
          'predecessor file hashes are anchored by original sealed manifest')
    for name, record in predecessor['files'].items():
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
            check(False, 'unsafe predecessor path: ' + name)
            continue
        target = old / Path(*path.parts)
        check(target.is_file() and not target.is_symlink() and sha(target.read_bytes()) == record['sha256']
              and target.stat().st_size == record['bytes'], 'predecessor unchanged/' + name)
    check(files['runtime/wsl_locked3.sh']['sha256'] == predecessor['files']['readable/runtime/wsl_locked3.sh']['sha256'],
          'same original shared-lock wrapper bytes')
    return checks
