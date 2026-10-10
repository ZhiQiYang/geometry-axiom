"""Readonly schema-aware correction of the reviewer golden-map assumption."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys

S = Path('<workspace-path>')
D = S / 'geometry-delivery-closeout-20261009'
P = D / 'f3b-durable-full-public-v3'
G = S / 'geometry-root-f3b82857-durable-full-cdp-gate'
PREV = S / 'geometry-formal-full-v3-source-actor-closure-review'
OUT = S / 'geometry-formal-full-v3-golden-envelope-supplement'
HEAD = 'f3b8285729b42cd22451c98cba1e2ec4514517f3'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    assert not OUT.exists()
    OUT.mkdir()
    previous = json.loads((PREV / 'report.json').read_text())
    r = json.loads((G / 'receipt.json').read_text())
    m = json.loads((P / 'manifest.json').read_text())
    command = ['git', 'show', HEAD + ':geometry-web/cdp_sections.golden.json']
    golden_raw = subprocess.check_output(command, cwd='<workspace-path>')
    golden = json.loads(golden_raw)
    c = r['evidence']['canonicalResult']
    checks = []
    def check(n, v):
        checks.append({'name': n, 'passed': bool(v)})
    check('prioractual330/1 exit1 unchanged report', sha((PREV / 'report.json').read_bytes()) == '330767a7e17c98c8307c65c3cc6f4cac5ae319c3cba41f594cb51bf2fe92cc10' and previous['actualExitCode'] == 1 and previous['passedMetadataChecks'] == 330 and previous['failedMetadataChecks'] == 1)
    check('prior solefinding is golden-envelope reviewerassumption', previous['findings'][0]['name'] == 'original frozen golden84 matched exact actualcanonicalsections')
    check('prioractual source/raw hashes retained', sha((S / 'geometry-formal-full-v3-source-actor-closure-review.py').read_bytes()) == previous['reviewSourceSHA256'] and sha((PREV / 'command.raw.log').read_bytes()) == previous['rawLog']['sha256'])
    check('exact frozen golden e3e742 original bytes unmodified', sha(golden_raw) == 'e3e742ec3d731e701afc22149efa9bc11cf6506340715176175e594c94778bd9' and golden_raw == (P / 'committed-f3-source-reference/geometry-web/cdp_sections.golden.json').read_bytes())
    check('original golden envelope schema mode total exact', set(golden) == {'schema', 'mode', 'total', 'sections'} and golden['schema'] == 'geometry-cdp-sections/1' and golden['mode'] == 'full' and golden['total'] == 2207)
    check('all84 actualcanonical sections exactly match originalgolden sections', c['sections'] == golden['sections'] and len(golden['sections']) == len(c['sections']) == 84 and sum(golden['sections'].values()) == c['passedAssertions'] == 2207)
    check('actual original gate reportedgolden matched on completedunfilteredfull', c['goldenCompare'] == 'matched' and c['completed'] is True and c['scope']['mode'] == 'full' and c['scope']['filters'] == c['scope']['modifiers'] == [] and c['failedAssertions'] == 0 and c['skipped'] == [])
    check('actual original Node/gate0 originalSHA retained', r['execution']['exitCode'] == r['gateExitCode'] == 0 and sha((G / 'receipt.json').read_bytes()) == '38bda376c1aed0faf20b02d611747b145eaf594f0d77d037dba9e598ef3d2d35' and r['before']['git']['head'] == r['after']['git']['head'] == HEAD and r['before']['git']['status'] == r['after']['git']['status'] == '')
    check('new metadata does not change product testcount2207 or expectedexception1', m['formalFullResult']['passed'] == 2207 and m['formalFullResult']['originalGoldenSectionsMatched'] == 84 and m['formalFullResult']['expectedOriginalFbAutoProbeExceptions'] == c['uncaughtBrowserExceptions'] == 1)
    check('manifest immutable exact formalpublicv3', sha((P / 'manifest.json').read_bytes()) == 'f33d0032d3bfd33cec02f9790a90104892e8a4bbd8803b8349105544571c7b93')
    failures = [x for x in checks if not x['passed']]
    raw = ''.join(('PASS ' if x['passed'] else 'FAIL ') + x['name'] + '\n' for x in checks)
    (OUT / 'command.raw.log').write_text(raw)
    result = {'schema': 'geometry-formal-full-v3-golden-envelope-supplement/1', 'actor': '/root/publication_final_review/assembly_packet_review', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': [sys.executable, '-B', str(Path(__file__).resolve())], 'actualPython': str(Path(sys.executable).resolve()), 'actualPythonSHA256': sha(Path(sys.executable).resolve().read_bytes()), 'reviewSourceSHA256': sha(Path(__file__).read_bytes()), 'readonlyGitObjectCommand': command, 'actualExitCode': 1 if failures else 0, 'passedMetadataChecks': len(checks) - len(failures), 'failedMetadataChecks': len(failures), 'countsAreProductTests': False, 'productOrBrowserOrServiceOrCLIOrAPIExecuted': False, 'repositoryOrGitHubWritten': False, 'packetOrOriginalsChanged': False, 'sourceActorSupplementAccepted': not failures, 'parentWholePacketAcceptanceSeparate': True, 'originalFailedReviewRetained': {'path': str(PREV / 'report.json'), 'sha256': sha((PREV / 'report.json').read_bytes()), 'actualExitCode': 1, 'passedMetadataChecks': 330, 'failedMetadataChecks': 1}, 'correctedReviewerAssumption': 'Golden source is the original schema envelope {schema,mode,total,sections}; prior predicate erroneously compared canonical sections directly to the envelope. Exact original golden.sections matches84 actualcanonical sections totaling2207. Original source, golden, assertions, receipts and failed review remain unchanged.', 'rawLog': {'path': str(OUT / 'command.raw.log'), 'bytes': (OUT / 'command.raw.log').stat().st_size, 'sha256': sha((OUT / 'command.raw.log').read_bytes())}, 'findings': failures, 'checks': checks}
    (OUT / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:result[k] for k in ['actualExitCode', 'passedMetadataChecks', 'failedMetadataChecks', 'reviewSourceSHA256', 'rawLog', 'findings']}))
    return result['actualExitCode']


if __name__ == '__main__':
    raise SystemExit(main())
