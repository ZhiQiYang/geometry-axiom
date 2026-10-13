"""Prepare bounded, read-only CDP and independent-review publication projections.

Writes only a new scratch output directory. Never changes originals, repository,
services, browser state, GitHub state, historical executable identity or results.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil

BASE = Path('<original-evidence-root>')
REVIEW = Path('<independent-review-root>')
CLOSEOUT = Path('<delivery-closeout-root>')
CB8 = 'cb8d4e70d1659458017658d52139e2843cc5ba72'
BASELINE = '9029a8f6bc00a9ff8de1d2b0deb844f331e032e3'
REPLACEMENTS = {
    str(BASE): '<original-evidence-root>',
    str(REVIEW): '<independent-review-root>',
    str(CLOSEOUT): '<delivery-closeout-root>',
    '<takeover-repository-root>': '<takeover-repository-root>',
    '<baseline-repository-root>': '<baseline-repository-root>',
    '<frozen-cb8-repository-root>': '<frozen-cb8-repository-root>',
    '<resume-repository-root>': '<resume-repository-root>',
    '<configured-native-directory>': '<configured-native-directory>',
    '<node-runtime>': '<node-runtime>',
    '<python-runtime>': '<python-runtime>',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def redact_text(text):
    for prefix, replacement in sorted(REPLACEMENTS.items(), key=lambda item: -len(item[0])):
        text = text.replace(prefix, replacement)
    text = re.sub(r'<isolated-test-directory>"\x27<>]+', '<isolated-test-directory>', text)
    text = re.sub(r'<workspace-path>"\x27<>]+', '<workspace-path>', text)
    text = re.sub(r'<execution-runtime-path>"\x27<>]+', '<execution-runtime-path>', text)
    return text


def private(text):
    return any(token in text for token in ('<workspace-root-prefix>/', '<isolated-test-prefix>', '<execution-root-prefix>/'))


def project(value):
    if isinstance(value, dict):
        return {project(key): project(item) for key, item in value.items()}
    if isinstance(value, list):
        return [project(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def copy_projection(original, target, output, purpose):
    original = Path(original)
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = not private(original.read_text())
    if raw:
        shutil.copyfile(original, target)
        assert sha(original) == sha(target)
    else:
        target.write_text(redact_text(original.read_text()))
    return {
        'path': target.relative_to(output).as_posix(),
        'bytes': target.stat().st_size,
        'sha256': sha(target),
        'originalPathLabel': redact_text(str(original)),
        'originalBytes': original.stat().st_size,
        'originalSha256': sha(original),
        'byteIdenticalOriginal': raw,
        'publicProjection': not raw,
        'projectionChanges': [] if raw else ['Machine/executable/isolated feedback/profile path labels only.'],
        'originalRetainedOutsideGit': True,
        'purpose': purpose,
    }


def canonical_from_log(log):
    matches = [line[len('CDP_RESULT '):] for line in log.read_text().splitlines() if line.startswith('CDP_RESULT ')]
    assert len(matches) == 1, (log, len(matches))
    return json.loads(matches[0])


def pack_round(output, label, directory, head, expected, runner):
    receipt_path = directory / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    log = directory / 'command.log'
    assert receipt.get('finished') and receipt.get('after')
    assert receipt['before']['git']['head'] == receipt['after']['git']['head'] == head
    assert receipt['before']['git']['status'] == receipt['after']['git']['status'] == ''
    assert receipt['before']['sourceSha256'] == receipt['after']['sourceSha256']
    assert receipt['before']['runnerSha256'] == receipt['after']['runnerSha256'] == sha(runner)
    assert receipt['log']['sha256'] == sha(log)
    assert receipt['log']['bytes'] == log.stat().st_size
    assert receipt['problems'] == receipt['before']['problems'] == receipt['after']['problems'] == []
    result = canonical_from_log(log)
    assert (result['scope']['mode'], result['passedAssertions'], result['failedAssertions'],
            result['completed'], receipt['execution']['exitCode']) == expected
    destination = output / 'rounds' / label
    files = [copy_projection(log, destination / 'command.public.log', output, 'Raw command log; path-only projection when required.')]
    published = project(receipt)
    published['publicProjection'] = {
        'originalReceiptSha256': sha(receipt_path),
        'originalReceiptBytes': receipt_path.stat().st_size,
        'originalPathLabel': redact_text(str(receipt_path)),
        'originalRetainedOutsideGit': True,
        'changes': 'Machine and isolated directory paths only; command/source/identity/exit/results/hashes unchanged.',
    }
    write(destination / 'receipt.public.json', published)
    result_public = {
        'origin': 'Exact CDP_RESULT JSON payload parsed from the retained raw command log; paths projected only.',
        'originalLogSha256': sha(log),
        'originalLogBytes': log.stat().st_size,
        'canonicalResult': project(result),
    }
    write(destination / 'canonical-result.public.json', result_public)
    sources = []
    selected = ('geometry-web/cdp_test.js', 'geometry-web/cdp_helpers.js', 'geometry-web/grid_rule_editor_test.js',
                'geometry-web/grid_rule_lines_test.js', 'geometry-web/cdp_navigation.js', 'geometry-web/cdp_evaluation.js')
    snapshot = directory / 'executed-harness-sources'
    for relative, digest in receipt['before']['sourceSha256'].items():
        assert sha(snapshot / relative) == digest, relative
    for relative in selected:
        original = snapshot / relative
        if original.is_file():
            entry = copy_projection(original, destination / 'source' / relative, output,
                                    'Retained actually executed committed source; no oracle changes.')
            entry['repositoryPath'] = relative
            entry['sourceHead'] = head
            entry['publishedCopyWasExecuted'] = False
            sources.append(entry)
    sources.append(copy_projection(runner, destination / 'source' / runner.name, output,
                                   'Original scratch runner, historical recorded hash verified; publication copy not executed.'))
    if 'readOnlyLayoutPreloadSha256' in receipt['before']:
        original = BASE / 'grid-rule-layout-read.cjs'
        assert sha(original) == receipt['before']['readOnlyLayoutPreloadSha256']
        sources.append(copy_projection(original, destination / 'source' / original.name, output,
                                       'Read-only layout logger: adds no clicks, keys, scrolls, retries or assertions.'))
    for name, digest in receipt['before']['launchAdapterSha256'].items():
        original = BASE / 'full-launch-adapters' / name
        assert sha(original) == digest
        sources.append(copy_projection(original, destination / 'source' / 'launch-adapters' / name, output,
                                       'Actual historical sandbox launch adapter, original hash verified; publication copy not executed.'))
    review = directory / 'failed-full-executor-review.json'
    if review.exists():
        files.append(copy_projection(review, destination / 'executor-byte-review.public.json', output,
                                     'Same executor byte review, not an independent actor or new execution.'))
    executable_identity = receipt['before'].get('executables')
    return {
        'name': label,
        'testedHead': head,
        'dirty': False,
        'beforeTree': receipt['before']['git']['tree'],
        'afterTree': receipt['after']['git']['tree'],
        'createdUtc': receipt['created'],
        'finishedUtc': receipt['finished'],
        'command': receipt['command'],
        'executionExitCode': receipt['execution']['exitCode'],
        'gateExitCode': receipt['gateExitCode'],
        'canonicalResult': project(result),
        'receiptPath': (destination / 'receipt.public.json').relative_to(output).as_posix(),
        'originalReceiptSha256': sha(receipt_path),
        'originalReceiptBytes': receipt_path.stat().st_size,
        'sourceSnapshotVerifiedFiles': len(receipt['before']['sourceSha256']),
        'sourceSha256': receipt['before']['sourceSha256'],
        'runtimeAndActualNative': {
            'beforeRuntime': project(receipt['before']['runtime']),
            'afterRuntime': project(receipt['after']['runtime']),
            'beforeConfiguredNative': project(receipt['before']['native']),
            'afterConfiguredNative': project(receipt['after']['native']),
            'beforeLiveDirectChildBridge': project(receipt['before']['liveBridge']),
            'afterLiveDirectChildBridge': project(receipt['after']['liveBridge']),
        },
        'executableIdentity': project(executable_identity) if executable_identity else {
            'node': 'unknown: historical executable/version/hash absent; current Node not rebound',
            'browser': 'unknown: historical executable/hash absent; scope PID/profile alone retained',
            'python': {'versionOnly': receipt['python'], 'executableHash': 'unknown'},
        },
        'liveExecutionIdentity': project(receipt.get('executionIdentity', 'unknown: not captured for this historical run')),
        'publicLogAndReview': files,
        'executedSourceOrPublicationCopies': sources,
        'releaseApproved': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert not output.exists()
    assert output.is_relative_to(CLOSEOUT)
    output.mkdir(parents=True)
    rounds = [
        pack_round(output, 'full-cdp-cb8-incomplete', BASE / 'after-known-four-cb8d4e7-20261009' / 'full-cdp-gate',
                   CB8, ('full', 1383, 0, False, 1), BASE / 'run_full_cdp.py'),
        pack_round(output, 'partial-grid-baseline-9029', BASE / 'baseline-p87-layout-9029-20261009',
                   BASELINE, ('partial', 346, 0, True, 0), BASE / 'run_cdp_grid_diagnostic.py'),
        pack_round(output, 'partial-grid-cb8-incomplete', BASE / 'candidate-p87-layout-cb8-20261009',
                   CB8, ('partial', 193, 0, False, 1), BASE / 'run_cdp_grid_diagnostic_identity.py'),
    ]
    independent = []
    for name in ('independent-actor-scoped-semantics-review.json', 'independent-actor-scoped-semantics-review-receipt.json',
                 'independent-actor-scoped-semantics-review.log', 'review_scoped_semantics.py',
                 'semantic-review-r1-independent-actor-scoped-semantics-review.json',
                 'semantic-review-r1-review_scoped_semantics.py'):
        original = REVIEW / name
        assert original.is_file(), original
        independent.append(copy_projection(original, output / 'independent-review' / name, output,
                                           'Distinct reviewer actor read-only semantic verification; no browser re-execution.'))
    report = json.loads((REVIEW / 'independent-actor-scoped-semantics-review.json').read_text())
    assert report['actor'] == '/root/race_review' and report['testedSHA'] == CB8 and report['result'] is True
    assert sha(REVIEW / 'independent-actor-scoped-semantics-review.json') == 'c39122e2f0f79949f0d21243b85448a8f462f9c332ba92a222dec13792bf38e0'
    manifest = {
        'schema': 'geometry-cdp-diagnosis-public/1',
        'preparedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'preparerActor': '/root/delivery_closeout',
        'scope': 'Historical incomplete canonical full CDP and two purpose-specific existing partial diagnostics; separate independent actor review of seven scoped gates. No new product test execution.',
        'rounds': rounds,
        'independentActorReview': {
            'actor': report['actor'],
            'executorActor': '/root/evidence_harness',
            'independence': report['independence'],
            'testedHead': CB8,
            'dirty': False,
            'originalReportSha256': sha(REVIEW / 'independent-actor-scoped-semantics-review.json'),
            'originalReceiptSha256': sha(REVIEW / 'independent-actor-scoped-semantics-review-receipt.json'),
            'gateCensus': [{key: gate[key] for key in ('gate', 'declaredCases', 'semanticPassed')} for gate in report['gates']],
            'publicFiles': independent,
            'oldExecutorIndependentFilenameIsIndependentReview': False,
        },
        'historicalFullCdp': {'testedHead': '5174a8dafd8c48329d7166abbd3d104e3c28c0c4', 'passed': 2207, 'failed': 0, 'skipped': 0, 'rebound': False},
        'windows173': {'passed': 1692, 'failed': 2, 'exitCode': 1, 'completed': False, 'rawReceivedInCloud': False, 'partialResultsAggregated': False, 'goldenComparedByThisTask': False},
        'omissions': ['Private feedback and user data', 'Browser trace/profile and screenshots', 'Native binary/sidecar bytes', 'Private queue DB, events and owner-thread data', 'Missing historical executable identities are not reconstructed from current files'],
        'limitations': ['No counts added together to create full acceptance.', 'Original historical failures preserved.', 'Formal EDGE38 historical Node executable/version/hash unknown.', 'Full cb8 and baseline partial historical Node/browser executable/hash unknown; cb8 partial captured its own live bindings.', 'Before/after clean identity does not prove absence of transient source edits.', 'Independent reviewer wrote formal20 supplemental oracle; actor distinction does not establish independent oracle authorship.'],
        'releaseApproved': False,
    }
    shutil.copyfile(CLOSEOUT / 'cdp-diagnosis-README.md', output / 'README.md')
    manifest['publicFiles'] = [
        {'path': path.relative_to(output).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)}
        for path in sorted(output.rglob('*')) if path.is_file()
    ]
    write(output / 'manifest.json', manifest)
    for path in output.rglob('*'):
        if path.is_file():
            assert not private(path.read_text()), path
    print(json.dumps({'bundle': str(output), 'manifestSha256': sha(output / 'manifest.json'),
                      'files': len(manifest['publicFiles']) + 1,
                      'bytes': sum(path.stat().st_size for path in output.rglob('*') if path.is_file()),
                      'sourceTestedHeads': [r['testedHead'] for r in rounds]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
