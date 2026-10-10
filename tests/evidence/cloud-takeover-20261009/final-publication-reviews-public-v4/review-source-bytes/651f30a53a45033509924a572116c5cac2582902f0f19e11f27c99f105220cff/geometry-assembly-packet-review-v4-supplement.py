"""Readonly supplement; preserves first ASM review and corrects assumptions.

This review does not execute/import packaging or product source. The prior
configuration provenance label remains explicitly unresolved pending its author.
"""
from pathlib import Path
import datetime
import hashlib
import json
import re
import sys

S = Path('<workspace-path>')
D = S / 'geometry-delivery-closeout-20261009'
P = D / 'f3b-original-assembly-public-v4'
G = S / 'geometry-root-f3b82857-original-assembly-gate'
FIRST = S / 'geometry-assembly-v4-independent-publication-review'
OUT = S / 'geometry-assembly-v4-independent-publication-supplement'
TOKEN = re.compile(r'/workspace/[A-Za-z0-9._~%+@:=/\-]+|/tmp/geometry-[A-Za-z0-9._~%+@:=/\-]+|/opt/codex/[A-Za-z0-9._~%+@:=/\-]+')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(p):
    return json.loads(p.read_text())


def project(data):
    def replace(m):
        return '<workspace-path>' if m.group().startswith('/workspace/') else '<isolated-test-directory>' if m.group().startswith('/tmp/') else '<execution-runtime-path>'
    return TOKEN.sub(replace, data.decode()).encode()


def main():
    assert not OUT.exists()
    OUT.mkdir()
    checks = []
    def check(n, v, d=None):
        checks.append({'name': n, 'passed': bool(v), 'details': d})
    m = load(P / 'manifest.json')
    r = load(G / 'receipt.json')
    previous = load(FIRST / 'report.json')
    first_source = S / 'geometry-assembly-packet-review-v4-independent.py'
    check('first actual1152/3 exit1 and source/raw immutable', previous['actualExitCode'] == 1 and previous['passedMetadataChecks'] == 1152 and previous['failedMetadataChecks'] == 3 and sha(first_source.read_bytes()) == previous['reviewSourceSHA256'] and sha((FIRST / 'command.raw.log').read_bytes()) == previous['rawLog']['sha256'])
    records = {x['artifactRelativePath'].removeprefix('executed-harness-sources/'): x for x in m['rounds'][0]['rawEvidence'] if x.get('artifactRelativePath', '').startswith('executed-harness-sources/')}
    check('exact125 public capture refs original before/after maps', len(records) == len(r['before']['sourceSha256']) == 125 and r['before']['sourceSha256'] == r['after']['sourceSha256'] and set(records) == set(r['before']['sourceSha256']))
    projected = []
    for relative, digest in r['before']['sourceSha256'].items():
        ref = records[relative]
        original = (G / 'executed-harness-sources' / relative).read_bytes()
        public = (P / ref['path']).read_bytes()
        if ref['publicProjection']:
            projected.append(relative)
            valid = not ref['byteIdenticalOriginal'] and public == project(original)
        else:
            valid = ref['byteIdenticalOriginal'] and public == original
        check('original captured source identity and declared public projection ' + relative, sha(original) == digest == ref['originalSha256'] and len(original) == ref['originalBytes'] and sha(public) == ref['sha256'] and len(public) == ref['bytes'] and valid)
    check('exact123 original copies and2 explicit bounded path projections', sorted(projected) == ['geometry-web/model_update_browser_check.js', 'geometry-web/source_inspector_browser_check.js'])
    oldbuild = load(D / 'f3b-original-assembly-package-build-v2.json')
    implementation = m['publicationImplementation']
    config_generator = sha((D / 'prepare_f3b_original_assembly_packet_v2.py').read_bytes())
    prior_generic = sha((D / 'prepare_ui_history_packet_v7.py').read_bytes())
    current_generic = sha((D / 'prepare_ui_history_packet_v8.py').read_bytes())
    check('new v8 publication builder correctly pinned', implementation['builderOriginalSHA256'] == current_generic == '0209c3f9467a9b63d6c4ae3ca74e4d14cf48a3f51dd31e1ec1fa594f15a0f065')
    check('superseded v2 configuration generator correctly retained distinct', implementation['supersededV2BuilderOriginalSHA256'] == config_generator == oldbuild['builderSHA256'])
    check('configurationPreparer label actually resolves to prior generic v7', implementation['configurationPreparerOriginalSHA256'] == prior_generic == oldbuild['preparerSHA256'] == '103735521e97a3c4d4287b8cb9b738eb7c1deb91c3d4248c330955288abc35a8')
    check('original build command confirms prior generic v7 packaging only', oldbuild['actualExitCode'] == 0 and Path(oldbuild['command'][2]).name == 'prepare_ui_history_packet_v7.py' and oldbuild['command'][oldbuild['command'].index('--extra-config') + 1] == str(D / 'f3b-original-assembly-config-v2.json'))
    raw = ''.join(('PASS ' if x['passed'] else 'FAIL ') + x['name'] + '\n' for x in checks)
    (OUT / 'command.raw.log').write_text(raw)
    failures = [x for x in checks if not x['passed']]
    report = {'schema': 'geometry-assembly-v4-independent-publication-supplement/1', 'actor': '/root/publication_final_review/assembly_packet_review', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': [sys.executable, '-B', str(Path(__file__).resolve())], 'actualPython': str(Path(sys.executable).resolve()), 'actualPythonSHA256': sha(Path(sys.executable).resolve().read_bytes()), 'reviewSourceSHA256': sha(Path(__file__).read_bytes()), 'actualExitCode': 1 if failures else 0, 'passedMetadataChecks': len(checks) - len(failures), 'failedMetadataChecks': len(failures), 'countsAreProductTests': False, 'productOrBrowserOrServiceExecuted': False, 'repositoryOrGitHubWritten': False, 'packetOrOriginalsChanged': False, 'manifestSHA256': sha((P / 'manifest.json').read_bytes()), 'originalReview': {'path': str(FIRST / 'report.json'), 'sha256': sha((FIRST / 'report.json').read_bytes()), 'actualExitCode': 1, 'passedMetadataChecks': 1152, 'failedMetadataChecks': 3}, 'correctedValidatorAssumptions': [{'priorFinding': 'actual captured source and public bytes geometry-web/model_update_browser_check.js', 'classification': 'validator assumed byte-identical public copy despite explicit legal path projection; original capture and all non-token characters valid'}, {'priorFinding': 'actual captured source and public bytes geometry-web/source_inspector_browser_check.js', 'classification': 'validator assumed byte-identical public copy despite explicit legal path projection; original capture and all non-token characters valid'}], 'remainingProvenanceLabelQuestion': {'field': 'publicationImplementation.configurationPreparerOriginalSHA256', 'actualSource': 'prepare_ui_history_packet_v7.py', 'actualSourceSHA256': prior_generic, 'configurationGeneratingSource': 'prepare_f3b_original_assembly_packet_v2.py', 'configurationGeneratingSourceSHA256': config_generator, 'status': 'Requires packaging author semantics; not presumed to name the configuration-generating executor. Packet final acceptance withheld pending precise label explanation or fresh corrected packet.'}, 'finalPacketAcceptance': False, 'rawLog': {'path': str(OUT / 'command.raw.log'), 'sha256': sha((OUT / 'command.raw.log').read_bytes()), 'bytes': (OUT / 'command.raw.log').stat().st_size}, 'findings': failures, 'checks': checks}
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:report[k] for k in ['actualExitCode', 'passedMetadataChecks', 'failedMetadataChecks', 'reviewSourceSHA256', 'rawLog', 'finalPacketAcceptance', 'remainingProvenanceLabelQuestion']}))
    return report['actualExitCode']


if __name__ == '__main__':
    raise SystemExit(main())
