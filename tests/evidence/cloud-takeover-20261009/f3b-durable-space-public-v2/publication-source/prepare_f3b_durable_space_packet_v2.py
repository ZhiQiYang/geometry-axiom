"""Fresh scratch-only public packaging of the sealed durable standalone Space run.

No product, native, browser, service, repository or remote command is executed.
The exact v8 publication implementation is imported, with its unrelated default
source-reference loop explicitly skipped to preserve existing saved snapshots.
Own exact-f3 Git references and all actual captured sources are supplied instead.
"""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SCRATCH = Path('<workspace-path>')
REPO = Path('<workspace-path>')
HEAD = 'f3b8285729b42cd22451c98cba1e2ec4514517f3'
GATE = SCRATCH / 'geometry-root-f3b82857-durable-full-space-gate'
LIFE = SCRATCH / 'geometry-root-f3b82857-durable-full-space-lifecycle'
DETACHED = SCRATCH / 'geometry-root-f3b82857-durable-full-space-detached-launch'
VERIFY = SCRATCH / 'geometry-ui-verification'
PREP = VERIFY / 'f3b-source-and-census-preparation'
HARNESS = SCRATCH / 'geometry-takeover-evidence-harness'
PREPARER = HERE / 'prepare_ui_history_packet_v8.py'
spec = importlib.util.spec_from_file_location('durable_space_publication_v8', PREPARER)
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def write_new(path, value, public=False):
    assert not path.exists(), path
    path.parent.mkdir(parents=True, exist_ok=True)
    if public:
        value = P.collision_safe_projection(value)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git_bytes(relative):
    return subprocess.check_output(['git', 'show', HEAD + ':' + relative], cwd=REPO)


def public_source_entry(path, public_path, role, relative=None, captured=False):
    original = path.read_bytes()
    text = original.decode()
    projected = P.p.redact_text(text).encode() if P.p.private(text) else original
    entry = {'sourceHead': HEAD, 'repositoryPath': relative,
             'originalSHA256': hashlib.sha256(original).hexdigest(),
             'originalBytes': len(original), 'publicSHA256': hashlib.sha256(projected).hexdigest(),
             'publicBytes': len(projected), 'publicPath': public_path,
             'role': role, 'originalExecutionSnapshotCaptured': captured,
             'publishedCopyWasExecuted': False}
    if captured:
        entry['recordedBeforeAndAfterSHA256'] = entry['originalSHA256']
        entry['exactGitObjectMatchesCapturedBytes'] = True
    return entry


def main():
    version = 1
    names = ['public', 'config', 'extra', 'metadata', 'README', 'source-reference',
             'adapter', 'package-build', 'packager-selfcheck', 'build.stdout.raw', 'build.stderr.raw']
    suffixes = {'public': '', 'source-reference': '', 'README': '.md', 'adapter': '.py',
                'build.stdout.raw': '.log', 'build.stderr.raw': '.log'}
    while any((HERE / ('f3b-durable-space-' + name + '-v' + str(version) + suffixes.get(name, '.json'))).exists() for name in names):
        version += 1
    paths = {name: HERE / ('f3b-durable-space-' + name + '-v' + str(version) + suffixes.get(name, '.json')) for name in names}
    output = paths['public']
    receipt = load(GATE / 'receipt.json')
    terminal = load(LIFE / 'terminal.json')
    stop = load(LIFE / 'owned-stop/terminal-receipt.json')
    launch = load(DETACHED / 'launch.json')
    review_path = VERIFY / 'supplementary-validation-f3b-durable-full-space.json'
    addendum_path = VERIFY / 'supplementary-validation-f3b-durable-space-launch-addendum.json'
    review, addendum = load(review_path), load(addendum_path)
    assert sha(review_path) == '1cadc0c1a180ab102af416479d363da8d200c30a8d11e6cf1a3c22b35005d0f2'
    assert sha(addendum_path) == 'b23bda2c19ba4fb7c6c8e3564763aaf842dc97432aad6cb2ff9ddb524efb87a6'
    assert receipt['command'] == ['node', 'geometry-web/space_model_test.js']
    assert receipt['before']['git']['head'] == receipt['after']['git']['head'] == HEAD
    assert receipt['before']['git']['status'] == receipt['after']['git']['status'] == ''
    assert receipt['before']['sourceSha256'] == receipt['after']['sourceSha256']
    canonical = receipt['evidence']['canonicalResult']
    assert (canonical['passed'], canonical['failed'], canonical['completed']) == (228, 0, True)
    assert receipt['executionVerified'] is True and receipt['evidence']['completionVerified'] is True
    assert receipt['execution']['exitCode'] == receipt['gateExitCode'] == terminal['actualGateExitCode'] == terminal['stopExitCode'] == stop['exitCode'] == 0
    assert launch['launchExitCode'] == 0
    assert launch['actualControllerPID'] == launch['actualControllerPGID'] == launch['actualControllerSID'] == 280637
    assert addendum['currentControllerKernelObservation']['actualControllerExitFromKernel'] == 0
    assert addendum['currentControllerKernelObservation']['state'] == 'Z'
    assert review['exitCode'] == addendum['exitCode'] == 0
    assert len(review['integrityChecks']) == 39 and all(review['integrityChecks'].values())
    assert len(review['acceptanceChecks']) == 7 and all(review['acceptanceChecks'].values())
    assert len(addendum['checks']) == 19 and all(addendum['checks'].values())
    expected_groups = {'setup': 2, 'space-height-library': 112, 'projection-lifecycle': 18,
                       'projection-placement': 36, 'font-layout': 19, 'space-flow': 39, 'browser-health': 2}
    assert set(canonical['groups']) == set(expected_groups)
    assert sum(expected_groups.values()) == 228
    for name, count in expected_groups.items():
        assert canonical['groups'][name] == {'expected': count, 'passed': count, 'failed': 0, 'completed': True}
    assert canonical['scope']['filters'] == []
    assert canonical['scope']['included'] == ['space-height-library', 'projection-lifecycle', 'projection-placement', 'font-layout', 'space-flow']
    assert canonical['scope']['omitted'] == ['timber-material', 'timber-source-guards']
    assert sha(GATE / 'command.log') == receipt['log']['sha256'] == '1764f15915c25c253dd1c44ef57b3ffa0ac6ca9f4a6ea5d8f7a7b1e3dc38bf82'
    for recorded in terminal['rawFiles']:
        original = LIFE / recorded['path']
        assert sha(original) == recorded['sha256'] and original.stat().st_size == recorded['bytes']
    for recorded in stop['rawFiles']:
        original = LIFE / 'owned-stop' / recorded['path']
        assert sha(original) == recorded['sha256'] and original.stat().st_size == recorded['bytes']

    config = [{'name': 'f3b-durable-standalone-space-completed', 'head': HEAD,
               'receipt': str(GATE / 'receipt.json'),
               'scope': 'Original canonical standalone node geometry-web/space_model_test.js with no filters: five declared groups plus setup/browser-health, 228 assertions; two timber groups omitted. No all-Space, all43, full CDP or golden acceptance.',
               'result': {'pass': 228, 'fail': 0, 'completed': True, 'actualExitCode': 0,
                          'gateExitCode': 0, 'executionVerified': True, 'groups': expected_groups,
                          'goldenCompared': False, 'allSpaceAcceptance': False},
               'logs': [str(GATE / 'command.log')], 'artifacts': [str(GATE)],
               'canonicalLogPrefix': 'SPACE_RESULT '}]
    extras = []
    bindings = []
    sources = []

    def add(path, destination, purpose, expected=None):
        path = Path(path)
        assert path.exists(), path
        if expected:
            assert path.is_file() and sha(path) == expected, (path, expected)
        extras.append({'path': str(path), 'destination': destination, 'purpose': purpose})
        if path.is_file():
            bindings.append({'originalPathLabel': str(path), 'originalPathSHA256': hashlib.sha256(str(path).encode()).hexdigest(),
                             'originalBasename': path.name, 'originalSHA256': sha(path),
                             'originalBytes': path.stat().st_size, 'publicPath': destination,
                             'publishedCopyWasExecuted': False})

    add(LIFE, 'original-owned-lifecycle', 'Original complete Space lifecycle started/ready/terminal, exact service/gate/stop commands and raw streams; no product execution by this packager.')
    add(DETACHED, 'original-detached-launch', 'Original detached launch receipt and final controller streams. Launch-time stream hashes attest then-empty files; final stream hashes remain separately recorded.')
    for parent, destination in [(LIFE, 'original-owned-lifecycle'), (DETACHED, 'original-detached-launch')]:
        for original in sorted(parent.rglob('*.raw')):
            add(original, destination + '/' + original.relative_to(parent).as_posix(), 'Actual retained process stat raw bytes. Explicit inclusion because v8 tree collector excludes .raw; zombie observations retain their original Z state.')
    add(review_path, 'independent-space-review/review.public.json', 'Original different-actor readonly Space identity/source/census review: 39 integrity and 7 acceptance checks, never product assertions.', '1cadc0c1a180ab102af416479d363da8d200c30a8d11e6cf1a3c22b35005d0f2')
    add(Path(review['rawReviewLog']['path']), 'independent-space-review/command.raw.public.log', 'Original actual readonly reviewer raw output, actual exit0; no browser/service/product execution.', review['rawReviewLog']['sha256'])
    add(addendum_path, 'independent-launch-addendum/review.public.json', 'Original different-actor launch/source/AST/controller-kernel addendum:19 metadata checks; its retained controller kernel wait status0 proves exit0, while original launch final exit remains null.', 'b23bda2c19ba4fb7c6c8e3564763aaf842dc97432aad6cb2ff9ddb524efb87a6')
    add(addendum_path.with_suffix('.raw.log'), 'independent-launch-addendum/command.raw.public.log', 'Original actual launch-addendum raw output and actual exit0; no product count.', addendum['rawReviewLogSHA256'])
    executor_sources = [
        (HARNESS / 'run_full_space_identity.py', receipt['before']['runnerSha256']),
        (HARNESS / 'space_execution_identity.py', receipt['before']['identityObserverSha256']),
        (HARNESS / 'cdp_execution_identity_v2.py', receipt['before']['identityProcessSamplerSha256']),
        (HARNESS / 'full-launch-adapters/sandbox-launch.cjs', receipt['before']['launchAdapterSha256']['sandbox-launch.cjs']),
        (HARNESS / 'full-launch-adapters/sitecustomize.py', receipt['before']['launchAdapterSha256']['sitecustomize.py']),
        (SCRATCH / 'geometry-stage-launch.py', terminal['launchSHA256']),
        (SCRATCH / 'geometry-stage-stop.py', stop['helperSHA256']),
        (SCRATCH / 'geometry-owned-integration-lifecycle-f3b-v2.py', terminal['controllerSHA256']),
        (SCRATCH / 'geometry-stop-with-terminal-receipt-f3b.py', stop['wrapperSHA256']),
        (SCRATCH / 'geometry-launch-detached-owned-integration-f3b.py', launch['launcherSourceSHA256']),
        (PREP / 'validate_f3b_full_integration.py', review['reviewExecutor']['scriptSHA256']),
        (PREP / 'validate_f3b_durable_integration.py', load(PREP / 'durable-census-preparation-review.json')['sourceFiles'][str(PREP / 'validate_f3b_durable_integration.py')]),
        (PREP / 'prepare_durable_full_census.py', addendum['sourceHashes'][str(PREP / 'prepare_durable_full_census.py')]),
        (PREP / 'review_durable_space_launch_and_census.py', addendum['sourceHashes'][str(PREP / 'review_durable_space_launch_and_census.py')]),
    ]
    for original, digest in executor_sources:
        destination = 'executor-source-bytes/' + original.name
        add(original, destination, 'Hash-bound original execution or different-actor review source bytes; public projection never executed. Runtime wrapper snapshot directory is absent; same-hash retained originals are supplied with this limit.', digest)
        sources.append(public_source_entry(original, destination, 'recorded scratch executor/reviewer source'))
    add(PREP / 'durable-census-preparation-review.json', 'independent-launch-addendum/preparation-review.public.json', 'Original separate preparation check report keeps its literal-search false result; later AST correction in launch addendum remains separate and no static check is product coverage.', addendum['sourceHashes'][str(PREP / 'durable-census-preparation-review.json')])
    add(PREP / 'census-f3b-derivation.patch', 'independent-launch-addendum/census-derivation.patch', 'Retained source-only preparation derivation; original Space review executed validate_f3b_full_integration.py, not the separately derived durable validator.')

    captured = receipt['before']['sourceSha256']
    snapshots = sorted(p for p in (GATE / 'executed-harness-sources').rglob('*') if p.is_file())
    assert len(snapshots) == len(captured) == 125
    assert {p.relative_to(GATE / 'executed-harness-sources').as_posix() for p in snapshots} == set(captured)
    for relative, digest in captured.items():
        original = GATE / 'executed-harness-sources' / relative
        assert sha(original) == digest and hashlib.sha256(git_bytes(relative)).hexdigest() == digest
        sources.append(public_source_entry(original, 'executed-source-bytes/' + digest + '/' + original.name,
                                           'actual before/after hash-captured web source; separately matched exact frozen Git object', relative, True))

    # Recursively resolve every local require of the canonical Node command.
    node_closure = set()
    pending = ['geometry-web/space_model_test.js']
    while pending:
        relative = pending.pop()
        if relative in node_closure:
            continue
        node_closure.add(relative)
        text = git_bytes(relative).decode()
        for local in re.findall(r"require\(['\"](\.[^'\"]+)['\"]\)", text):
            dependency = (Path(relative).parent / local).as_posix()
            dependency = os.path.normpath(dependency).replace(os.sep, '/')
            pending.append(dependency)
    assert node_closure == {'geometry-web/space_model_test.js', 'geometry-web/cdp_confirmation_gate.js',
                            'geometry-web/async_reply_ui_test.js', 'geometry-web/save_reopen_synthetic_test.js',
                            'geometry-web/cdp_evaluation.js', 'geometry-web/space_test_floor.js',
                            'geometry-web/vendor/fflate/umd/index.js'}
    helper_refs = ['tests/release_gate.py', 'tests/binaries.py', 'geometry-web/start_local.py',
                   'geometry-web/serve.py', 'geometry-web/runtime_version.py',
                   'geometry-web/native_context.py', 'geometry-web/feedback_store.py']
    references = []
    for relative in helper_refs + ['geometry-web/vendor/fflate/umd/index.js']:
        original = paths['source-reference'] / relative
        assert not original.exists()
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(git_bytes(relative))
        destination = 'committed-f3-source-reference/' + relative
        add(original, destination, 'Full exact-f3 Git object helper/dependency reference. Original receipt captured top-level web JS/CSS/HTML only; this is not an independently recorded original execution snapshot.', sha(original))
        references.append(public_source_entry(original, destination, 'exact frozen Git helper/dependency source reference', relative))

    adapter = '''"""Execute exact v8 scratch publisher with own complete Space source references.
Only the unrelated automatic common-source Git loop is skipped; it otherwise
rewrites existing saved snapshots. All copy/projection/receipt/collector code is
the original v8 implementation, with --only-extra and one Space config.
"""
from pathlib import Path
import importlib.util
import subprocess
from types import SimpleNamespace
path = Path(__file__).resolve().parent / 'prepare_ui_history_packet_v8.py'
spec = importlib.util.spec_from_file_location('space_publication_v8', path)
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)
skipped = []
def skip_unrelated_default_source_reference(command, **kwargs):
    assert command[:2] == ['git', 'show'], command
    skipped.append(command)
    return subprocess.CompletedProcess(command, 1, b'', b'Explicit scratch publication policy: unrelated default source references supplied separately; existing saved snapshots preserved.')
publisher.COMMON_SOURCES = []
publisher.subprocess = SimpleNamespace(run=skip_unrelated_default_source_reference)
publisher.main()
assert len(skipped) == 6
'''
    assert not paths['adapter'].exists()
    paths['adapter'].write_text(adapter)
    add(paths['adapter'], 'publication-source/space-v8-adapter.py', 'Actually executed scratch publication adapter; skips six unrelated default source references and preserves existing saved source snapshots. No product execution.')
    for original in [Path(__file__), HERE / 'execute_f3b_durable_space_packet_v2.py']:
        add(original, 'publication-source/' + original.name, 'Actual scratch publication source closure. Its public projected copy was never executed; original implementation hash remains recorded.')

    metadata = {
        'schema': 'geometry-f3b-durable-standalone-space-public/1',
        'scope': 'One original durable standalone Space command on clean f3b: five declared groups plus setup/browser-health; two timber groups omitted.',
        'preparerActor': '/root/delivery_closeout/restored_space_packet',
        'testedProductHead': HEAD, 'testedGitTree': receipt['before']['git']['tree'],
        'productGate': {'canonicalCommand': receipt['command'], 'originalReceiptSHA256': sha(GATE / 'receipt.json'),
                        'originalRawLogSHA256': sha(GATE / 'command.log'), 'actualNodeExitCode': 0,
                        'gateExitCode': 0, 'executionVerified': True, 'completed': True,
                        'passedAssertions': 228, 'failedAssertions': 0, 'groups': expected_groups,
                        'declaredIncludedGroups': canonical['scope']['included'], 'omittedGroups': canonical['scope']['omitted'],
                        'noScopeFilters': True, 'goldenCompared': False, 'allSpaceAcceptance': False,
                        'fullCDPAcceptance': False, 'all43Acceptance': False},
        'originalLifecycle': {'originalTerminalSHA256': sha(LIFE / 'terminal.json'), 'actualGateExitCode': 0,
                              'actualStopExitCode': 0, 'actualServiceExitAfterStop': terminal['actualServiceExitAfterStop'],
                              'serviceExitMeaning': 'Owned service terminated by exact stop SIGTERM; service process returncode -15 is separate from successful controller/gate/stop0.',
                              'actualControllerExitCode': 0, 'controllerExitProvenance': 'Retained different-actor kernel wait status0 in original launch addendum, separately supported by final controller stream and sys.exit(original gate0); original launch final controller exit remains null.',
                              'processObservations': stop['processObservations'], 'portObservation': stop['portObservation']},
        'detachedLaunch': {'originalReceiptSHA256': sha(DETACHED / 'launch.json'), 'actualLauncherExitCode': 0,
                           'actualControllerPID': 280637, 'actualControllerPGID': 280637, 'actualControllerSID': 280637,
                           'originalProductCompletionAtLaunch': 'pending', 'originalProductGateExitCodeAtLaunch': None,
                           'originalFinalControllerExitRecordedAtLaunch': None,
                           'launchTimeRawFileBindings': launch['rawFiles'],
                           'finalRetainedRawFileBindings': [{'path': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(DETACHED.iterdir()) if p.is_file()],
                           'launchTimeStreamsWereThenEmpty': True},
        'independentMetadataReviews': {
            'spaceCensus': {'originalReportSHA256': sha(review_path), 'actualReviewerExitCode': 0,
                            'integrityChecks': 39, 'acceptanceChecks': 7, 'passedRawReviewLines': 46,
                            'originalRawReviewSHA256': review['rawReviewLog']['sha256'],
                            'reviewExecutor': review['reviewExecutor'], 'countsAreProductAssertions': False},
            'launchAddendum': {'originalReportSHA256': sha(addendum_path), 'actualReviewerExitCode': 0,
                               'metadataChecks': 19, 'originalRawReviewSHA256': addendum['rawReviewLogSHA256'],
                               'actualReviewCommand': addendum['actualReviewCommand'],
                               'actualPython': addendum['actualPython'], 'actualPythonSHA256': addendum['actualPythonSHA256'],
                               'retainedControllerKernelObservation': addendum['currentControllerKernelObservation'],
                               'countsAreProductAssertions': False},
            'preparationOriginalFalseCheckRetained': True, 'derivedDurableValidatorExecutedForSpaceProof': False,
            'packagerIsIndependentQA': False, 'productTestsOrBrowserExecutedByThisPackage': False},
        'sourceClosure': {'actualCapturedWebFiles': 125, 'allCapturedBeforeAfterHashesMatch': True,
                          'allCapturedSnapshotsMatchExactFrozenGitObjects': True,
                          'canonicalNodeLocalRequireClosure': sorted(node_closure), 'canonicalNodeClosureComplete': True,
                          'committedPythonHelperReferences': helper_refs, 'committedVendorDependencyReferences': ['geometry-web/vendor/fflate/umd/index.js'],
                          'committedReferencesAreIndependentHistoricalSnapshots': False,
                          'executedWrapperSnapshotDirectoryAbsent': True, 'originalAvailableWrapperSnapshotChecks': review['availableWrapperSnapshotChecks'],
                          'retainedWrapperSourcesMatchRecordedHashes': True,
                          'sourceVersion': receipt['before']['sourceVersion'],
                          'sourceVersionIsNotAFileByFileRuntimeSourceArchive': True,
                          'sourceCopiesWereExecutedForPublication': False},
        'sourceCopies': sources + references, 'fullTestedCommitSourceCopies': references,
        'sourceAndArtifactByteBindings': bindings,
        'publicationImplementation': {'originalV8SHA256': sha(PREPARER), 'actualBuilderOriginalSHA256': sha(__file__),
                                    'actualAdapterOriginalSHA256': sha(paths['adapter']), 'implementationSourceIncluded': False, 'adapterBuilderSourcesIncluded': True, 'completeOriginalEngineSourceClosureRetainedBesideBuildReceipt': True,
                                    'unchangedV8MainWithOnlyExtra': True, 'defaultUnrelatedCommonSourceLoopSkipped': True,
                                    'defaultExistingSavedSourceSnapshotsOverwritten': False,
                                    'projection': 'v8 bounded ASCII machine-path tokens preserve all non-token prose, backticks and punctuation; structured JSON/JSONL/ZIP mappings retain injective dictionary keys and one-to-one values.'},
        'historicalFullCdp': {'testedHead': '5174a8dafd8c48329d7166abbd3d104e3c28c0c4', 'pass': 2207, 'fail': 0, 'skip': 0, 'includedInThisPackage': False, 'rebound': False},
        'windows173': {'pass': 1692, 'fail': 2, 'exitCode': 1, 'completed': False, 'cloudOriginalsReceived': False, 'includedInThisPackage': False, 'rebound': False},
        'independentOtherScopes': {'included': False, 'earlier9ebFailed1842IncompletePreservedElsewhere': True,
                                   'earlierF3Unreceipted2207Golden84ExitActorUnknownPreservedElsewhere': True,
                                   'caption329AndSIX198Remain9eb': True, 'prior243OriginalSpace228NotRebound': True,
                                   'firstFullMotherSIG9IsNotProductFailure': True, 'mutableNewFullRunArtifactsCollected': False},
        'environmentLimits': {'actualPackagingUID': os.getuid(), 'originalProductUIDRecordedInReceipt': None, 'originalUIDLimit': 'Product receipt does not separately record Unix UID; current packager UID is not rebound to original runtime.', 'goldenCDPCompared': False},
        'omissions': ['Private queue/feedback/profile/user payloads, native binary/sidecar/executable bytes, standalone large PNG screenshots.',
                      'All33 actual sealed Space PNGs exceed16KiB and are omitted; no temporary same-name assembly PNG was read.',
                      'Other product scopes, mutable new FULL files, raw unreceipted historical outputs and historical Windows originals.'],
        'limits': ['228 are original assertion checks with programmatic fixtures/state observation/failure injection, not end-to-end scenario counts; metadata checks are never added.',
                   'Only five declared groups plus setup/browser-health are complete. Timber material/source guards remain omitted; no allSpace/all43/fullCDP/golden claim.',
                   'The125 top-level web JS/CSS/HTML snapshots are actual hash-captured before/after copies. Seven Python helpers and vendor fflate are separate exact-f3 Git references; absence of transient source changes is not proved.',
                   'Original executed-wrapper-sources directory is absent and its available-check map is empty. Same-hash retained original wrapper sources are supplied without relabeling them sealed historical snapshots.',
                   'Original executable/native hashes, runtime session and actual live Node/Chromium identity remain in receipts. Binary/shared-library/profile bytes are omitted; this is not a complete archival runtime image.',
                   'Detached launch starts controller280637 in its own PGID/SID. Its receipt retains launch-time pending metadata and empty stream hashes; final streams and kernel wait status0 are separate later evidence.',
                   'Stop observation records server280656/native280657 as existing Z; Node280720/browser280730 absent at observation, port refused. Z is never called absent.',
                   'Full-space different-actor proof uses actual reviewExecutor/rawReviewLog; launch addendum uses actualReviewCommand/rawReviewLogSHA256. All reviewer sources/logs/preparation inputs are retained without re-execution.',
                   'Preparation original literal-search false check is retained; addendum separately uses AST correction. Its derived durable validator is source-only for this Space proof.',
                   'v8 original publication code uses bounded ASCII token projection and injective structured dictionary keys. Actual original/public bytes and hashes remain distinct.',
                   'This builder performs read/hash/parser/selfchecks only. It is not an independent packet QA actor or release approval.'],
        'releaseApproved': False,
    }
    readme = '''# Durable standalone Space public evidence

The original canonical `node geometry-web/space_model_test.js` completed on clean `f3b8285729b42cd22451c98cba1e2ec4514517f3`: **228 passed, 0 failed**; `completed` and `executionVerified` are true. Actual Node, gate, controller, launcher and stop exited 0. This package preserves that execution and does not rerun product tests, validators, browser or services.

The five declared groups are space-height-library112, projection-lifecycle18, projection-placement36, font-layout19 and space-flow39. Setup2 and browser-health2 bring the scope to228. The original suite expressly omits timber-material and timber-source-guards. These are assertion counts with programmatic fixture setup, state observation and failure injection, not end-to-end scenarios. This is bounded standalone Space acceptance, with no all-Space, all43, full CDP or CDP golden claim. The packaging command records UID1000; the original product receipt does not separately record Unix UID.

The owned lifecycle preserves started, ready and terminal receipts, runtime/native/executable identity, exact service/gate/stop commands, original raw streams and explicit `.stat.raw` files. The exact stop records server280656 and native280657 as existing zombies Z; Node280720 and Chromium280730 are absent at that observation, and the port refuses connection. The service then returns-15 after SIGTERM, separately from successful controller/gate/stop0.

Detached launch started controller280637 with its own PGID280637 and SID280637. Its original receipt honestly retains product pending at launch, final controller exit unknown at launch, and then-empty stdout/stderr hashes. Later final raw stream hashes remain separately recorded. The different-actor addendum retains the kernel zombie stat with wait status0, establishing controller exit0; no current process observation was substituted.

All125 actual captured top-level web JS/CSS/HTML sources match the original before/after map and exact frozen f3 Git objects. The recursive local Node require closure includes space_model_test, cdp_confirmation_gate, async_reply_ui_test, save_reopen_synthetic_test, cdp_evaluation, space_test_floor and vendor fflate. Seven committed Python helpers for gate/service/runtime and vendor fflate are separate exact-f3 source references. The original capture did not independently record those helper/vendor files, and does not exclude transient changes. Every source entry separates fullSHA, original hash/bytes, public hash/bytes and snapshot status; public copies were never executed.

Hash-bound original runner, observers, launch adapters, stage launcher/stop helper, lifecycle controller, stop wrapper and detached launcher sources are retained. The original executed-wrapper snapshot directory is absent and availableWrapperSnapshotChecks is empty; same-hash retained source originals are supplied with this limit. Native/executable hashes and runtime/session identity remain in receipts, while binaries, sidecars, shared libraries and profiles are omitted. This is not a full archival runtime image.

The different-actor Space review retains its actual reviewExecutor, rawReviewLog and validator:39 integrity plus7 acceptance checks, actual exit0. The launch addendum retains its actualReviewCommand, rawReviewLogSHA256, reviewer source and19 metadata checks, actual exit0. Its preparation input and all source dependencies are retained. The original preparation literal-search false check remains false; the addendum separately corrects classification through AST. The separately derived durable validator was not the Space proof executor. None of these checks adds to228 product assertions. Packager checks are selfchecks, and independent packet QA remains separate.

Original9eb failed1842 incomplete, first f3 unreceipted raw2207/goldenmatched84 with unknown exit/actor, caption329/SIX198 on9eb and prior243 original Space228 remain elsewhere and are never rebound to this receipt. Earlier full mother-process SIG9 is not relabeled product failure. Historical clean5174 fullCDP2207 and Windows1731692/2 incomplete retain their original sources; their raw evidence is not collected here. No mutable new FULL evidence or temporary same-name assembly PNG is used.

Private queue/feedback/user payloads, profiles, binaries/sidecars, and all33 sealed Space PNGs above16KiB are omitted. The synthetic saved `.gcanvas`, complete result, raw logs and exact source references remain. Original/public hashes and byte counts, projection flags and one-to-one structured key audits are preserved. Original v8 bounds replacement to ASCII machine-path tokens, preserving non-token prose, backticks and punctuation. The scratch adapter supplies its own full Space references and skips six unrelated default source copies, preserving existing saved source snapshots. Complete actual publication source, executable, command, exit and raw stream hashes remain beside the package build receipt. Original engine sources containing generic path-regex literals stay outside this public package; adapter and builder source copies are included. This package is not release approval.
'''
    write_new(paths['config'], config)
    write_new(paths['extra'], extras)
    write_new(paths['metadata'], metadata, public=True)
    assert not paths['README'].exists()
    paths['README'].write_text(readme)
    python = Path('/proc/self/exe').resolve()
    command = [str(python), '-B', str(paths['adapter']), '--output', str(output), '--only-extra',
               '--extra-config', str(paths['config']), '--extra-evidence', str(paths['extra']),
               '--metadata', str(paths['metadata']), '--readme', str(paths['README'])]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with paths['build.stdout.raw'].open('xb') as stdout, paths['build.stderr.raw'].open('xb') as stderr:
        result = subprocess.run(command, stdout=stdout, stderr=stderr)
    build_sources = [Path(__file__), paths['adapter'], PREPARER, HERE / 'prepare_resume_packet.py', HERE / 'prepare_cdp_diagnosis.py', HERE / 'execute_f3b_durable_space_packet_v2.py']
    build = {'schema': 'geometry-f3b-durable-space-scratch-package-build/1', 'startedUTC': started,
             'finishedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': command,
             'actualExitCode': result.returncode, 'actualPython': str(python), 'actualPythonSHA256': sha(python),
             'builderCommand': sys.orig_argv, 'builderUID': os.getuid(),
             'publicationSourceClosure': [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in build_sources],
             'inputFiles': [{'role': name, 'path': str(paths[name]), 'bytes': paths[name].stat().st_size, 'sha256': sha(paths[name])} for name in ['config', 'extra', 'metadata', 'README']],
             'rawStreams': [{'path': str(paths[name]), 'bytes': paths[name].stat().st_size, 'sha256': sha(paths[name])} for name in ['build.stdout.raw', 'build.stderr.raw']],
             'output': str(output), 'productExecuted': False, 'validatorsReexecuted': False,
             'serviceOrBrowserUsed': False, 'repoWritten': False, 'oldSavedResultsOverwritten': False, 'independentQA': False}
    if (output / 'manifest.json').exists():
        build['manifestSHA256'] = sha(output / 'manifest.json')
    write_new(paths['package-build'], build)
    assert result.returncode == 0, build
    manifest = load(output / 'manifest.json')
    files = sorted(p for p in output.rglob('*') if p.is_file())
    assert set(p.relative_to(output).as_posix() for p in files) == {'manifest.json', *(entry['path'] for entry in manifest['publicFiles'])}
    for entry in manifest['publicFiles']:
        actual = output / entry['path']
        assert sha(actual) == entry['sha256'] and actual.stat().st_size == entry['bytes']
    for entry in sources + references:
        public = output / entry['publicPath']
        assert sha(public) == entry['publicSHA256'] and public.stat().st_size == entry['publicBytes']
    assert manifest['rounds'][0]['declaredResult']['pass'] == 228 and len(manifest['rounds']) == 1
    assert manifest['rounds'][0]['declaredResult']['fail'] == 0
    assert len(manifest['sourceCopies']) == 147
    assert not list(output.rglob('*.png'))
    sample = 'X`<workspace-path>` after; foo(<isolated-test-directory>), done.'
    assert P.p.redact_text(sample) == 'X`<workspace-path>` after; foo(<isolated-test-directory>), done.'
    collision = {'<workspace-path>': {'p': '<workspace-path>'}, '<workspace-path>': {'p': '<workspace-path>'}}
    assert len(P.collision_safe_projection(collision)) == 2
    for path in files:
        if path.suffix == '.json':
            json.loads(path.read_text())
    summary = {'schema': 'geometry-f3b-durable-space-packager-selfcheck/1', 'checksPassed': True,
               'manifestSHA256': sha(output / 'manifest.json'), 'files': len(files),
               'bytes': sum(p.stat().st_size for p in files), 'rounds': 1,
               'actualCapturedWebSources': 125, 'hashBoundExecutorReviewerSources': 14,
               'separateExactF3GitHelperVendorReferences': 8, 'canonicalNodeLocalRequireClosureFiles': 7,
               'productPass': 228, 'productFail': 0, 'scopeGroups': expected_groups,
               'independentMetadataReviewChecks': {'integrity': 39, 'acceptance': 7, 'launchAddendum': 19},
               'originalRawProcessStatFilesRetained': 3, 'largePngsOmitted': 33,
               'selfcheckActor': '/root/delivery_closeout/restored_space_packet', 'independentQA': False,
               'actualPython': str(python), 'actualPythonSHA256': sha(python), 'actualBuilderCommand': sys.orig_argv,
               'actualBuilderSourceSHA256': sha(__file__), 'innerBuildReceiptSHA256': sha(paths['package-build'])}
    write_new(paths['packager-selfcheck'], summary)
    print(json.dumps({'output': str(output), 'manifestSHA256': summary['manifestSHA256'],
                      'files': summary['files'], 'bytes': summary['bytes'],
                      'buildReceipt': str(paths['package-build']), 'selfcheck': str(paths['packager-selfcheck'])}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
