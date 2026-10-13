"""Independent readonly audit of the final original ASM v4 public packet.

Does not import/run the packet builder, product sources, browsers, services or
GitHub. Writes only this actor's fresh scratch report and raw audit stream.
"""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import re
import subprocess
import sys
import zipfile

S = Path('<workspace-path>')
D = S / 'geometry-delivery-closeout-20261009'
P = D / 'f3b-original-assembly-public-v4'
G = S / 'geometry-root-f3b82857-original-assembly-gate'
L = S / 'geometry-root-f3b82857-original-assembly-lifecycle'
T = S / 'geometry-root-f3b82857-original-assembly-stop-recovery'
REPO = Path('<workspace-path>')
HEAD = 'f3b8285729b42cd22451c98cba1e2ec4514517f3'
MANIFEST_SHA = 'bebeec6f3074b2c8cad4ab71c90d7decd3287db7b1b5dfa25444d83b6add9d64'
OUT = S / 'geometry-assembly-v4-independent-publication-review'
CHECKS = []
TOKEN = re.compile(r'/workspace/[A-Za-z0-9._~%+@:=/\-]+|/tmp/geometry-[A-Za-z0-9._~%+@:=/\-]+|/opt/codex/[A-Za-z0-9._~%+@:=/\-]+')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(name, condition, details=None):
    CHECKS.append({'name': name, 'passed': bool(condition), 'details': details})


def unique(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError('duplicate JSON key: ' + k)
        result[k] = v
    return result


def loads(data):
    return json.loads(data, object_pairs_hook=unique)


def load(path):
    return loads(path.read_bytes())


def project_text(text):
    def replacement(m):
        s = m.group(0)
        return '<workspace-path>' if s.startswith('/workspace/') else '<isolated-test-directory>' if s.startswith('/tmp/') else '<execution-runtime-path>'
    return TOKEN.sub(replacement, text)


def project(value):
    if isinstance(value, dict):
        labels = [project_text(k) for k in value]
        counts = collections.Counter(labels)
        result = {}
        for k, v in value.items():
            label = project_text(k)
            if counts[label] > 1:
                label += '|basename=' + Path(k).name + '|originalKeySha256=' + sha(k.encode())
            assert label not in result
            result[label] = project(v)
        assert len(result) == len(value)
        return result
    if isinstance(value, list):
        return [project(v) for v in value]
    return project_text(value) if isinstance(value, str) else value


def git(args):
    return subprocess.check_output(['git', *args], cwd=REPO)


def equal_projection(original, public, suffix, receipt_footer=False):
    if original == public:
        return True
    if suffix in {'.json', '.stacks'}:
        actual = loads(public)
        if receipt_footer:
            actual.pop('publicProjection', None)
        return project(loads(original)) == actual
    if suffix in {'.jsonl', '.trace', '.network'}:
        return [project(loads(x)) for x in original.splitlines() if x.strip()] == [loads(x) for x in public.splitlines() if x.strip()]
    return project_text(original.decode()).encode() == public


def main():
    assert not OUT.exists(), 'fresh report directory required'
    OUT.mkdir()
    before_git = {'head': git(['rev-parse', 'HEAD']).decode().strip(), 'status': git(['status', '--short']).decode()}
    m = load(P / 'manifest.json')
    check('final-ready manifest exact SHA256', sha((P / 'manifest.json').read_bytes()) == MANIFEST_SHA)
    entries = m['publicFiles']
    paths = [x['path'] for x in entries]
    census = {x.relative_to(P).as_posix() for x in P.rglob('*') if x.is_file()}
    check('exact 199 listed + manifest 200 files', len(paths) == len(set(paths)) == 199 and census == set(paths) | {'manifest.json'})
    for row in entries:
        f = P / row['path']
        check('safe relative path ' + row['path'], not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts and not f.is_symlink())
        data = f.read_bytes()
        check('public bytes and SHA256 ' + row['path'], len(data) == row['bytes'] and sha(data) == row['sha256'])
        if f.suffix in {'.json', '.jsonl', '.trace', '.network', '.stacks'}:
            try:
                if f.suffix in {'.json', '.stacks'}:
                    loads(data)
                else:
                    for line in data.splitlines():
                        if line.strip():
                            loads(line)
                check('unique structured keys ' + row['path'], True)
            except Exception as exc:
                check('unique structured keys ' + row['path'], False, repr(exc))
        if f.suffix in {'.zip', '.gcanvas'}:
            try:
                with zipfile.ZipFile(f) as z:
                    names = z.namelist()
                    assert len(names) == len(set(names))
                    assert all(not Path(x).is_absolute() and '..' not in Path(x).parts for x in names)
                    assert z.testzip() is None
                    for name in names:
                        if name.endswith('.json'):
                            loads(z.read(name))
                check('archive member safety CRC JSON ' + row['path'], True)
            except Exception as exc:
                check('archive member safety CRC JSON ' + row['path'], False, repr(exc))

    originals = {}
    candidates = [G, L, T]
    for extra in load(D / 'f3b-original-assembly-extra-v2.json'):
        candidates.append(Path(extra['path']))
    for candidate in candidates:
        files = [candidate] if candidate.is_file() else [f for f in candidate.rglob('*') if f.is_file()]
        for f in files:
            data = f.read_bytes()
            originals.setdefault(sha(data), (f, data))

    evidence = m['rounds'][0]['rawEvidence'] + m['historyReviewsAndExecutorSources'] + m['fullTestedCommitSourceCopies']
    reviewed_paths = set()
    for row in evidence:
        path = row['path']
        public = (P / path).read_bytes()
        if 'repositoryPath' in row:
            original = git(['show', row['sourceHead'] + ':' + row['repositoryPath']])
            provenance = 'readonly full SHA git object'
        else:
            binding = originals.get(row['originalSha256'])
            if binding is None:
                check('original retained identity ' + path, False, row['originalSha256'])
                continue
            provenance, original = binding
        check('original bytes and SHA256 ' + path, len(original) == row['originalBytes'] and sha(original) == row['originalSha256'])
        check('one-to-one projection all non-token characters ' + path, equal_projection(original, public, Path(path).suffix), {'original': str(provenance), 'byteIdentical': original == public})
        check('projection markers accurate ' + path, row['byteIdenticalOriginal'] == (original == public) and row['publicProjection'] == (original != public))
        reviewed_paths.add(path)

    r = load(G / 'receipt.json')
    pr = load(P / m['rounds'][0]['receiptPath'])
    check('receipt public projection preserves full original keys and associations', equal_projection((G / 'receipt.json').read_bytes(), (P / m['rounds'][0]['receiptPath']).read_bytes(), '.json', True))
    check('receipt explicit original provenance', pr['publicProjection']['originalSha256'] == sha((G / 'receipt.json').read_bytes()) and pr['publicProjection']['originalBytes'] == (G / 'receipt.json').stat().st_size)
    canonical_rows = [loads(line[len('CDP_RESULT '):]) for line in (G / 'command.log').read_text().splitlines() if line.startswith('CDP_RESULT ')]
    check('exact one canonical original result', len(canonical_rows) == 1)
    c = canonical_rows[0]
    check('canonical public matches original projected result', project(c) == load(P / 'rounds/f3b-original-assembly-completed-partial/canonical-original-result.public.json'))
    check('original partial 150/0/0 P77 134 P82 16 no golden', c['completed'] is True and c['passedAssertions'] == 150 and c['failedAssertions'] == 0 and c['skipped'] == [] and c['sections'] == {'P77': 134, 'P82': 16} and c['scope']['mode'] == 'partial' and c['scope']['filters'] == ['GEOMETRY_ASSEMBLY_ONLY'] and c['scope']['modifiers'] == [] and c['goldenCompare'] == 'not compared (partial mode)')
    check('actual canonical Node and gate exit 0 execution verified', r['execution']['exitCode'] == r['gateExitCode'] == 0 and r['executionVerified'] is True and not r['execution']['timedOut'] and not r['execution']['interrupted'])
    for phase in ('before', 'after'):
        check('original ' + phase + ' full clean f3 SHA', r[phase]['git']['head'] == HEAD and r[phase]['git']['status'] == '' and r[phase]['runtime']['fresh'] is True)
    captured = r['before']['sourceSha256']
    check('all 125 captured web maps match before/after', len(captured) == 125 and captured == r['after']['sourceSha256'])
    for relative, digest in captured.items():
        source = G / 'executed-harness-sources' / relative
        copy = P / 'executed-source-bytes' / digest / Path(relative).name
        check('actual captured source and public bytes ' + relative, sha(source.read_bytes()) == digest and copy.read_bytes() == source.read_bytes())
    live = r['executionIdentity']['liveBinding']
    actors = {a['role']: a for a in live['processes']}
    node = actors['actual browser parent Node']
    chrome = actors['actual CDP_SCOPE Chromium main process']
    check('actual live Node ELF PID/hash command preserved', node['pid'] == r['execution']['pid'] == 252395 and node['executableMagicHex'] == '7f454c46' and node['sha256'] == r['before']['executables']['node']['sha256'] and node['cmdline'] == ['node', 'geometry-web/cdp_test.js'])
    check('actual live Chrome ELF CDP_SCOPE PID preserved', chrome['pid'] == c['scope']['browserPid'] == 252403 and chrome['executableMagicHex'] == '7f454c46' and chrome['sha256'] == 'd387400aaf740ccb75e5e996a34aa0940e6e97683a4eabd6ae34c1eed6804723' and not any(x.startswith('--no-sandbox') for x in chrome['cmdline']))
    check('source maps runner observer adapters stable', all(r['before'][k] == r['after'][k] for k in ['runnerSha256', 'identityObserverSha256', 'launchAdapterSha256']))

    error = load(L / 'controller-error.json')
    recovery = load(T / 'terminal-receipt.json')
    observation = load(S / 'geometry-root-f3b82857-original-assembly-recovery-observation.json')
    check('original controller failure retained missing terminal', error['actualGateExitCode'] == 0 and error['stopExitCode'] == 1 and '9eb670110379ec0d726914f3e5b2d8e7237f2b9c' in error['controllerError'] and not (L / 'terminal.json').exists() and not (P / 'original-owned-lifecycle/terminal.json').exists())
    check('parent-reported original controller1 distinct provenance', observation['originalLifecycleActualExitCode'] == 1 and '70298' in observation['originalLifecycleExitSource'] and m['originalLifecycle']['actualControllerExitCodeFromOriginalFiles'] is None and m['originalLifecycle']['parentReportedActualControllerExitCode'] == 1)
    check('original service actual exit unknown retained', observation['originalServiceActualExitCode'] is None and m['originalLifecycle']['originalServiceActualExitCode'] is None)
    check('separate recovery stop0 no replacement no rerun', recovery['exitCode'] == 0 and recovery['productTestExecution'] is False and observation['productTestsRepeatedForStopRepair'] is False and m['separateStopRecovery']['replacesOriginalLifecycleTerminal'] is False)
    for pid in (252331, 252332, 252403):
        row = next(x for x in recovery['processObservations'] if x['pid'] == pid)
        stat = (T / ('proc-' + str(pid) + '.stat.raw')).read_bytes()
        state = stat.decode().split(')', 1)[1].strip().split()[0]
        check('existing zombie Z exact original raw PID ' + str(pid), row['exists'] is True and row['state'] == state == 'Z' and row['statSHA256'] == sha(stat))
    check('only Node absent at recovery, port refused', next(x for x in recovery['processObservations'] if x['pid'] == 252395)['exists'] is False and recovery['portObservation']['accepting'] is False)
    check('seven helper and seven dependency references no historical execution attestation', len([x for x in m['sourceAndArtifactByteBindings'] if x['role'] == 'exact fullSHA committed helper/dependency source reference']) == 14 and m['sourceClosure']['committedHelperReferenceFiles'] == m['sourceClosure']['committedDependencyReferenceFiles'] == 7 and all(x['publishedCopyWasExecuted'] is False for x in m['sourceAndArtifactByteBindings']))
    check('publication builder real v8 0209 source identity', sha((D / 'prepare_ui_history_packet_v8.py').read_bytes()) == m['publicationImplementation']['builderOriginalSHA256'] == '0209c3f9467a9b63d6c4ae3ca74e4d14cf48a3f51dd31e1ec1fa594f15a0f065')
    check('configuration preparer identity separate v2', sha((D / 'prepare_f3b_original_assembly_packet_v2.py').read_bytes()) == m['publicationImplementation']['configurationPreparerOriginalSHA256'])
    check('no manufactured screenshots no full acceptance release approval', not any(x.endswith('.png') for x in census) and m['productGate']['fullAcceptance'] is False and m['releaseApproved'] is False and m['historicalFullCdp'] is None and m['windows173'] is None and all(v is False for v in m['independentOtherScopes'].values()))
    review = load(P / 'independent-assembly-review/review.public.json')
    check('prior35 checks metadata scope actual0 not added product', review['passedIntegrityChecks'] == 35 and review['failedIntegrityChecks'] == 0 and review['exitCode'] == 0 and m['independentMetadataReview']['countsAreProductAssertions'] is False and m['independentMetadataReview']['browserExecuted'] is False)
    reviewed_paths.update([m['rounds'][0]['receiptPath'], 'rounds/f3b-original-assembly-completed-partial/canonical-original-result.public.json', 'README.md'])
    check('all public files accounted by evidence/source/canonical/receipt/README', set(paths) == reviewed_paths, sorted(set(paths) - reviewed_paths))
    check('README final original exact bytes', (P / 'README.md').read_bytes() == (D / 'f3b-original-assembly-README-v4.md').read_bytes())
    after_git = {'head': git(['rev-parse', 'HEAD']).decode().strip(), 'status': git(['status', '--short']).decode()}
    check('packet manifest immutable throughout audit', sha((P / 'manifest.json').read_bytes()) == MANIFEST_SHA)
    raw = ''.join(('PASS ' if x['passed'] else 'FAIL ') + x['name'] + '\n' for x in CHECKS)
    raw_path = OUT / 'command.raw.log'
    raw_path.write_text(raw)
    failures = [x for x in CHECKS if not x['passed']]
    report = {'schema': 'geometry-assembly-v4-independent-publication-review/1', 'actor': '/root/publication_final_review/assembly_packet_review', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'packet': str(P), 'manifestSHA256': MANIFEST_SHA, 'testedProductSHA': HEAD, 'command': [sys.executable, '-B', str(Path(__file__).resolve())], 'actualPython': str(Path(sys.executable).resolve()), 'actualPythonSHA256': sha(Path(sys.executable).resolve().read_bytes()), 'reviewSourceSHA256': sha(Path(__file__).read_bytes()), 'actualExitCode': 1 if failures else 0, 'passedMetadataChecks': len(CHECKS) - len(failures), 'failedMetadataChecks': len(failures), 'countsAreProductTests': False, 'productExecuted': False, 'browserOrServiceUsed': False, 'repoOrGitHubWritten': False, 'originalsRewritten': False, 'beforeGitObservation': before_git, 'afterGitObservation': after_git, 'rawLog': {'path': str(raw_path), 'sha256': sha(raw_path.read_bytes()), 'bytes': raw_path.stat().st_size}, 'findings': failures, 'checks': CHECKS}
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['actualExitCode', 'passedMetadataChecks', 'failedMetadataChecks', 'reviewSourceSHA256', 'rawLog', 'findings']}))
    return report['actualExitCode']


if __name__ == '__main__':
    raise SystemExit(main())
