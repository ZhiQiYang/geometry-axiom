"""Independent readonly source/actor supplement for the formal FULL v3 packet.

The parent separately audits full packet hashes/JSON/inverse projections. This
actor audits captured/Git source roles and actual execution identity closure,
without running product, browser, services, CLI/API or packaging code.
"""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import sys

S = Path('<workspace-path>')
D = S / 'geometry-delivery-closeout-20261009'
P = D / 'f3b-durable-full-public-v3'
G = S / 'geometry-root-f3b82857-durable-full-cdp-gate'
L = S / 'geometry-root-f3b82857-durable-full-cdp-lifecycle'
A = S / 'geometry-root-f3b82857-durable-full-cdp-detached-launch'
K = S / 'geometry-ui-verification/f3b-durable-full-launch-kernel-review-v2'
HEAD = 'f3b8285729b42cd22451c98cba1e2ec4514517f3'
MANIFEST = 'f33d0032d3bfd33cec02f9790a90104892e8a4bbd8803b8349105544571c7b93'
H = S / 'geometry-assembly-packet-review-v4-independent.py'
assert hashlib.sha256(H.read_bytes()).hexdigest() == '0c7d16eac138b21ec9a2d70235e5e8ba8b57336a5c449cea2e66aa6583f35e60'
spec = importlib.util.spec_from_file_location('readonly_parser_helpers', H)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
OUT = S / 'geometry-formal-full-v3-source-actor-closure-review'


def main():
    assert not OUT.exists()
    OUT.mkdir()
    checks = []
    def check(n, v, details=None):
        checks.append({'name': n, 'passed': bool(v), 'details': details})
    m = h.load(P / 'manifest.json')
    r, terminal, stop, launch = h.load(G / 'receipt.json'), h.load(L / 'terminal.json'), h.load(L / 'owned-stop/terminal-receipt.json'), h.load(A / 'launch.json')
    check('final-ready formalFULLv3 manifest identity', h.sha((P / 'manifest.json').read_bytes()) == MANIFEST)
    check('original formal receipt distinct original SHA38bda', h.sha((G / 'receipt.json').read_bytes()) == m['formalFullResult']['originalReceiptSHA256'] == '38bda376c1aed0faf20b02d611747b145eaf594f0d77d037dba9e598ef3d2d35')
    check('original formal raw command identity distinct b7ef', h.sha((G / 'command.log').read_bytes()) == m['formalFullResult']['rawLogOriginalSHA256'] == r['log']['sha256'] == 'b7ef0a651079a2ac51f211929d3e625bf83aff6018249de1477900f1c4b104d3')
    for phase in ('before', 'after'):
        check('original actual clean fullf3 SHA ' + phase, r[phase]['git']['head'] == HEAD and r[phase]['git']['status'] == '' and r[phase]['runtime']['fresh'] is True and r[phase]['runtime']['root'] == str(h.REPO))
    captures = r['before']['sourceSha256']
    captured_refs = {x['repositoryPath']: x for x in m['sourceBindings'] if x['role'] == 'actual original before/after captured source, separately exact-Git-matched'}
    public_capture_refs = {x['artifactRelativePath'].removeprefix('executed-harness-sources/'): x for x in m['rounds'][0]['rawEvidence'] if x.get('artifactRelativePath', '').startswith('executed-harness-sources/')}
    check('exact125 captured maps before/after/ref-census', len(captures) == len(captured_refs) == len(public_capture_refs) == 125 and captures == r['after']['sourceSha256'] and set(captures) == set(captured_refs) == set(public_capture_refs))
    check('original archiveexact125 no omitted extra web sources', {x.relative_to(G / 'executed-harness-sources').as_posix() for x in (G / 'executed-harness-sources').rglob('*') if x.is_file()} == set(captures))
    for relative, digest in captures.items():
        original = (G / 'executed-harness-sources' / relative).read_bytes()
        git = h.git(['show', HEAD + ':' + relative])
        ref, public_ref = captured_refs[relative], public_capture_refs[relative]
        public = (P / public_ref['path']).read_bytes()
        check('actual captured bytes match originalfrozenGit ' + relative, original == git and h.sha(original) == digest == ref['originalSHA256'] == public_ref['originalSha256'] and len(original) == ref['originalBytes'] == public_ref['originalBytes'])
        check('public source identity role not executed ' + relative, h.sha(public) == public_ref['sha256'] and len(public) == public_ref['bytes'] and ref['publicCopyExecuted'] is False and public_ref['byteIdenticalOriginal'] == (original == public) and public_ref['publicProjection'] == (original != public))
    original_actor_refs = {Path(x['publicPath']).name: x for x in m['sourceAndArtifactByteBindings'] if x['publicPath'].startswith('executor-source-bytes/')}
    actor_sources = {
        'run_full_cdp_identity.py': (S / 'geometry-takeover-evidence-harness/run_full_cdp_identity.py', r['before']['runnerSha256']),
        'cdp_execution_identity_v2.py': (S / 'geometry-takeover-evidence-harness/cdp_execution_identity_v2.py', r['before']['identityObserverSha256']),
        'sandbox-launch.cjs': (S / 'geometry-takeover-evidence-harness/full-launch-adapters/sandbox-launch.cjs', r['before']['launchAdapterSha256']['sandbox-launch.cjs']),
        'sitecustomize.py': (S / 'geometry-takeover-evidence-harness/full-launch-adapters/sitecustomize.py', r['before']['launchAdapterSha256']['sitecustomize.py']),
        'geometry-owned-integration-lifecycle-f3b-v2.py': (S / 'geometry-owned-integration-lifecycle-f3b-v2.py', terminal['controllerSHA256']),
        'geometry-stage-launch.py': (S / 'geometry-stage-launch.py', terminal['launchSHA256']),
        'geometry-stop-with-terminal-receipt-f3b.py': (S / 'geometry-stop-with-terminal-receipt-f3b.py', stop['wrapperSHA256']),
        'geometry-owned-full-stage-stop.py': (S / 'geometry-owned-full-stage-stop.py', stop['helperSHA256']),
        'geometry-launch-detached-owned-integration-f3b.py': (S / 'geometry-launch-detached-owned-integration-f3b.py', launch['launcherSourceSHA256']),
    }
    check('exact9 original sourceactors roles distinct', len(original_actor_refs) == len(actor_sources) == 9 and set(original_actor_refs) == set(actor_sources))
    for name, (source, digest) in actor_sources.items():
        ref = original_actor_refs[name]
        public_ref = next(x for x in m['historyReviewsAndExecutorSources'] if x['path'] == ref['publicPath'])
        public = (P / ref['publicPath']).read_bytes()
        check('original sourceactor hash bound to actualrun ' + name, h.sha(source.read_bytes()) == digest == ref['originalSHA256'] == public_ref['originalSha256'] and source.stat().st_size == ref['originalBytes'] == public_ref['originalBytes'])
        check('public sourceactor recordedidentity copy notexecuted ' + name, h.sha(public) == public_ref['sha256'] and len(public) == public_ref['bytes'] and ref['publicCopyExecuted'] is False)
    check('original runner5ce/controller5a334/stopcc505/launch1bd explicit', r['before']['runnerSha256'] == '5ce8212de96e45d0b613b17888a053a7a679024dc1a230f4c734a6170cc5da89' and terminal['controllerSHA256'] == '5a33421c7b84919c212ebf3c444bed22a950177462cd87c073e4d99fdda0e5ae' and stop['wrapperSHA256'] == 'cc505b94c1011bed31d350a8670422808ded123e6b058e54e3c7853ff79286a2' and launch['launcherSourceSHA256'] == '1bd4791d7745744634a093b9df3bbb31901ffbe4723e5858712b1ca3d11d6333')
    check('original runnerobserveradapters beforeafter stable', all(r['before'][k] == r['after'][k] for k in ['runnerSha256', 'identityObserverSha256', 'launchAdapterSha256']))
    helpers = ['tests/release_gate.py', 'tests/binaries.py', 'geometry-web/start_local.py', 'geometry-web/serve.py', 'geometry-web/runtime_version.py', 'geometry-web/native_context.py', 'geometry-web/feedback_store.py']
    references = {x['repositoryPath']: x for x in m['sourceBindings'] if x['role'] == 'exact frozen Git source reference, not original independently captured helper snapshot'}
    check('Python7/vendor/golden9 references distinct from125 captures', set(references) == set(helpers + ['geometry-web/vendor/fflate/umd/index.js', 'geometry-web/cdp_sections.golden.json']) and len(references) == 9)
    for relative, ref in references.items():
        original = h.git(['show', HEAD + ':' + relative])
        path = 'committed-f3-source-reference/' + relative
        artifact_ref = next(x for x in m['sourceAndArtifactByteBindings'] if x['publicPath'] == path)
        public_ref = next(x for x in m['historyReviewsAndExecutorSources'] if x['path'] == path)
        check('exact fullf3 source reference role ' + relative, h.sha(original) == ref['originalSHA256'] == artifact_ref['originalSHA256'] == public_ref['originalSha256'] and len(original) == ref['originalBytes'] and ref['sourceHead'] == HEAD and ref['publicCopyExecuted'] is artifact_ref['publicCopyExecuted'] is False)
        check('reference public source identity ' + relative, h.sha((P / path).read_bytes()) == public_ref['sha256'] and (P / path).stat().st_size == public_ref['bytes'])
    check('six synthetic fixtures exactdeclared referencecensus', len(m['additionalFixtureSourceReferences']) == 6 and {x['repositoryPath'] for x in m['additionalFixtureSourceReferences']} == {'tests/reference_pdf_fixture.js', 'tests/fixtures/evidence_pdf.cjs', 'tests/room_outline_fixture.js', 'tests/fixtures/assembly-external-dependencies.scene', 'geometry-web/examples/assembly-rules-v1.gcanvas', 'geometry-web/examples/assembly-generation-v1.gcanvas'})
    for ref in m['additionalFixtureSourceReferences']:
        original = h.git(['show', HEAD + ':' + ref['repositoryPath']])
        check('frozen synthetic fixture source reference noexecutionclaim ' + ref['repositoryPath'], h.sha(original) == ref['originalSha256'] and len(original) == ref['originalBytes'] and ref['sourceHead'] == HEAD and ref['publishedCopyWasExecuted'] is False and 'reference' in ref['role'])
    check('wrapper snapshot originally unavailable limit preserved', not (G / 'executed-wrapper-sources').exists() and m['ownedLifecycleOutcome']['originalWrapperSnapshotDirectoryAvailable'] is False and m['ownedLifecycleOutcome']['sameHashRetainedScratchActorsIncluded'] is True)
    canonical = r['evidence']['canonicalResult']
    check('actual unfiltered original canonical command fullscope', r['command'] == ['node', 'geometry-web/cdp_test.js'] and canonical['scope']['mode'] == 'full' and canonical['scope']['filters'] == canonical['scope']['modifiers'] == [] and not any(k.endswith('_ONLY') or k in {'GEOMETRY_UPDATE_GOLDEN', 'GEOMETRY_CDP_MODULE_OVERRIDE', 'GEOMETRY_CDP_SOURCE_OVERRIDE'} for k in r['environment']))
    check('original actual Node/gate0 successfulcomplete2207 no borrowedfirst run', r['execution']['exitCode'] == r['gateExitCode'] == terminal['actualGateExitCode'] == 0 and r['execution']['timedOut'] is r['execution']['interrupted'] is False and r['executionVerified'] is True and canonical['completed'] is True and canonical['passedAssertions'] == 2207 and canonical['failedAssertions'] == 0 and canonical['skipped'] == [] and m['formalFullResult']['firstUnreceiptedRawRunReused'] is False)
    golden = h.loads(h.git(['show', HEAD + ':geometry-web/cdp_sections.golden.json']))
    check('original frozen golden84 matched exact actualcanonicalsections', canonical['goldenCompare'] == 'matched' and canonical['sections'] == golden and len(golden) == 84 and sum(golden.values()) == 2207)
    log = (G / 'command.log').read_text()
    source = (G / 'executed-harness-sources/geometry-web/cdp_test.js').read_text()
    check('original expectedP38 probe1 no inventedzeroexceptionpredicate', canonical['uncaughtBrowserExceptions'] == 1 and log.count('[EXPECTED EXCEPTION] Error: fb-auto-probe') == 1 and '[UNEXPECTED EXCEPTION]' not in log and "fb-auto-probe" in source and m['formalFullResult']['expectedOriginalFbAutoProbeExceptions'] == 1)
    live = r['executionIdentity']['liveBinding']
    actors = {x['role']: x for x in live['processes']}
    node, chrome = actors['actual browser parent Node'], actors['actual CDP_SCOPE Chromium main process']
    check('actual live Node PID/ELF/hash/canonicalcmd', node['pid'] == r['execution']['pid'] == 284641 and node['sha256'] == r['before']['executables']['node']['sha256'] and node['executableMagicHex'] == '7f454c46' and node['cmdline'] == ['node', 'geometry-web/cdp_test.js'] and node['cwd'] == str(h.REPO))
    check('actual live Chrome ELF CDP_SCOPE PID/port/profile', chrome['pid'] == canonical['scope']['browserPid'] == live['cdpScope']['browserPid'] == 284692 and chrome['sha256'] == 'd387400aaf740ccb75e5e996a34aa0940e6e97683a4eabd6ae34c1eed6804723' and chrome['executableMagicHex'] == '7f454c46' and '--remote-debugging-port=' + str(canonical['scope']['cdpPort']) in chrome['cmdline'] and '--user-data-dir=' + r['ownedBrowserProfile'] in chrome['cmdline'] and not any(x.startswith('--no-sandbox') for x in chrome['cmdline']))
    check('dash launchstage excluded from actualChromeidentity', any(x['exe'] == '/usr/bin/dash' and x['pid'] == chrome['pid'] for x in r['executionIdentity']['excludedLauncherStages']) and chrome['exe'] != '/usr/bin/dash' and r['executionIdentity']['errors'] == [])
    for phase in ('before', 'after'):
        bridge = r[phase]['liveBridge']
        check('actual owned directbridge PID/parent/nativehash ' + phase, len(bridge) == 1 and bridge[0]['pid'] == 284554 and bridge[0]['parent'] == r[phase]['runtime']['pid'] == 284553 and bridge[0]['sha256'] == r[phase]['native']['bridge']['sha256'])
        check('actual native freshness bridge/modelsourcefingerprints ' + phase, all(r[phase]['native'][k]['state'] == 'fresh' and len(r[phase]['native'][k]['sha256']) == len(r[phase]['native'][k]['sidecarSha256']) == len(r[phase]['native'][k]['fingerprint']) == 64 for k in ['bridge', 'model-base']))
    check('native/runtimebeforeafter sameexactidentity', r['before']['native'] == r['after']['native'] and r['before']['runtime'] == r['after']['runtime'])
    check('sealed original lifecycle and ownedstop0 service-15 cleanhead', h.sha((L / 'terminal.json').read_bytes()) == m['formalFullResult']['ownedTerminalOriginalSHA256'] and terminal['actualGateExitCode'] == terminal['stopExitCode'] == stop['exitCode'] == 0 and terminal['actualServiceExitAfterStop'] == -15 and terminal['headAfter'] == HEAD and terminal['dirtyBefore'] == terminal['dirtyAfter'] == '')
    check('original detached launch nullfinalgate and pending not substituted0', launch['launchExitCode'] == 0 and launch['productGateExitCodeAtLaunch'] is None and launch['productCompletionAtLaunch'] == 'pending' and m['ownedLifecycleOutcome']['originalLaunchRecordedFinalExitFields']['productGateExitCodeAtLaunch'] is None)
    check('original actualcontroller PID/PGID/SID all284534', launch['actualControllerPID'] == launch['actualControllerPGID'] == launch['actualControllerSID'] == 284534)
    initial_raw = (A / 'launched-controller.stat.raw').read_bytes()
    terminal_raw = (K / 'controller.terminal.stat.raw').read_bytes()
    initial_fields = initial_raw.decode().split(')', 1)[1].strip().split()
    final_fields = terminal_raw.decode().split(')', 1)[1].strip().split()
    check('same actualkernel PID originalstarttime PGID SID preventsPIDreuse', initial_raw.decode().split('(', 1)[0].strip() == terminal_raw.decode().split('(', 1)[0].strip() == '284534' and initial_fields[19] == final_fields[19] and int(initial_fields[2]) == int(initial_fields[3]) == int(final_fields[2]) == int(final_fields[3]) == 284534)
    kernel = h.load(K / 'receipt.json')
    kobs = kernel['actualControllerTerminalObservation']
    check('actual datedterminal kernel Z waitstatus0 provescontroller0', final_fields[0] == kobs['state'] == 'Z' and int(final_fields[49]) == kobs['kernelWaitStatus'] == 0 and kobs['actualControllerExitCode'] == m['ownedLifecycleOutcome']['actualControllerExitCode'] == 0 and kobs['pid'] == 284534 and kobs['rawSHA256'] == h.sha(terminal_raw) == m['ownedLifecycleOutcome']['kernelActualStatOriginalSHA256'])
    check('kernel originalreceipt/sourcehash not current reconstructedobservation', h.sha((K / 'receipt.json').read_bytes()) == m['ownedLifecycleOutcome']['kernelReviewOriginalSHA256'] == 'b1f872248cf5eaf1cfda3ebbd0e494006308a740fe4d90080396fa92148f55c8' and kernel['exitCode'] == 0 and kernel['checksPassed'] == 17 and all(kernel['checks'].values()) and datetime.datetime.fromisoformat(kobs['observedUTC']) > datetime.datetime.fromisoformat(terminal['finishedUtc']))
    kernel_source = next(x for x in kernel['actualCommand'] if isinstance(x, str) and x.endswith('.py'))
    check('actual originalkernel reviewer sourceidentity305452', h.sha(Path(kernel_source).read_bytes()) == kernel['sourceHashes'][kernel_source] == '30545241fbbddf575bb995d76df148df2f2d3699c0d9f64737edf30273029aa9')
    for row in stop['processObservations']:
        if row['exists']:
            raw_stat = (L / ('owned-stop/proc-' + str(row['pid']) + '.stat.raw')).read_bytes()
            check('ownedstop existingprocess stateexact dated ' + str(row['pid']), row['state'] == raw_stat.decode().split(')', 1)[1].strip().split()[0] and row['statSHA256'] == h.sha(raw_stat))
        else:
            check('ownedstop absentprocess observation not zombie ' + str(row['pid']), row['state'] == 'absent-at-observation')
    check('owned stop portrefused actualnot activeuser service', stop['portObservation']['accepting'] is False and stop['productTestExecution'] is False)
    check('no metadata counts added tofull product2207', kernel['productTestsExecuted'] is False and m['formalFullResult']['passed'] == 2207 and m['formalFullResult']['originalGoldenSectionsMatched'] == 84)
    check('same formal manifest and original receipt stablethroughread', h.sha((P / 'manifest.json').read_bytes()) == MANIFEST and h.sha((G / 'receipt.json').read_bytes()) == '38bda376c1aed0faf20b02d611747b145eaf594f0d77d037dba9e598ef3d2d35')
    failures = [x for x in checks if not x['passed']]
    raw = ''.join(('PASS ' if x['passed'] else 'FAIL ') + x['name'] + '\n' for x in checks)
    (OUT / 'command.raw.log').write_text(raw)
    result = {'schema': 'geometry-formal-full-v3-source-actor-closure-review/1', 'actor': '/root/publication_final_review/assembly_packet_review', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': [sys.executable, '-B', str(Path(__file__).resolve())], 'actualPython': str(Path(sys.executable).resolve()), 'actualPythonSHA256': h.sha(Path(sys.executable).resolve().read_bytes()), 'reviewSourceSHA256': h.sha(Path(__file__).read_bytes()), 'parserHelperSourceSHA256': h.sha(H.read_bytes()), 'actualExitCode': 1 if failures else 0, 'passedMetadataChecks': len(checks) - len(failures), 'failedMetadataChecks': len(failures), 'countsAreProductTests': False, 'productOrBrowserOrServiceOrCLIOrAPIExecuted': False, 'repositoryOrGitHubWritten': False, 'packetOrOriginalsChanged': False, 'currentProcInspected': False, 'manifestSHA256': MANIFEST, 'testedProductSHA': HEAD, 'scope': 'Distinct source/Git and actual actor/kernel-role supplement; parent audits complete193-file packet hash/JSON/inverse projection scope separately.', 'referenceLimits': ['125 captured web sources match actual original before/after maps and exact frozen Git objects.', '7 Python/vendor/golden and6synthetic fixture references are exact frozen Git source references, not independent original captured execution snapshots.', 'Original9executor/helper actor sources match recorded hashes; original wrapper source snapshot archive absent, same-hash retained source bytes provided.', 'Original launch final gate exit is null; actualcontroller0 comes from dated retained samePID/starttime/PGID/SID kernelstat, never current process reconstruction.'], 'rawLog': {'path': str(OUT / 'command.raw.log'), 'bytes': (OUT / 'command.raw.log').stat().st_size, 'sha256': h.sha((OUT / 'command.raw.log').read_bytes())}, 'findings': failures, 'checks': checks}
    (OUT / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:result[k] for k in ['actualExitCode', 'passedMetadataChecks', 'failedMetadataChecks', 'reviewSourceSHA256', 'rawLog', 'findings']}))
    return result['actualExitCode']


if __name__ == '__main__':
    raise SystemExit(main())
