"""Independent, read-only publisher/evidence QA. No product tests are executed."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ACTOR = '/root/delivery_closeout/packet_readonly_qa'
BASE = Path('<workspace-path>')
REPO = Path('<workspace-path>')
EXPECTED_MANIFESTS = {
    'ui-single-room-prior-public-v2': '9e056d97db6fb5c7e14062014e8be7e7895a92ebed651500e53ffbbf3b6eed66',
    'ui-single-room-640-public-v2': '888c4697d96bcdc66bc99cbae975749fa4a93dd9485944693f9fbe55c243ab8b',
    'ui-single-room-0b37-failed-public-v2': 'e6fd7bc548bcb75aa5de2847be22277721a7df765c1d4867e6990ede2c984ae7',
}
P = '<workspace-path>'
S = '<workspace-path>'
H = '<workspace-path>'
V = '<workspace-path>'
E = '<workspace-path>'
PRIOR_RECEIPTS = {
    'ui123-2703-original-six': '<isolated-test-directory>',
    'ui123-f980-six': '<isolated-test-directory>',
    'room54-f980-incomplete-ten': V + '/room54-f98078dc-gate/receipt.json',
    'ui123-c0-six': '<isolated-test-directory>',
    'grid-c0-incomplete': E + '/after-final-c0f05baa-grid-20261009/receipt.json',
    'projection-f980-original-ten': P + '/baseline-f980-r2/receipt.json',
    'projection-c0-original-ten': P + '/after-c0f05baa-r1/receipt.json',
    'same-owner-f980': S + '/baseline-f980-r1/receipt.json',
    'same-owner-c0': S + '/after-c0f05baa-r1/receipt.json',
    'normal-hole-f980': H + '/baseline-f980-r1/receipt.json',
    'normal-hole-c0': H + '/after-c0f05baa-r1/receipt.json',
    'resume-c0-four': P + '/after-c0f05baa-resume-r4/receipt.json',
    'scenario-c0-formal-four': '<workspace-path>',
}
# Expected counts are reviewer input from original handoff; no cross-scope sum.
EXPECTED_RESULTS = {
    'ui123-2703-original-six': (85, 5, True, 1),
    'ui123-f980-six': (194, 0, True, 0),
    'room54-f980-incomplete-ten': (208, 1, False, 1),
    'ui123-c0-six': (174, 1, True, 1),
    'grid-c0-incomplete': (99, 1, False, 1),
    'projection-f980-original-ten': (3, 7, True, 1),
    'projection-c0-original-ten': (8, 2, True, 1),
    'same-owner-f980': (0, 2, True, 1),
    'same-owner-c0': (2, 0, True, 0),
    'normal-hole-f980': (2, 0, True, 0),
    'normal-hole-c0': (2, 0, True, 0),
    'resume-c0-four': (4, 0, True, 0),
    'scenario-c0-formal-four': (131, 0, True, 0),
    'ui123-640-six-with-header-hit': (198, 0, True, 0),
    'room54-640-original-ten-negatives': (273, 0, True, 0),
    'formal-edge-640-38': (38, 0, True, 0),
    'grid-640-partial-identity-gap': (346, 0, True, 0),
    'projection-640-corrected-v2-ten': (10, 0, True, 0),
    'same-owner-640-two': (2, 0, True, 0),
    'ui123-640-four-supplement-failed': (108, 3, False, 1),
    'ui123-0b37-four-supplement-v2-failed': (138, 3, False, 1),
    'full-cdp-0b37-incomplete': (506, 4, False, 1),
    'full-space-0b37-incomplete': (222, 7, False, 1),
    'replacement-0b37-sixteen': (16, 0, True, 0),
    'cross-b-0b37-old-entry-incomplete': (4, 4, False, 1),
    'card-0b37-four': (4, 0, True, 0),
}
EXPECTED_RESULTS = {
    'replacement-243-scoped': (16, 0, True, 0),
    'cross-b-visible-picker-v2-243-scoped': (8, 0, True, 0),
    'held-bhit-visible-picker-243-scoped': (2, 0, True, 0),
    'held-proj-visible-picker-243-scoped': (2, 0, True, 0),
    'card-243-scoped': (4, 0, True, 0),
    'formal-race-243-scoped': (20, 0, True, 0),
    'full-space-243-complete-declared-five': (228, 0, True, 0),
    'full-cdp-243-terminal-failed': (1713, 6, False, 1),
    'ui123-four-v4-failed-243': (185, 2, False, 1),
    'ui123-four-v5-complete-243': (327, 0, True, 0),
    'room54-original-ten-negatives-243': (273, 0, True, 0),
}
REPLACEMENTS = {
    E: '<original-evidence-root>',
    '<workspace-path>': '<independent-review-root>',
    str(BASE): '<delivery-closeout-root>',
    '<workspace-path>': '<takeover-repository-root>',
    '<workspace-path>': '<baseline-repository-root>',
    '<workspace-path>': '<frozen-cb8-repository-root>',
    '<workspace-path>': '<resume-repository-root>',
    '<isolated-test-directory>': '<configured-native-directory>',
    '<execution-runtime-path>': '<node-runtime>',
    '<execution-runtime-path>': '<python-runtime>',
    '<workspace-path>': '<unit-evidence-root>',
    '<workspace-path>': '<old-unit-evidence-root>',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def redact(text):
    for key, value in sorted(REPLACEMENTS.items(), key=lambda item: -len(item[0])):
        text = text.replace(key, value)
    for pattern, replacement in [
        (r'/tmp/geometry-[^\s"\x27<>]+', '<isolated-test-directory>'),
        (r'/workspace/[^\s"\x27<>]+', '<workspace-path>'),
        (r'/opt/codex/[^\s"\x27<>]+', '<execution-runtime-path>'),
        (r'/tmp/playwright_chromiumdev_profile-[^\s"\x27<>]+', '<isolated-browser-profile>'),
    ]:
        text = re.sub(pattern, replacement, text)
    return text


def project(value):
    if isinstance(value, dict):
        key_labels = [redact(key) for key in value]
        mapped = {key: (label + '|basename=' + Path(key).name + '|originalKeySha256=' + sha(key.encode()) if key_labels.count(label) > 1 else label) for key, label in zip(value, key_labels)}
        assert len(set(mapped.values())) == len(value)
        return {mapped[key]: project(item) for key, item in value.items()}
    if isinstance(value, list):
        return [project(v) for v in value]
    return redact(value) if isinstance(value, str) else value


def dictionary_audit(value, location='$', output=None):
    if output is None:
        output = []
    if isinstance(value, dict):
        labels = [redact(key) for key in value]
        mapping = {key: (label + '|basename=' + Path(key).name + '|originalKeySha256=' + sha(key.encode()) if labels.count(label) > 1 else label) for key, label in zip(value, labels)}
        if len(set(labels)) != len(labels):
            output.append({'dictionaryLocation': location, 'originalEntries': len(value), 'publicEntries': len(value), 'rule': 'Colliding public path keys retain basename plus full SHA256 of original key; values retained one-to-one', 'mapping': [{'originalKeySha256': sha(key.encode()), 'originalBasename': Path(key).name, 'publicKey': mapping[key]} for key in value]})
        for key, item in value.items():
            dictionary_audit(item, location + '.' + redact(key), output)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            dictionary_audit(item, location + '[' + str(index) + ']', output)
    return output


def private_path(text):
    return any(x in text for x in ['/workspace/', '/opt/codex/', '/tmp/geometry-', '/tmp/playwright_chromiumdev_profile-'])


def strict_pairs(rows):
    result = {}
    for key, item in rows:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = item
    return result


def strict_json(text):
    return json.loads(text, object_pairs_hook=strict_pairs)


def head_dirty(j, after=False):
    if 'run' in j:
        return (j['run']['headAfter'], j['run']['dirtyAfter']) if after else (j['run']['head'], j['run']['dirty'])
    v = j.get('after' if after else 'before', {})
    v = v.get('git', v)
    return v.get('head', v.get('fullSHA')), v.get('status', v.get('dirty'))


def canonical(j, original_log=None):
    if 'run' in j:
        return j['passed'], j['failed'], j['completed'], j['run']['exitCode']
    if 'pass' in j:
        return j['pass'], j['fail'], j['completed'], j['exitCode']
    if 'acceptanceResult' in j:
        a = j['acceptanceResult']
        return a['passed'], a['failed'], a['completed'], j['execution']['exitCode']
    if 'formalResult' in j:
        a = j['formalResult']['canonical'][0]
        return a['passed'], a['failed'], a['completed'], j['execution']['exitCode']
    a = j.get('evidence', {}).get('canonicalResult')
    if a:
        return a.get('passedAssertions', a.get('passed')), a.get('failedAssertions', a.get('failed')), a['completed'], j['execution']['exitCode']
    if 'probeCensus' in j:
        a = j['probeCensus']
        return a['pass'], a['fail'], a['completed'], j['execution']['exitCode'] if 'execution' in j else j['exitCode']
    if original_log:
        records = [json.loads(line.split(' ', 1)[1]) for line in original_log.read_text().splitlines() if line.startswith(('CDP_RESULT ', 'SPACE_RESULT '))]
        if records:
            assert len(records) == 1
            a = records[0]
            return a.get('passedAssertions', a.get('passed')), a.get('failedAssertions', a.get('failed')), a['completed'], j['execution']['exitCode']
    if 'result' in j:
        a = j['result']
        if 'counts' in a:
            return a['counts']['pass'], a['counts']['fail'], a['completed'], j['execution']['exitCode']
        return a['pass'], a['fail'], True, j['execution']['exitCode']
    raise ValueError('Unknown receipt result schema')


def main():
    out = Path(sys.argv[1])
    global EXPECTED_MANIFESTS
    if len(sys.argv) > 2:
        EXPECTED_MANIFESTS = json.loads(Path(sys.argv[2]).read_text())
    current_bundle = next(iter(EXPECTED_MANIFESTS))
    out.mkdir(parents=True, exist_ok=True)
    def git_state():
        return {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(), 'dirty': subprocess.check_output(['git', 'status', '--short'], cwd=REPO, text=True).strip(), 'cwd': str(REPO)}
    before = git_state()
    actual_python = Path(os.readlink('/proc/self/exe'))
    execution_identity = {'actor': ACTOR, 'pid': os.getpid(), 'argv': sys.argv, 'cwd': os.getcwd(), 'script': str(Path(__file__).resolve()), 'scriptSha256': sha(Path(__file__).read_bytes()), 'actualPythonExecutable': str(actual_python), 'actualPythonExecutableSha256': sha(actual_python.read_bytes()), 'pythonVersion': sys.version}
    print('REVIEW_IDENTITY', json.dumps(execution_identity, sort_keys=True))
    findings = []
    checks = []
    def check(ok, kind, detail):
        checks.append({'kind': kind, 'ok': bool(ok), 'detail': detail})
        if not ok:
            findings.append({'kind': kind, 'detail': detail})
    manifests = {name: json.loads((BASE / name / 'manifest.json').read_text()) for name in EXPECTED_MANIFESTS}
    originals = {}
    for name in ['ui-243-config.json']:
        originals.update({x['name']: x['receipt'] for x in json.loads((BASE / name).read_text())})
    all_refs = []
    for bundle, m in manifests.items():
        all_refs.extend([(bundle, ref) for r in m['rounds'] for ref in r['rawEvidence']])
        all_refs.extend([(bundle, ref) for field in ['historyReviewsAndExecutorSources', 'fullTestedCommitSourceCopies'] for ref in m[field]])
    sizes = {x.get('originalBytes') for _, x in all_refs if x.get('originalBytes') is not None}
    names_without_size = {Path(x['path']).name for _, x in all_refs if x.get('originalBytes') is None}
    wanted = {x.get('originalSha256') for _, x in all_refs}
    wanted.update(r['originalReceiptSha256'] for m in manifests.values() for r in m['rounds'])
    roots = [Path(V), Path(P), Path(S), Path(H), Path(E),
             Path('<workspace-path>'),
             Path('<workspace-path>'),
             Path('<workspace-path>'),
             BASE / 'ui-retained-source-snapshots', BASE / 'pr179-ci-0b37-readonly']
    for extra in ['ui-243-extra-evidence.json']:
        for item in json.loads((BASE / extra).read_text()):
            roots.append(Path(item['path']))
    for config in ['ui-243-config.json']:
        for item in json.loads((BASE / config).read_text()):
            roots.extend(Path(x) for x in item.get('artifacts', []))
    roots += [p for p in Path('/tmp').glob('geometry-*') if p.is_dir() and any(t in p.name for t in ['ui123-', 'room54-', 'resume-browser-c0f05baa'])]
    candidates = set()
    for root in roots:
        if root.is_file():
            candidates.add(root)
        elif root.is_dir():
            candidates.update(p for p in root.rglob('*') if p.is_file() and not ({'feedback', 'queue', 'profile', 'profiles', 'node_modules', '__pycache__'} & set(p.parts)))
    by_hash = {}
    for path in sorted(candidates):
        if path.stat().st_size not in sizes and path.name not in names_without_size and str(path) not in originals.values():
            continue
        digest = sha(path.read_bytes())
        if digest in wanted:
            by_hash.setdefault(digest, []).append(path)
    zip_summary = {'archives': 0, 'projectedEntries': 0, 'binaryEntries': 0, 'unchangedEntries': 0, 'maxBytes': 0}
    world_count = 0
    source_count = 0
    snapshot_entries = {}
    git_source_cache = {}
    round_reports = []
    ref_count = 0
    for bundle, m in manifests.items():
        directory = BASE / bundle
        check(sha((directory / 'manifest.json').read_bytes()) == EXPECTED_MANIFESTS[bundle], 'manifest-hash', bundle)
        declared_paths = [x['path'] for x in m['publicFiles']]
        actual_paths = [p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file() and p.name != 'manifest.json']
        # Nested snapshot manifests are public files too.
        actual_paths = [p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file() and p != directory / 'manifest.json']
        check(len(declared_paths) == len(set(declared_paths)) and set(declared_paths) == set(actual_paths), 'public-file-census', {'bundle': bundle, 'declared': len(declared_paths), 'actual': len(actual_paths)})
        for item in m['publicFiles']:
            path = directory / item['path']
            check(path.is_relative_to(directory) and not path.is_symlink() and '..' not in Path(item['path']).parts, 'safe-public-path', item['path'])
            data = path.read_bytes()
            check(len(data) == item['bytes'] and sha(data) == item['sha256'], 'public-file-identity', {'bundle': bundle, 'path': item['path']})
            check(not ({'feedback', 'queue', 'profile', 'profiles', 'node_modules'} & set(Path(item['path']).parts)), 'no-private-data-directory', item['path'])
            if path.suffix not in ['.zip', '.gcanvas', '.pdf', '.png']:
                text = data.decode('utf-8')
                check(not private_path(text), 'no-machine-private-path', {'bundle': bundle, 'path': item['path']})
                # Terms in explanatory documentation do not represent payload.
                check(not any(x in text for x in ['"owner_thread_id":', '"PRIVATE_QUEUE_DATABASE":', 'closure-evidence/queue/']), 'no-private-payload-token', item['path'])
                if path.suffix in ['.json', '.jsonl']:
                    try:
                        if path.suffix == '.json':
                            strict_json(text)
                        else:
                            for line in text.splitlines():
                                if line.strip():
                                    strict_json(line)
                        check(True, 'strict-json-jsonl-readable-no-key-loss', {'bundle': bundle, 'path': item['path']})
                    except ValueError as error:
                        check(False, 'strict-json-jsonl-readable-no-key-loss', {'bundle': bundle, 'path': item['path'], 'error': str(error)})
        check(m['releaseApproved'] is False, 'no-release-approval', bundle)
        check(m['historicalFullCdp'] == {'testedHead': '5174a8dafd8c48329d7166abbd3d104e3c28c0c4', 'pass': 2207, 'fail': 0, 'skip': 0, 'rebound': False}, 'historic-cdp-binding', bundle)
        check(m['windows173'] == {'pass': 1692, 'fail': 2, 'exitCode': 1, 'completed': False, 'cloudOriginalsReceived': False, 'partialsAggregated': False, 'goldenComparedByThisPacket': False}, 'windows-not-relabelled', bundle)
        for r in m['rounds']:
            receipt = Path(originals[r['name']])
            j = json.loads(receipt.read_text())
            pub = json.loads((directory / r['receiptPath']).read_text())
            provenance = pub.pop('publicProjection')
            check(sha(receipt.read_bytes()) == r['originalReceiptSha256'] == provenance['originalSha256'], 'original-receipt-identity', r['name'])
            check(pub == project(j), 'receipt-path-only-projection', r['name'])
            check(provenance['dictionaryKeyAudit'] == dictionary_audit(j), 'receipt-all-original-key-audit', r['name'])
            check(re.fullmatch('[0-9a-f]{40}', r['testedHead']) is not None and r['dirty'] is False, 'full-tested-sha-clean', r['name'])
            check(head_dirty(j) == (r['testedHead'], '') and head_dirty(j, True) == (r['testedHead'], ''), 'original-before-after-binding', {'scope': r['name'], 'before': head_dirty(j), 'after': head_dirty(j, True)})
            log = Path(j['log']['path']) if 'log' in j else None
            observed = canonical(j, log)
            check(observed == EXPECTED_RESULTS[r['name']], 'original-canonical-result', {'scope': r['name'], 'observed': observed, 'expected': EXPECTED_RESULTS[r['name']]})
            d = r['declaredResult']
            if 'pass' in d:
                check((d['pass'], d['fail'], d['completed'], d.get('actualExitCode', d.get('actualNodeExitCode'))) == observed, 'declared-result-keeps-scope', r['name'])
            if log:
                check(sha(log.read_bytes()) == j['log']['sha256'], 'original-log-identity', r['name'])
            for log_ref in j.get('logs', []):
                check(sha(Path(log_ref['path']).read_bytes()) == log_ref['sha256'], 'original-stream-identity', {'scope': r['name'], 'stream': log_ref.get('stream')})
            if 'run' in j:
                check(sha(Path(j['run']['rawLogPath']).read_bytes()) == j['run']['rawLogSHA256'], 'probe-original-log-identity', r['name'])
            if 'probeCompleted' in d:
                probe = json.loads(Path(j['acceptanceResult']['probePath']).read_text())
                expected_accepted = d['completed']
                check(('completed' not in probe or probe['completed'] is True) and j['acceptanceResult']['completed'] is expected_accepted and j['probeVerified'] is expected_accepted, 'inner-schema-and-outer-acceptance-preserved', r['name'])
                check(sha(Path(j['acceptanceResult']['probePath']).read_bytes()) == j['acceptanceResult']['probeSHA256'] and sum(x['ok'] is True for x in probe['results']) == observed[0] and sum(x['ok'] is False for x in probe['results']) == observed[1], 'ui-independent-original-probe-case-census', r['name'])
            if 'acceptanceCompleted' in d:
                wrapper = next(x for x in r['rawEvidence'] if 'wrapper-receipts' in x['path'])
                outer = json.loads((directory / wrapper['path']).read_text())
                check(j['completed'] is True and outer['acceptanceResult']['completed'] is False and outer['probeVerified'] is False and d['acceptanceCompleted'] is False, 'early-ui-attempted-is-not-accepted', r['name'])
            if 'directActualProbeBindings' in j:
                census = j['probeCensus']
                probe_results = Path(census['resultsPath'])
                check(sha(probe_results.read_bytes()) == census['resultsSha256'] and census['actualCases'] == len(census['cases']) and census['pass'] == sum(x['ok'] is True for x in census['cases']) and census['fail'] == sum(x['ok'] is False for x in census['cases']), 'scoped-live-original-probe-census', r['name'])
                for field in ['rawLog', 'originalCommandRawLog', 'innerOriginalGate']:
                    original_ref = j[field]
                    check(sha(Path(original_ref['path']).read_bytes()) == original_ref['sha256'], 'scoped-live-original-gate-log-hash', {'scope': r['name'], 'field': field})
                inner = json.loads(Path(j['innerOriginalGate']['path']).read_text())
                check(head_dirty(inner) == (r['testedHead'], '') and head_dirty(inner, True) == (r['testedHead'], '') and inner['execution']['exitCode'] == j['innerExitCode'] == observed[3], 'scoped-live-original-inner-gate-binding', r['name'])
                bindings = j['directActualProbeBindings']
                python_rows, node_rows, chrome_rows = [bindings[k] for k in ['probePython', 'ownedDriverNode', 'ownedMainChrome']]
                check(len(python_rows) == len(node_rows) == len(chrome_rows) == 1, 'scoped-live-distinct-owned-python-node-chrome', r['name'])
                if len(python_rows) == len(node_rows) == len(chrome_rows) == 1:
                    py, node, chrome = python_rows[0], node_rows[0], chrome_rows[0]
                    check(py['pid'] == bindings['innerGateExecutionPid'] == inner['execution']['pid'] and py['argv'] == j['probeCommand'], 'scoped-live-exact-probe-python-pid-argv', r['name'])
                    check(node['parent'] == py['pid'] and node['parentStartTicks'] == py['startTicks'] and chrome['parent'] == node['pid'] and chrome['parentStartTicks'] == node['startTicks'], 'scoped-live-direct-parent-start-ticks', r['name'])
                    check(py['sha256'] == j['before']['configuredExecutables']['python']['sha256'] and node['sha256'] == j['before']['configuredExecutables']['node']['sha256'] and chrome['exe'] == '/usr/lib/chromium/chromium' and re.fullmatch('[0-9a-f]{64}', chrome['sha256']) is not None, 'scoped-live-executable-role-hashes', r['name'])
                runtime = j['before']['runtime']
                native = j['before']['nativeActualChildren']
                native_identity = lambda rows: [{k: v for k, v in row.items() if k != 'observedAt'} for row in rows]
                check(runtime == j['after']['runtime'] and runtime['fresh'] is True and len(native) == 1 and native_identity(native) == native_identity(j['after']['nativeActualChildren']) and native[0]['parent'] == runtime['pid'], 'scoped-live-native-runtime-session-stable', r['name'])
                check(j['before']['executionFiles'] == j['after']['executionFiles'], 'scoped-live-source-original-before-after', r['name'])
                all_scope_refs = r['rawEvidence'] + m['historyReviewsAndExecutorSources']
                published_original_hashes = {x.get('originalSha256') for x in all_scope_refs}
                script_sources = [(path, digest) for path, digest in j['before']['executionFiles'].items() if path.startswith('/workspace/') and Path(path).suffix in ['.py', '.js', '.cjs']]
                check(all(digest in published_original_hashes for _, digest in script_sources), 'scoped-live-all-declared-script-sources-readable', {'scope': r['name'], 'sources': script_sources})
                for stage in ['before', 'after']:
                    check(len(pub[stage]['executionFiles']) == len(j[stage]['executionFiles']), 'scoped-public-source-map-no-key-collision-loss', {'scope': r['name'], 'stage': stage, 'originalEntries': len(j[stage]['executionFiles']), 'publicEntries': len(pub[stage]['executionFiles']), 'detail': 'Distinct absolute path keys collapsed by projection; a fresh collision-safe publication supplement is required.'})
                if r['name'] == 'cross-b-0b37-old-entry-incomplete':
                    held = [x for x in census['cases'] if x['ok'] is False]
                    check(len(held) == 4 and all('#workSurf' in x['harnessError'] and 'element is not visible' in x['harnessError'] for x in held) and census['completed'] is False, 'cross-b-old-navigation-held-oracle-unreached', r['name'])
            round_reports.append({'bundle': bundle, 'name': r['name'], 'testedHead': r['testedHead'], 'dirty': False, 'originalReceipt': str(receipt), 'originalReceiptSha256': sha(receipt.read_bytes()), 'observedIndependentResult': list(observed), 'declaredResult': d, 'originalLog': str(log) if log else None})
            for source_ref in [x for x in r['rawEvidence'] if x.get('artifactRelativePath', '').startswith('executed-harness-sources/geometry-web/')]:
                relative = source_ref['artifactRelativePath'][len('executed-harness-sources/'):]
                target = r['testedHead'] + ':' + relative
                if target not in git_source_cache:
                    result = subprocess.run(['git', 'show', target], cwd=REPO, capture_output=True)
                    git_source_cache[target] = (result.returncode, len(result.stdout), sha(result.stdout))
                check(git_source_cache[target] == (0, source_ref['originalBytes'], source_ref['originalSha256']), 'integration-snapshot-actual-git-source', {'scope': r['name'], 'path': relative})
                before_source = j['before'].get('sourceSha256', {}).get(relative)
                after_source = j['after'].get('sourceSha256', {}).get(relative)
                if before_source is not None:
                    check(before_source == after_source == source_ref['originalSha256'], 'integration-snapshot-measured-before-after', {'scope': r['name'], 'path': relative})
            snapshots = [x for x in r['rawEvidence'] if x.get('artifactRelativePath') == 'executed-sources/manifest.json']
            for snapshot_ref in snapshots:
                snapshot = json.loads((directory / snapshot_ref['path']).read_text())
                check(snapshot['fullSHA'] == r['testedHead'] and snapshot['receiptSHA256'] == r['originalReceiptSha256'], 'snapshot-measured-receipt-sha-binding', r['name'])
                entries = snapshot['entries']
                snapshot_entries[r['name']] = len(entries)
                refs = {x.get('artifactRelativePath'): x for x in r['rawEvidence'] if x.get('artifactRelativePath', '').startswith('executed-sources/')}
                check(len(entries) == len({x['path'] for x in entries}), 'snapshot-distinct-source-census', r['name'])
                for entry in entries:
                    source_ref = refs.get('executed-sources/' + entry['path'], {})
                    check(source_ref.get('originalSha256') == entry['sha256'] and source_ref.get('originalBytes') == entry['bytes'], 'snapshot-entry-original-source-ref', {'scope': r['name'], 'path': entry['path']})
                    if entry['origin'].startswith('git show '):
                        target = entry['origin'][len('git show '):]
                        check(target == r['testedHead'] + ':' + entry['path'], 'snapshot-source-exact-sha-origin', {'scope': r['name'], 'path': entry['path']})
                        if target not in git_source_cache:
                            result = subprocess.run(['git', 'show', target], cwd=REPO, capture_output=True)
                            git_source_cache[target] = (result.returncode, len(result.stdout), sha(result.stdout))
                        check(git_source_cache[target] == (0, entry['bytes'], entry['sha256']), 'snapshot-entry-actual-git-bytes', {'scope': r['name'], 'path': entry['path']})
                        if entry['path'] in j['before'].get('sources', {}):
                            check(j['before']['sources'][entry['path']] == j['after']['sources'][entry['path']] == entry['sha256'], 'snapshot-entry-measured-before-after', {'scope': r['name'], 'path': entry['path']})
                    elif entry['path'].startswith('approved-source-override/'):
                        check(entry['sha256'] == j['testSourceProvenance']['executedProbeSHA256'] and j['testSourceProvenance']['sourceOverride'] is True, 'snapshot-actual-approved-oracle-override', r['name'])
                    elif entry['path'].startswith('run_ui_gate'):
                        check(entry['sha256'] == j['before']['runnerSHA256'] == j['after']['runnerSHA256'], 'snapshot-measured-wrapper-identity', r['name'])
        for ref in m['fullTestedCommitSourceCopies']:
            result = subprocess.run(['git', 'show', ref['sourceHead'] + ':' + ref['repositoryPath']], cwd=REPO, capture_output=True)
            check(result.returncode == 0 and sha(result.stdout) == ref['originalSha256'], 'exact-git-source-original', {'bundle': bundle, 'sourceHead': ref['sourceHead'], 'path': ref['repositoryPath']})
            check(ref['publishedCopyWasExecuted'] is False, 'publication-not-executed-source', ref['path'])
            source_count += 1
    # Every ref is independently resolved to an actual retained original by hash.
    seen = set()
    for bundle, ref in all_refs:
        key = (bundle, ref['path'], ref.get('originalSha256'))
        if key in seen:
            continue
        seen.add(key)
        public = BASE / bundle / ref['path']
        digest = ref.get('originalSha256')
        matches = by_hash.get(digest, [])
        check(bool(matches), 'retained-original-found', {'bundle': bundle, 'path': ref['path'], 'originalSha256': digest})
        if not matches:
            continue
        original = matches[0]
        ref_count += 1
        raw = original.read_bytes()
        data = public.read_bytes()
        check('originalBytes' not in ref or len(raw) == ref['originalBytes'], 'original-byte-size', {'bundle': bundle, 'path': ref['path']})
        if public.suffix in ['.zip', '.gcanvas']:
            zip_summary['archives'] += 1
            zip_summary['maxBytes'] = max(zip_summary['maxBytes'], len(data))
            check(len(data) <= 10 * 1024 * 1024, 'bounded-trace-archive', ref['path'])
            with zipfile.ZipFile(original) as a, zipfile.ZipFile(public) as b:
                check(a.namelist() == b.namelist(), 'zip-entry-census', ref['path'])
                entry_meta = {x['entry']: x for x in ref.get('traceEntryProjections', [])}
                changed = set()
                for name in a.namelist():
                    check(not name.startswith('/') and '..' not in Path(name).parts, 'zip-safe-entry-path', {'archive': ref['path'], 'entry': name})
                    old, new = a.read(name), b.read(name)
                    try:
                        text = old.decode('utf-8')
                    except UnicodeDecodeError:
                        zip_summary['binaryEntries'] += 1
                        check(old == new, 'zip-binary-original-bytes', {'archive': ref['path'], 'entry': name})
                        continue
                    check(not private_path(new.decode('utf-8')), 'zip-public-private-path', {'archive': ref['path'], 'entry': name})
                    check(not any(x in new.decode('utf-8') for x in ['"owner_thread_id":', '"PRIVATE_QUEUE_DATABASE":', 'closure-evidence/queue/']), 'zip-no-private-payload', {'archive': ref['path'], 'entry': name})
                    structured_trace = name.endswith(('.trace', '.network', '.stacks', '.json', '.jsonl'))
                    if structured_trace:
                        try:
                            if name.endswith(('.trace', '.network', '.jsonl')):
                                old_rows = [strict_json(line) for line in text.splitlines() if line.strip()]
                                new_rows = [strict_json(line) for line in new.decode().splitlines() if line.strip()]
                                check(new_rows == [project(row) for row in old_rows], 'trace-jsonl-all-original-values-preserved', {'archive': ref['path'], 'entry': name, 'rows': len(old_rows)})
                            else:
                                check(strict_json(new.decode()) == project(strict_json(text)), 'trace-stacks-resource-json-readable-values-preserved', {'archive': ref['path'], 'entry': name})
                        except ValueError as error:
                            check(False, 'trace-structured-json-readable', {'archive': ref['path'], 'entry': name, 'error': str(error)})
                    if old == new:
                        zip_summary['unchangedEntries'] += 1
                    else:
                        zip_summary['projectedEntries'] += 1
                        changed.add(name)
                        if not structured_trace:
                            check(new == redact(text).encode(), 'zip-path-only-projection', {'archive': ref['path'], 'entry': name})
                        meta = entry_meta.get(name, {})
                        check(meta == {'entry': name, 'originalBytes': len(old), 'originalSha256': sha(old), 'publicBytes': len(new), 'publicSha256': sha(new)}, 'zip-entry-original-public-hashes', {'archive': ref['path'], 'entry': name})
                check(changed == set(entry_meta), 'zip-changed-entry-census', ref['path'])
            if public.suffix == '.gcanvas':
                check(raw == data, 'gcanvas-original-whole-bytes', ref['path'])
        elif public.suffix == '.json' and 'wrapper-receipts' not in ref['path']:
            check(strict_json(data.decode()) == project(strict_json(raw.decode())), 'json-path-only-one-to-one-original-values', {'bundle': bundle, 'path': ref['path']})
            if 'projectionDictionaryKeyAudit' in ref:
                check(ref['projectionDictionaryKeyAudit'] == dictionary_audit(strict_json(raw.decode())), 'artifact-all-original-key-audit', ref['path'])
        elif public.suffix == '.jsonl':
            old_rows = [strict_json(line) for line in raw.decode().splitlines() if line.strip()]
            new_rows = [strict_json(line) for line in data.decode().splitlines() if line.strip()]
            check(new_rows == [project(row) for row in old_rows], 'jsonl-path-only-one-to-one-original-values', {'bundle': bundle, 'path': ref['path'], 'rows': len(old_rows)})
        elif ref.get('byteIdenticalOriginal') is True:
            check(raw == data, 'byte-identical-original', {'bundle': bundle, 'path': ref['path']})
        elif 'wrapper-receipts' in ref['path']:
            obj = json.loads(data)
            meta = obj.pop('publicProjection')
            check(obj == project(json.loads(raw)) and meta['originalSha256'] == digest, 'wrapper-path-only-projection', ref['path'])
        else:
            check(data.decode('utf-8') == redact(raw.decode('utf-8')), 'text-path-only-projection', {'bundle': bundle, 'path': ref['path']})
        if public.suffix == '.scene':
            world_count += 1
            check(raw == data and ref.get('byteIdenticalOriginal') is True, 'world-original-bytes', {'bundle': bundle, 'path': ref['path']})
        if public.suffix == '.png':
            check(len(data) <= 16384 and raw == data, 'small-synthetic-png', ref['path'])
    # Independently scoped product results and actual source provenance.
    current = manifests[current_bundle]
    directory = BASE / current_bundle
    scopes = {x['name']: x for x in current['rounds']}
    check(set(scopes) == set(EXPECTED_RESULTS), 'eleven-independent-scopes-no-sum', list(scopes))
    check(all(x['testedHead'] == '243326b512896ace70e068f62c8f3d6397f6000d' and x['dirty'] is False for x in scopes.values()), 'all-actual-scopes-bound-clean-243', None)
    earlier_expected = {'ui-single-room-prior-public-v4': '3f2abb29f759de73c6e4c72323ead0c42aab763ca4e6391f63d41f9802ae8e9d', 'ui-single-room-640-public-v4': '64a0d10728631d4e9ccdac5c4051f666a95e9104a6159e43eac72950884f0522', 'ui-single-room-0b37-failed-public-v5': '389b1fdf3e0d8639bf192f2087f0d49de5a565799229598dc958132bdbcdaa97'}
    check({x['name']: x['manifestSha256'] for x in current['earlierBundles']} == earlier_expected and all(sha((BASE / name / 'manifest.json').read_bytes()) == value for name, value in earlier_expected.items()), 'prior-accepted-pointers-immutable', earlier_expected)
    space_receipt = json.loads(Path(originals['full-space-243-complete-declared-five']).read_text())
    space = space_receipt['evidence']['canonicalResult']
    space_log = Path(space_receipt['log']['path'])
    space_rows = [strict_json(line[len('SPACE_RESULT '):]) for line in space_log.read_text().splitlines() if line.startswith('SPACE_RESULT ')]
    declared_space = scopes['full-space-243-complete-declared-five']['declaredResult']
    check(space_rows == [space] and space['scope']['included'] == declared_space['included'] and space['scope']['omitted'] == declared_space['omitted'] and space['scope']['filters'] == [] and space['completed'] is True and not space['completenessProblems'], 'full-space-declared-five-canonical-only', declared_space)
    cdp_receipt = json.loads(Path(originals['full-cdp-243-terminal-failed']).read_text())
    cdp_log = Path(cdp_receipt['log']['path'])
    cdp_rows = [strict_json(line[len('CDP_RESULT '):]) for line in cdp_log.read_text().splitlines() if line.startswith('CDP_RESULT ')]
    check(len(cdp_rows) == 1 and cdp_rows[0]['completed'] is False and cdp_rows[0]['scope']['mode'] == 'full' and cdp_rows[0]['scope']['filters'] == [] and scopes['full-cdp-243-terminal-failed']['declaredResult']['goldenCompared'] is False and cdp_receipt['execution']['exitCode'] == 1, 'full-cdp-terminal-failure-no-golden', cdp_rows)
    for name in ['full-space-243-complete-declared-five', 'full-cdp-243-terminal-failed']:
        receipt = json.loads(Path(originals[name]).read_text())
        processes = receipt['executionIdentity']['liveBinding']['processes']
        chrome = [x for x in processes if x['exe'] == '/usr/lib/chromium/chromium']
        node = [x for x in processes if 'Node' in x['role']]
        check(len(chrome) == len(node) == 1 and chrome[0]['executableMagicHex'] == node[0]['executableMagicHex'] == '7f454c46' and node[0]['pid'] == receipt['execution']['pid'] and all(re.fullmatch('[0-9a-f]{64}', x['sha256']) for x in chrome + node), 'integration-actual-owned-chrome-elf-node-identity', name)
    for name, expected_override, expected_hash in [('ui123-four-v4-failed-243', True, 'a62999473b6ff6076e414a48d5950135998f49f653fbcfbc70c20b25aa61bd24'), ('ui123-four-v5-complete-243', True, '69f30662c7eac4588b21a318cd8983ec8b85cc21a95b7cc99c7b7aab2bb77798'), ('room54-original-ten-negatives-243', False, None)]:
        receipt = json.loads(Path(originals[name]).read_text())
        provenance = receipt['testSourceProvenance']
        check(provenance['sourceOverride'] is expected_override and (expected_hash is None or provenance['executedProbeSHA256'] == expected_hash), 'formal-vs-reviewed-source-override-identity', {'name': name, 'provenance': provenance})
        identity = receipt['executionIdentity']
        check(identity['node']['pid'] == receipt['execution']['pid'] and identity['browser']['executable'] == '/usr/lib/chromium/chromium' and all(re.fullmatch('[0-9a-f]{64}', identity[x]['sha256']) for x in ['node', 'browser']), 'ui-actual-node-chrome-executable-identity', name)
    room_receipt = json.loads(Path(originals['room54-original-ten-negatives-243']).read_text())
    room = json.loads(Path(room_receipt['acceptanceResult']['probePath']).read_text())
    room_measured = [{'scenario': x['scenario'], 'candidate': x['candidate']['actions'], 'manual': x['manual']['actions'], 'protocol': x['protocol']} for x in room['measurements']]
    check(len(room_measured) == 6 and sorted((x['candidate'], x['manual']) for x in room_measured) == [(12, 16), (12, 16), (14, 20), (14, 20), (16, 24), (16, 24)] and all(x['protocol'] == 'room-direct-row-dimensions/1' for x in room_measured), 'room-cost-same-declared-protocol', room_measured)
    # Exact source ledger is checked against original measured keys, not the
    # current dirty worktree. Every association remains distinct after projection.
    ledger = strict_json((BASE / 'ui-243-source-ledger.json').read_text())
    ledger_public = strict_json((directory / 'executors/actual-source-ledger.public.json').read_text())
    check(ledger_public == project(ledger), 'executed-source-ledger-key-value-associations', None)
    measured_sources = {}
    for name in EXPECTED_RESULTS:
        receipt = json.loads(Path(originals[name]).read_text())
        for stage in ['before', 'after']:
            for key, value in receipt[stage].get('executionFiles', {}).items():
                if key.startswith('/workspace/') and Path(key).suffix in ['.py', '.js', '.cjs', '.c', '.h', '.inc', '.css', '.html', '.json', '.jsonl']:
                    measured_sources.setdefault(key, set()).add(value)
    check(len(ledger['entries']) == 175 and len({x['originalPath'] for x in ledger['entries']}) == 175, 'source-ledger-175-distinct-associations', None)
    for entry in ledger['entries']:
        source = Path(entry['retainedSourcePath'])
        retained_hash = sha(source.read_bytes())
        check(entry['originalPathSha256'] == sha(entry['originalPath'].encode()) and retained_hash == entry['executedSha256'] and entry['executedSha256'] in measured_sources.get(entry['originalPath'], set()), 'ledger-retained-original-source-execution-binding', {'entry': entry['originalPath'], 'origin': entry['retentionOrigin']})
        published = directory / entry['publicPath']
        check(published.read_text() == redact(source.read_text()), 'ledger-original-vs-public-source-bytes', entry['publicPath'])
        if 'git show' in entry['retentionOrigin'] or 'recover' in entry['retentionOrigin'].lower():
            relative = entry['originalPath'].split('<workspace-path>', 1)[-1]
            recovered = subprocess.run(['git', 'show', ledger['testedHead'] + ':' + relative], cwd=REPO, capture_output=True)
            check(recovered.returncode == 0 and sha(recovered.stdout) == retained_hash and entry['retainedSourcePath'] != entry['originalPath'], 'ledger-dirty-source-exact-git-recovery', entry)
    # Publisher execution is observed separately and never counted as a product run.
    publisher_dir = BASE / (current_bundle + '-publisher-execution')
    publisher = strict_json((publisher_dir / 'receipt.json').read_text())
    check(publisher['exitCode'] == 0 and publisher['completed'] is True and publisher['sourceBefore'] == publisher['sourceAfter'] and publisher['productTestExecuted'] is False and publisher['repositoryOrRemoteWrites'] is False and publisher['manifest']['sha256'] == EXPECTED_MANIFESTS[current_bundle], 'publisher-actual-exit-source-closure-not-product', None)
    for name, digest in publisher['sourceBefore'].items():
        check(sha((BASE / name).read_bytes()) == digest, 'publisher-sealed-source-config-identity', name)
    actual_publisher = publisher['actualPublisherPython']
    check(sha(Path(actual_publisher['executablePath']).read_bytes()) == actual_publisher['executableSha256'] and actual_publisher['commandLine'].strip() == ' '.join(publisher['command']) and int(actual_publisher['procStat'].split(' ', 1)[0]) == actual_publisher['pid'], 'publisher-actual-python-process-executable', actual_publisher['pid'])
    check(sha(Path(publisher['rawLog']['path']).read_bytes()) == publisher['rawLog']['sha256'] and Path(publisher['rawLog']['path']).stat().st_size == publisher['rawLog']['bytes'], 'publisher-original-command-log-identity', publisher['rawLog'])
    readme = (directory / 'README.md').read_text()
    check(all(text in readme for text in ['P75', 'still requires diagnosis', 'not final integration acceptance', '327 / 0', 'sourceOverride', '273 / 0', 'no sourceOverride', '228 / 0', 'timber-source-guards omitted', 'seven original Windows logs are not received', 'CI was **not executed**', 'same execution actor', 'not an independent review', 'proof', 'not browser product tests']), 'readme-scope-source-override-failures-unknown-limits', None)
    for name, expected_counts in [('supplementary-validation-243-supplement-v5.json', (51, 1, False)), ('supplementary-validation-243-supplement-v5-census-corrected.json', (52, 0, True)), ('supplementary-validation-243-room54.json', (113, 0, True))]:
        proof = strict_json((directory / 'scope-review' / name).read_text())
        counts = (sum(x['ok'] is True for x in proof['checks']), sum(x['ok'] is False for x in proof['checks']), proof['ok'])
        check(counts == expected_counts and proof['browserExecuted'] is False and proof['nativeExecuted'] is False and proof['repoWritten'] is False and proof['sourceSHA'] == '243326b512896ace70e068f62c8f3d6397f6000d' and proof['dirty'] == '', 'original-and-corrected-independent-artifact-proofs-not-product', {'proof': name, 'counts': counts})
    after = git_state()
    # Parent may advance candidate while this evidence-only QA runs. Historical
    # tested SHAs come from their own original receipts, never current checkout.
    inventories = []
    for start in range(0, len(checks), 2000):
        inventory = out / ('artifact-checks-%03d.jsonl' % (start // 2000 + 1))
        inventory.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in checks[start:start + 2000]))
        check_size = inventory.stat().st_size
        assert check_size < 10 * 1024 * 1024
        inventories.append({'path': str(inventory), 'bytes': check_size, 'sha256': sha(inventory.read_bytes()), 'entries': len(checks[start:start + 2000])})
    final = {'schema': 'geometry-public-evidence-independent-review/1', 'actor': ACTOR, 'reviewedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'accepted' if not findings else 'findings', 'scope': 'Read-only publication/evidence QA; no browser/native/service/product tests executed; checks are never added to product test totals.', 'reviewExecutionIdentity': execution_identity, 'repositoryObservedBefore': before, 'repositoryObservedAfter': after, 'repositoryMutationByThisReviewer': False, 'manifests': EXPECTED_MANIFESTS, 'publicFilesVerified': {name: len(m['publicFiles']) for name, m in manifests.items()}, 'independentScopes': round_reports, 'distinctOriginalRefsVerified': ref_count, 'sourceCopiesCheckedAgainstExactGit': source_count, 'executedSourceSnapshotEntries': snapshot_entries, 'snapshotGitSourcesIndependentlyVerified': len(git_source_cache), 'worldFilesCheckedByteIdentical': world_count, 'archiveEntryReview': zip_summary, 'checkCount': len(checks), 'failedCheckCount': len(findings), 'findings': findings, 'checkInventories': inventories, 'releaseApproved': False, 'limits': ['Product behavior, actual served app.js response bytes, historical unknown executable identities, Windows raw originals and private queue state are not established by this QA.', 'All original results remain independently scoped; no product count aggregation or rerun/relabel.', 'Root is sole repository/GitHub writer; this review writes scratch only.']}
    (out / 'report.json').write_text(json.dumps(final, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'status': final['status'], 'checkCount': len(checks), 'failedCheckCount': len(findings), 'findings': findings[:20], 'publicFilesVerified': final['publicFilesVerified'], 'archives': zip_summary, 'originalRefs': ref_count, 'worlds': world_count, 'sources': source_count}, ensure_ascii=False))
    return 0 if not findings else 1


if __name__ == '__main__':
    sys.exit(main())
