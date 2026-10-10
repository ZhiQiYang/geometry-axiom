"""Readonly correction of an audit assumption about fresh publication time."""
from pathlib import Path
import datetime
import hashlib
import json
import sys

S = Path('<workspace-path>')
D = S / 'geometry-delivery-closeout-20261009'
P4, P5 = D / 'f3b-original-assembly-public-v4', D / 'f3b-original-assembly-public-v5'
OUT = S / 'geometry-assembly-v5-independent-time-supplement'
PREVIOUS = S / 'geometry-assembly-v5-independent-publication-review'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def main():
    assert not OUT.exists()
    OUT.mkdir()
    a, b = load(P4 / 'manifest.json'), load(P5 / 'manifest.json')
    previous = load(PREVIOUS / 'report.json')
    checks = []
    def check(n, v):
        checks.append({'name': n, 'passed': bool(v)})
    check('prioractual629/1 exit1 preserved', previous['actualExitCode'] == 1 and previous['passedMetadataChecks'] == 629 and previous['failedMetadataChecks'] == 1 and sha((PREVIOUS / 'report.json').read_bytes()) == '95e80baf19eff575ba0ec14545b1b5aa6af8d982cb2763c32e14e8dd18b28dab')
    check('prioractualsource/raw hashes preserved', sha((S / 'geometry-assembly-packet-review-v5-independent.py').read_bytes()) == previous['reviewSourceSHA256'] and sha((PREVIOUS / 'command.raw.log').read_bytes()) == previous['rawLog']['sha256'])
    changed = {k for k, value in a.items() if k not in {'publicationImplementation', 'publicFiles'} and value != b[k]}
    check('sole difference outside role metadata/census is fresh preparedUtc', changed == {'preparedUtc'})
    check('new preparedUtc is later valid UTC preparation time', datetime.datetime.fromisoformat(b['preparedUtc']) > datetime.datetime.fromisoformat(a['preparedUtc']) and datetime.datetime.fromisoformat(b['preparedUtc']).utcoffset() == datetime.timedelta(0))
    for key in ['rounds', 'historyReviewsAndExecutorSources', 'fullTestedCommitSourceCopies', 'testedProductHead', 'productGate', 'originalLifecycle', 'separateStopRecovery', 'independentMetadataReview', 'sourceClosure', 'sourceAndArtifactByteBindings', 'limits', 'omissions', 'independentOtherScopes']:
        check('exact historical execution/byte associations unchanged ' + key, a[key] == b[key])
    check('fresh metadata time never changes original testedfullSHA', b['testedProductHead'] == 'f3b8285729b42cd22451c98cba1e2ec4514517f3' and b['rounds'][0]['testedHead'] == b['testedProductHead'] and b['rounds'][0]['dirty'] is False)
    check('actual metadata-role correction remains specificgenerator vs genericdep', b['publicationImplementation']['inheritedConfigurationGeneratorOriginalSHA256'] == sha((D / 'prepare_f3b_original_assembly_packet_v2.py').read_bytes()) and b['publicationImplementation']['inheritedGenericProjectionModuleOriginalSHA256'] == sha((D / 'prepare_ui_history_packet_v7.py').read_bytes()))
    check('v5 immutable final-ready manifest identity', sha((P5 / 'manifest.json').read_bytes()) == 'a8254cb4fab9151008f2c65ed37e01646e1542c828a8c59f2f9bc1532d8688a6')
    check('v4 withdrawn mother immutable exact identity', sha((P4 / 'manifest.json').read_bytes()) == 'bebeec6f3074b2c8cad4ab71c90d7decd3287db7b1b5dfa25444d83b6add9d64')
    failure = [x for x in checks if not x['passed']]
    raw = ''.join(('PASS ' if x['passed'] else 'FAIL ') + x['name'] + '\n' for x in checks)
    (OUT / 'command.raw.log').write_text(raw)
    report = {'schema': 'geometry-assembly-v5-independent-time-supplement/1', 'actor': '/root/publication_final_review/assembly_packet_review', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': [sys.executable, '-B', str(Path(__file__).resolve())], 'actualPython': str(Path(sys.executable).resolve()), 'actualPythonSHA256': sha(Path(sys.executable).resolve().read_bytes()), 'reviewSourceSHA256': sha(Path(__file__).read_bytes()), 'actualExitCode': 1 if failure else 0, 'passedMetadataChecks': len(checks) - len(failure), 'failedMetadataChecks': len(failure), 'countsAreProductTests': False, 'productOrBrowserOrServiceExecuted': False, 'repositoryOrGitHubWritten': False, 'packetOrOriginalsChanged': False, 'manifestSHA256': sha((P5 / 'manifest.json').read_bytes()), 'finalPacketAcceptance': not failure, 'priorResult': {'report': str(PREVIOUS / 'report.json'), 'sha256': sha((PREVIOUS / 'report.json').read_bytes()), 'actualExitCode': 1, 'passedMetadataChecks': 629, 'failedMetadataChecks': 1}, 'correctedValidatorAssumption': 'Prior equality predicate included preparedUtc as historical execution metadata. Fresh publication preparedUtc legitimately changed from18:59:36 to19:39:00. Every original execution/byte-association field and198 retained non-README files are unchanged; real v4 generic/config-generator role finding is fixed in freshv5.', 'priorV4FailedAndSupplementalReviewsPreserved': True, 'rawLog': {'path': str(OUT / 'command.raw.log'), 'sha256': sha((OUT / 'command.raw.log').read_bytes()), 'bytes': (OUT / 'command.raw.log').stat().st_size}, 'findings': failure, 'checks': checks}
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:report[k] for k in ['actualExitCode', 'passedMetadataChecks', 'failedMetadataChecks', 'reviewSourceSHA256', 'rawLog', 'findings', 'finalPacketAcceptance']}))
    return report['actualExitCode']


if __name__ == '__main__':
    raise SystemExit(main())
