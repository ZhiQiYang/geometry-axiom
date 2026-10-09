"""Readonly provenance closure supplement; no source/reviewer execution."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import sys

S = Path('<workspace-path>')
D = S / 'geometry-delivery-closeout-20261009'
P = D / 'f3b-durable-space-public-v2'
G = S / 'geometry-root-f3b82857-durable-full-space-gate'
L = S / 'geometry-root-f3b82857-durable-full-space-lifecycle'
A = S / 'geometry-root-f3b82857-durable-full-space-detached-launch'
H = S / 'geometry-assembly-packet-review-v4-independent.py'
spec = importlib.util.spec_from_file_location('readonly_helpers', H)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
OUT = S / 'geometry-space-v2-independent-source-bindings-review'


def main():
    assert not OUT.exists()
    OUT.mkdir()
    checks = []
    def check(n, v):
        checks.append({'name': n, 'passed': bool(v)})
    m, r = h.load(P / 'manifest.json'), h.load(G / 'receipt.json')
    terminal, stop, launch = h.load(L / 'terminal.json'), h.load(L / 'owned-stop/terminal-receipt.json'), h.load(A / 'launch.json')
    review = h.load(S / 'geometry-ui-verification/supplementary-validation-f3b-durable-full-space.json')
    add = h.load(S / 'geometry-ui-verification/supplementary-validation-f3b-durable-space-launch-addendum.json')
    prep = h.load(S / 'geometry-ui-verification/f3b-source-and-census-preparation/durable-census-preparation-review.json')
    refs = {Path(x['publicPath']).name: x for x in m['sourceCopies'] if x['role'] == 'recorded scratch executor/reviewer source'}
    expected = {
        'run_full_space_identity.py': r['before']['runnerSha256'],
        'space_execution_identity.py': r['before']['identityObserverSha256'],
        'cdp_execution_identity_v2.py': r['before']['identityProcessSamplerSha256'],
        'sandbox-launch.cjs': r['before']['launchAdapterSha256']['sandbox-launch.cjs'],
        'sitecustomize.py': r['before']['launchAdapterSha256']['sitecustomize.py'],
        'geometry-stage-launch.py': terminal['launchSHA256'],
        'geometry-stage-stop.py': stop['helperSHA256'],
        'geometry-owned-integration-lifecycle-f3b-v2.py': terminal['controllerSHA256'],
        'geometry-stop-with-terminal-receipt-f3b.py': stop['wrapperSHA256'],
        'geometry-launch-detached-owned-integration-f3b.py': launch['launcherSourceSHA256'],
        'validate_f3b_full_integration.py': review['reviewExecutor']['scriptSHA256'],
    }
    for path, digest in prep['sourceFiles'].items():
        name = Path(path).name
        if name in refs:
            expected[name] = digest
    for path, digest in add['sourceHashes'].items():
        name = Path(path).name
        if name in refs:
            expected[name] = digest
    check('exact14 scratchsource references and recorded hash-role pins', len(refs) == len(expected) == 14 and set(refs) == set(expected))
    for name, digest in expected.items():
        ref = refs[name]
        check('original role pin vs public source original identity ' + name, ref['originalSHA256'] == digest and ref['originalExecutionSnapshotCaptured'] is False and ref['publishedCopyWasExecuted'] is False)
    extras = h.load(D / 'f3b-durable-space-extra-v2.json')
    destination_original = {x['destination']: Path(x['path']) for x in extras if Path(x['path']).is_file()}
    for ref in m['sourceAndArtifactByteBindings']:
        original = destination_original[ref['publicPath']]
        data = original.read_bytes()
        check('exact original path hash and original byte association ' + ref['publicPath'], h.sha(str(original).encode()) == ref['originalPathSHA256'] and h.sha(data) == ref['originalSHA256'] and len(data) == ref['originalBytes'] and original.name == ref['originalBasename'] and ref['publishedCopyWasExecuted'] is False)
    first = h.load(S / 'geometry-space-v2-independent-publication-review/report.json')
    check('first actual1111 metadata0 findings exit0 retained', first['actualExitCode'] == 0 and first['passedMetadataChecks'] == 1111 and first['failedMetadataChecks'] == 0 and h.sha((S / 'geometry-space-v2-independent-publication-review/command.raw.log').read_bytes()) == first['rawLog']['sha256'])
    prior = h.load(D / 'f3b-durable-space-package-build-v1.json')
    check('original preparation package-v1 exit1 remains exit1', prior['actualExitCode'] == 1 and prior['productExecuted'] is False and prior['serviceOrBrowserUsed'] is False)
    for role in ['rawStreams', 'inputFiles', 'publicationSourceClosure']:
        for source in prior[role]:
            f = Path(source['path'])
            check('retained prior-v1 original identity ' + f.name, f.stat().st_size == source['bytes'] and h.sha(f.read_bytes()) == source['sha256'])
    check('manifest immutable exact final-ready Spacev2', h.sha((P / 'manifest.json').read_bytes()) == 'dbd3e468c878b2bea7c48b54ea578a795cbdb142939b115c903c732461a4bd4a')
    raw = ''.join(('PASS ' if x['passed'] else 'FAIL ') + x['name'] + '\n' for x in checks)
    (OUT / 'command.raw.log').write_text(raw)
    failures = [x for x in checks if not x['passed']]
    result = {'schema': 'geometry-space-v2-independent-source-binding-review/1', 'actor': '/root/publication_final_review/assembly_packet_review', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': [sys.executable, '-B', str(Path(__file__).resolve())], 'actualPython': str(Path(sys.executable).resolve()), 'actualPythonSHA256': h.sha(Path(sys.executable).resolve().read_bytes()), 'reviewSourceSHA256': h.sha(Path(__file__).read_bytes()), 'parserHelperSourceSHA256': h.sha(H.read_bytes()), 'actualExitCode': 1 if failures else 0, 'passedMetadataChecks': len(checks) - len(failures), 'failedMetadataChecks': len(failures), 'countsAreProductTests': False, 'productOrBrowserOrServiceExecuted': False, 'repoOrGitHubWritten': False, 'packetOrOriginalsChanged': False, 'rawLog': {'path': str(OUT / 'command.raw.log'), 'sha256': h.sha((OUT / 'command.raw.log').read_bytes()), 'bytes': (OUT / 'command.raw.log').stat().st_size}, 'firstReview': {'path': str(S / 'geometry-space-v2-independent-publication-review/report.json'), 'sha256': h.sha((S / 'geometry-space-v2-independent-publication-review/report.json').read_bytes()), 'actualExitCode': 0}, 'findings': failures, 'checks': checks}
    (OUT / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:result[k] for k in ['actualExitCode', 'passedMetadataChecks', 'failedMetadataChecks', 'reviewSourceSHA256', 'rawLog', 'findings']}))
    return result['actualExitCode']


if __name__ == '__main__':
    raise SystemExit(main())
