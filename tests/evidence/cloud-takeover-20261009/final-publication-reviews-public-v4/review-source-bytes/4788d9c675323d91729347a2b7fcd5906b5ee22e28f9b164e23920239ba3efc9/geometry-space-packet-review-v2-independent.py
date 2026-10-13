"""Independent readonly Space v2 packet audit; no product/browser/service use."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import zipfile

S = Path('<workspace-path>')
HELPER = S / 'geometry-assembly-packet-review-v4-independent.py'
assert hashlib.sha256(HELPER.read_bytes()).hexdigest() == '0c7d16eac138b21ec9a2d70235e5e8ba8b57336a5c449cea2e66aa6583f35e60'
spec = importlib.util.spec_from_file_location('readonly_parser_helpers', HELPER)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
D = S / 'geometry-delivery-closeout-20261009'
P = D / 'f3b-durable-space-public-v2'
G = S / 'geometry-root-f3b82857-durable-full-space-gate'
L = S / 'geometry-root-f3b82857-durable-full-space-lifecycle'
A = S / 'geometry-root-f3b82857-durable-full-space-detached-launch'
HEAD = 'f3b8285729b42cd22451c98cba1e2ec4514517f3'
MANIFEST = 'dbd3e468c878b2bea7c48b54ea578a795cbdb142939b115c903c732461a4bd4a'
OUT = S / 'geometry-space-v2-independent-publication-review'
CHECKS = []


def check(name, passed, details=None):
    CHECKS.append({'name': name, 'passed': bool(passed), 'details': details})


def main():
    assert not OUT.exists()
    OUT.mkdir()
    m = h.load(P / 'manifest.json')
    entries = m['publicFiles']
    paths = [x['path'] for x in entries]
    census = {x.relative_to(P).as_posix() for x in P.rglob('*') if x.is_file()}
    check('final-ready manifest exact SHA256', h.sha((P / 'manifest.json').read_bytes()) == MANIFEST)
    check('exact185 listed + manifest186 files', len(paths) == len(set(paths)) == 185 and census == set(paths) | {'manifest.json'})
    for row in entries:
        f = P / row['path']
        data = f.read_bytes()
        check('safe relative path ' + row['path'], not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts and not f.is_symlink())
        check('public bytes and SHA256 ' + row['path'], len(data) == row['bytes'] and h.sha(data) == row['sha256'])
        try:
            if f.suffix in {'.json', '.stacks'}:
                h.loads(data)
            elif f.suffix in {'.jsonl', '.trace', '.network'}:
                for line in data.splitlines():
                    if line.strip():
                        h.loads(line)
            elif f.suffix in {'.zip', '.gcanvas'}:
                with zipfile.ZipFile(f) as z:
                    names = z.namelist()
                    assert len(names) == len(set(names))
                    assert all(not Path(x).is_absolute() and '..' not in Path(x).parts for x in names)
                    assert z.testzip() is None
                    for name in names:
                        if name.endswith('.json'):
                            h.loads(z.read(name))
            else:
                continue
            check('structured unique keys/archive members CRC ' + row['path'], True)
        except Exception as exc:
            check('structured unique keys/archive members CRC ' + row['path'], False, repr(exc))

    originals = {}
    candidates = [G, L, A]
    extras = h.load(D / 'f3b-durable-space-extra-v2.json')
    for extra in extras:
        candidates.append(Path(extra['path']))
    for candidate in candidates:
        files = [candidate] if candidate.is_file() else [f for f in candidate.rglob('*') if f.is_file()]
        for f in files:
            data = f.read_bytes()
            originals.setdefault(h.sha(data), (f, data))
    evidence = m['rounds'][0]['rawEvidence'] + m['historyReviewsAndExecutorSources']
    reviewed = set()
    for row in evidence:
        path = row['path']
        public = (P / path).read_bytes()
        binding = originals.get(row['originalSha256'])
        if binding is None:
            check('retained original identity ' + path, False, row['originalSha256'])
            continue
        original_path, original = binding
        check('original bytes and SHA256 ' + path, len(original) == row['originalBytes'] and h.sha(original) == row['originalSha256'])
        check('one-to-one projection all non-token characters ' + path, h.equal_projection(original, public, Path(path).suffix), {'original': str(original_path), 'byteIdentical': original == public})
        check('declared projection markers accurate ' + path, row['byteIdenticalOriginal'] == (original == public) and row['publicProjection'] == (original != public))
        reviewed.add(path)

    r = h.load(G / 'receipt.json')
    raw = (G / 'command.log').read_text()
    canonical_rows = [h.loads(x[len('SPACE_RESULT '):]) for x in raw.splitlines() if x.startswith('SPACE_RESULT ')]
    check('one canonical original SPACE_RESULT', len(canonical_rows) == 1)
    c = canonical_rows[0]
    expected = {'setup': 2, 'space-height-library': 112, 'projection-lifecycle': 18, 'projection-placement': 36, 'font-layout': 19, 'space-flow': 39, 'browser-health': 2}
    check('228/0 completed all5 declared plus2 auxiliary groups', c['passed'] == 228 and c['failed'] == 0 and c['completed'] is True and c['completenessProblems'] == [] and set(c['groups']) == set(expected) and all(c['groups'][k] == {'expected': n, 'passed': n, 'failed': 0, 'completed': True} for k, n in expected.items()) and c['exceptions'] == c['consoleErrors'] == [])
    check('explicit2 omitted timber groups no filters', c['scope']['included'] == list(expected)[1:6] and c['scope']['omitted'] == ['timber-material', 'timber-source-guards'] and c['scope']['filters'] == [])
    check('actual Node/gate0 and original execution verified', r['command'] == ['node', 'geometry-web/space_model_test.js'] and r['execution']['exitCode'] == r['gateExitCode'] == 0 and r['executionVerified'] is True and not r['execution']['interrupted'] and not r['execution']['timedOut'])
    pr_path = m['rounds'][0]['receiptPath']
    check('public receipt all original associations plus explicit provenance', h.equal_projection((G / 'receipt.json').read_bytes(), (P / pr_path).read_bytes(), '.json', True) and h.load(P / pr_path)['publicProjection']['originalSha256'] == h.sha((G / 'receipt.json').read_bytes()))
    cp = 'rounds/f3b-durable-standalone-space-completed/canonical-original-result.public.json'
    check('public canonical exact original projected', h.load(P / cp) == h.project(c))
    reviewed.update([pr_path, cp, 'README.md'])
    for phase in ('before', 'after'):
        check('original clean fullf3 SHA + fresh runtime ' + phase, r[phase]['git']['head'] == HEAD and r[phase]['git']['status'] == '' and r[phase]['runtime']['fresh'] is True and r[phase]['git']['tree'] == m['testedGitTree'])
    captured = r['before']['sourceSha256']
    check('actual125 before/after capture maps equal', len(captured) == 125 and captured == r['after']['sourceSha256'])
    refs = {x['repositoryPath']: x for x in m['sourceCopies'] if x['originalExecutionSnapshotCaptured']}
    check('all125 captured source refs exactcensus', len(refs) == 125 and set(refs) == set(captured))
    for relative, digest in captured.items():
        source = (G / 'executed-harness-sources' / relative).read_bytes()
        git_bytes = h.git(['show', HEAD + ':' + relative])
        ref = refs[relative]
        public = (P / ref['publicPath']).read_bytes()
        check('capture/frozenGit/public reference ' + relative, h.sha(source) == digest == ref['originalSHA256'] == ref['recordedBeforeAndAfterSHA256'] and source == git_bytes and h.equal_projection(source, public, Path(relative).suffix) and h.sha(public) == ref['publicSHA256'] and ref['exactGitObjectMatchesCapturedBytes'] is True and ref['publishedCopyWasExecuted'] is False)
    for ref in m['fullTestedCommitSourceCopies']:
        original = h.git(['show', ref['sourceHead'] + ':' + ref['repositoryPath']])
        public = (P / ref['publicPath']).read_bytes()
        check('separate committed helper/vendor reference ' + ref['repositoryPath'], ref['sourceHead'] == HEAD and h.sha(original) == ref['originalSHA256'] and len(original) == ref['originalBytes'] and h.equal_projection(original, public, Path(ref['repositoryPath']).suffix) and h.sha(public) == ref['publicSHA256'] and len(public) == ref['publicBytes'] and ref['originalExecutionSnapshotCaptured'] is False and ref['publishedCopyWasExecuted'] is False)
        reviewed.add(ref['publicPath'])
    check('Python7/vendor1 not promoted independent historical snapshots', len(m['fullTestedCommitSourceCopies']) == 8 and m['sourceClosure']['committedReferencesAreIndependentHistoricalSnapshots'] is False and m['sourceClosure']['executedWrapperSnapshotDirectoryAbsent'] is True and m['sourceClosure']['originalAvailableWrapperSnapshotChecks'] == {})
    requires = set()
    def closure(relative):
        if relative in requires:
            return
        requires.add(relative)
        data = h.git(['show', HEAD + ':' + relative]).decode()
        for token in re.findall(r'require\(\s*[\'\"]([^\'\"]+)[\'\"]\s*\)', data):
            if not token.startswith('.'):
                continue
            raw_path = Path(relative).parent / token
            normalized = str(Path(__import__('posixpath').normpath(raw_path.as_posix())))
            if not Path(normalized).suffix:
                normalized += '.js'
            closure(normalized)
    closure('geometry-web/space_model_test.js')
    check('recursive local Node require closure complete', sorted(requires) == m['sourceClosure']['canonicalNodeLocalRequireClosure'])
    actors = {x['role']: x for x in r['executionIdentity']['liveBinding']['processes']}
    node, chrome = actors['actual browser parent Node'], actors['actual owned Space browser']
    check('actual live Node ELF identity/command', node['pid'] == r['execution']['pid'] == 280720 and node['sha256'] == r['before']['executables']['node']['sha256'] and node['executableMagicHex'] == '7f454c46' and node['cmdline'] == ['node', 'geometry-web/space_model_test.js'])
    check('actual live Chromium ELF identity/sandbox CDP port', chrome['pid'] == 280730 and chrome['sha256'] == 'd387400aaf740ccb75e5e996a34aa0940e6e97683a4eabd6ae34c1eed6804723' and chrome['executableMagicHex'] == '7f454c46' and '--remote-debugging-port=' + str(r['ownedCdpPort']) in chrome['cmdline'] and not any(x.startswith('--no-sandbox') for x in chrome['cmdline']))
    check('all recorded executor source identities stable before/after', all(r['before'][k] == r['after'][k] for k in ['runnerSha256', 'identityObserverSha256', 'identityProcessSamplerSha256', 'launchAdapterSha256']))
    terminal = h.load(L / 'terminal.json')
    stop = h.load(L / 'owned-stop/terminal-receipt.json')
    launch = h.load(A / 'launch.json')
    check('original lifecycle gate0 stop0 serviceSIGTERM-15 cleanhead', terminal['actualGateExitCode'] == terminal['stopExitCode'] == 0 and terminal['actualServiceExitAfterStop'] == -15 and terminal['headAfter'] == HEAD and terminal['dirtyBefore'] == terminal['dirtyAfter'] == '')
    check('owned detached launch ownPID PGID SID 280637', launch['actualControllerPID'] == launch['actualControllerPGID'] == launch['actualControllerSID'] == 280637 and launch['launchExitCode'] == 0 and launch['fullSHA'] == HEAD and launch['dirty'] == '' and launch['productGateExitCodeAtLaunch'] is None and launch['productCompletionAtLaunch'] == 'pending')
    launch_stat = (A / 'launched-controller.stat.raw').read_text()
    fields = launch_stat.split(')', 1)[1].strip().split()
    check('retained launch raw PGID SID and then-empty streambindings', int(fields[2]) == int(fields[3]) == 280637 and all(x['bytes'] == 0 for x in launch['rawFiles'] if x['path'].endswith('.log')))
    for pid in (280656, 280657):
        row = next(x for x in stop['processObservations'] if x['pid'] == pid)
        stat = (L / ('owned-stop/proc-' + str(pid) + '.stat.raw')).read_bytes()
        check('owned-stop existing zombie exact raw ' + str(pid), row['exists'] is True and row['state'] == stat.decode().split(')', 1)[1].strip().split()[0] == 'Z' and row['statSHA256'] == h.sha(stat))
    check('Node/browser actually absent observation; port refusal distinct', all(next(x for x in stop['processObservations'] if x['pid'] == pid)['exists'] is False for pid in (280720, 280730)) and stop['portObservation']['accepting'] is False)
    add = h.load(S / 'geometry-ui-verification/supplementary-validation-f3b-durable-space-launch-addendum.json')
    kernel = add['currentControllerKernelObservation']
    fields = kernel['raw'].split(')', 1)[1].strip().split()
    check('retained kernel wait status actually0 controllerexit0 distinctlaunchnull', kernel['exists'] is True and fields[0] == kernel['state'] == 'Z' and int(fields[49]) == kernel['kernelWaitStatus'] == 0 and kernel['actualControllerExitFromKernel'] == 0 and h.sha(kernel['raw'].encode()) == kernel['sha256'] and m['originalLifecycle']['actualControllerExitCode'] == 0 and m['detachedLaunch']['originalFinalControllerExitRecordedAtLaunch'] is None)
    prep = h.load(P / 'independent-launch-addendum/preparation-review.public.json')
    check('original static literal false preserved and addendum AST classification separate', prep['checks']['no product/browser/service execution in preparer'] is False and prep['allStaticChecksPassed'] is False and add['checks']['preparer AST contains no product/browser/service call'] is True and add['exitCode'] == 0)
    review = h.load(S / 'geometry-ui-verification/supplementary-validation-f3b-durable-full-space.json')
    check('actual original39integrity +7acceptance checks, addendum19, notproduct', len(review['integrityChecks']) == 39 and len(review['acceptanceChecks']) == 7 and review['exitCode'] == 0 and len(add['checks']) == 19 and all(add['checks'].values()) and all(x['countsAreProductAssertions'] is False for x in [m['independentMetadataReviews']['spaceCensus'], m['independentMetadataReviews']['launchAddendum']]))
    build = h.load(D / 'f3b-durable-space-package-build-v2.json')
    outer = h.load(D / 'f3b-durable-space-builder-execution-v2.json')
    check('actual package builder/outer0 ownUID1000 not originalruntimeUID', build['actualExitCode'] == outer['actualExitCode'] == 0 and outer['actualUID'] == m['environmentLimits']['actualPackagingUID'] == 1000 and m['environmentLimits']['originalProductUIDRecordedInReceipt'] is None)
    for source in build['publicationSourceClosure']:
        f = Path(source['path'])
        check('actual publication source original identity ' + f.name, f.stat().st_size == source['bytes'] and h.sha(f.read_bytes()) == source['sha256'])
    for source in build['inputFiles'] + build['rawStreams'] + outer['rawStreams']:
        f = Path(source['path'])
        check('sealed publication command inputs/raw identity ' + f.name, f.stat().st_size == source['bytes'] and h.sha(f.read_bytes()) == source['sha256'])
    imp = m['publicationImplementation']
    check('actual bounded v8 engine adapter builder identities', imp['originalV8SHA256'] == h.sha((D / 'prepare_ui_history_packet_v8.py').read_bytes()) and imp['actualBuilderOriginalSHA256'] == h.sha((D / 'prepare_f3b_durable_space_packet_v2.py').read_bytes()) and imp['actualAdapterOriginalSHA256'] == h.sha((D / 'f3b-durable-space-adapter-v2.py').read_bytes()))
    check('no saved source snapshots overwritten originalbeforeafter', outer['savedSourceSnapshotsBefore'] == outer['savedSourceSnapshotsAfter'])
    check('noall43/fullCDP/golden/allSpace claim no releaseApproval', all(m['productGate'][k] is False for k in ['goldenCompared', 'allSpaceAcceptance', 'fullCDPAcceptance', 'all43Acceptance']) and m['releaseApproved'] is False)
    check('33 sealed largePNG omitted no mutable assembly PNG', not any(x.endswith('.png') for x in census) and len([x for x in G.rglob('*.png') if x.stat().st_size > 16384]) == 33)
    check('all public files fully accounted and README exact', set(paths) == reviewed and (P / 'README.md').read_bytes() == (D / 'f3b-durable-space-README-v2.md').read_bytes(), sorted(set(paths) - reviewed))
    check('manifest and parser source immutable throughout', h.sha((P / 'manifest.json').read_bytes()) == MANIFEST and h.sha(HELPER.read_bytes()) == '0c7d16eac138b21ec9a2d70235e5e8ba8b57336a5c449cea2e66aa6583f35e60')
    failures = [x for x in CHECKS if not x['passed']]
    stream = ''.join(('PASS ' if x['passed'] else 'FAIL ') + x['name'] + '\n' for x in CHECKS)
    (OUT / 'command.raw.log').write_text(stream)
    report = {'schema': 'geometry-space-v2-independent-publication-review/1', 'actor': '/root/publication_final_review/assembly_packet_review', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': [sys.executable, '-B', str(Path(__file__).resolve())], 'actualPython': str(Path(sys.executable).resolve()), 'actualPythonSHA256': h.sha(Path(sys.executable).resolve().read_bytes()), 'reviewSourceSHA256': h.sha(Path(__file__).read_bytes()), 'parserHelperSourceSHA256': h.sha(HELPER.read_bytes()), 'actualExitCode': 1 if failures else 0, 'passedMetadataChecks': len(CHECKS) - len(failures), 'failedMetadataChecks': len(failures), 'manifestSHA256': MANIFEST, 'testedProductSHA': HEAD, 'productOrBrowserOrServiceExecuted': False, 'packetOrOriginalsChanged': False, 'repositoryOrGitHubWritten': False, 'countsAreProductTests': False, 'rawLog': {'path': str(OUT / 'command.raw.log'), 'bytes': (OUT / 'command.raw.log').stat().st_size, 'sha256': h.sha((OUT / 'command.raw.log').read_bytes())}, 'findings': failures, 'checks': CHECKS}
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:report[k] for k in ['actualExitCode', 'passedMetadataChecks', 'failedMetadataChecks', 'reviewSourceSHA256', 'rawLog', 'findings']}))
    return report['actualExitCode']


if __name__ == '__main__':
    raise SystemExit(main())
