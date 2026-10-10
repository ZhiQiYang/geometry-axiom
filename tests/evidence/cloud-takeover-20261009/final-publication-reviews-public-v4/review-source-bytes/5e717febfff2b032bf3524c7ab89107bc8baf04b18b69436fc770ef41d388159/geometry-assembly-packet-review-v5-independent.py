"""Readonly final ASM v5 review against immutable independently audited v4.

Verifies the real packaging identity finding is fixed by a fresh packet, all
product bytes retained, and earlier failed and supplementary reviews unchanged.
No product/browser/service, packaging engine or prior reviewer is executed.
"""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import sys

S = Path('<workspace-path>')
D = S / 'geometry-delivery-closeout-20261009'
P4 = D / 'f3b-original-assembly-public-v4'
P = D / 'f3b-original-assembly-public-v5'
H = S / 'geometry-assembly-packet-review-v4-independent.py'
assert hashlib.sha256(H.read_bytes()).hexdigest() == '0c7d16eac138b21ec9a2d70235e5e8ba8b57336a5c449cea2e66aa6583f35e60'
spec = importlib.util.spec_from_file_location('readonly_parser_helpers', H)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
OUT = S / 'geometry-assembly-v5-independent-publication-review'
MANIFEST = 'a8254cb4fab9151008f2c65ed37e01646e1542c828a8c59f2f9bc1532d8688a6'


def main():
    assert not OUT.exists()
    OUT.mkdir()
    checks = []
    def check(n, v, d=None):
        checks.append({'name': n, 'passed': bool(v), 'details': d})
    m, old = h.load(P / 'manifest.json'), h.load(P4 / 'manifest.json')
    check('exact freshv5 and original withdrawnv4 immutable manifests', h.sha((P / 'manifest.json').read_bytes()) == MANIFEST and h.sha((P4 / 'manifest.json').read_bytes()) == 'bebeec6f3074b2c8cad4ab71c90d7decd3287db7b1b5dfa25444d83b6add9d64')
    paths = [x['path'] for x in m['publicFiles']]
    census = {x.relative_to(P).as_posix() for x in P.rglob('*') if x.is_file()}
    check('exact200 listed + manifest201 files', len(paths) == len(set(paths)) == 200 and census == set(paths) | {'manifest.json'})
    for row in m['publicFiles']:
        f = P / row['path']
        data = f.read_bytes()
        check('safe public relative path ' + row['path'], not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts and not f.is_symlink())
        check('exact bytes and SHA256 ' + row['path'], len(data) == row['bytes'] and h.sha(data) == row['sha256'])
        if f.suffix == '.json':
            try:
                h.loads(data)
                check('distinct structured JSON keys ' + row['path'], True)
            except Exception as exc:
                check('distinct structured JSON keys ' + row['path'], False, repr(exc))
    old_paths = {x['path'] for x in old['publicFiles']}
    check('only one new role correction file', set(paths) - old_paths == {'publication-role-correction.json'} and old_paths <= set(paths))
    for relative in sorted(old_paths - {'README.md'}):
        check('all original v4 evidence/source/artifact bytes unchanged ' + relative, (P4 / relative).read_bytes() == (P / relative).read_bytes())
    check('all prior result/source/lifecycle metadata retained exact', all(m[k] == v for k, v in old.items() if k not in {'publicationImplementation', 'publicFiles'}))
    old_readme, new_readme = (P4 / 'README.md').read_text(), (P / 'README.md').read_text()
    check('README original prose intact and explicit rolefix addendum', new_readme.startswith(old_readme) and 'Fresh v5 corrects publication-role metadata only' in new_readme[len(old_readme):] and 'specific ASM configuration generator is d73f3 (v2)' in new_readme[len(old_readme):] and 'generic v7 module103735' in new_readme[len(old_readme):] and 'projection engine is0209 (v8)' in new_readme[len(old_readme):])
    fix = h.load(P / 'publication-role-correction.json')
    imp = m['publicationImplementation']
    check('role correction file and manifest match old exact and new exact fields', fix == m['publicationRoleCorrection'] and fix['oldField'] == old['publicationImplementation'] and fix['correctedField'] == imp and fix['supersededV4ManifestSHA256'] == h.sha((P4 / 'manifest.json').read_bytes()))
    specific = D / 'prepare_f3b_original_assembly_packet_v2.py'
    generic = D / 'prepare_ui_history_packet_v7.py'
    engine = D / 'prepare_ui_history_packet_v8.py'
    reviser = D / 'repair_assembly_and_source43_fresh_packets.py'
    config = D / 'f3b-original-assembly-config-v2.json'
    extras = D / 'f3b-original-assembly-extra-v2.json'
    check('corrected specific inherited configuration generator is d73f3v2', imp['inheritedConfigurationGeneratorOriginalSHA256'] == h.sha(specific.read_bytes()) == 'd73f3ef64b1e0a8163f3748e490015677ea5c5e3bb6431fc161fb6139923a68a' and imp['inheritedConfigurationGeneratorVersion'] == specific.name)
    check('corrected generic module distinct103735v7 actualidentity', imp['inheritedGenericProjectionModuleOriginalSHA256'] == h.sha(generic.read_bytes()) == '103735521e97a3c4d4287b8cb9b738eb7c1deb91c3d4248c330955288abc35a8' and 'did not generate the specific ASM config itself' in imp['inheritedGenericProjectionModuleRole'])
    check('final bounded projection engine actual0209v8 originalidentity', imp['finalProjectionEngineOriginalSHA256'] == h.sha(engine.read_bytes()) == '0209c3f9467a9b63d6c4ae3ca74e4d14cf48a3f51dd31e1ec1fa594f15a0f065')
    check('actual fresh packet reviser sourceidentity explicit4969', imp['actualFreshPacketReviserSHA256'] == h.sha(reviser.read_bytes()) == '4969f91f34d924c5780bbe616c8db74e75215d9ccc4b9ce6846af6fd938bc669')
    check('inherited originalv2 configuration andextras SHA bindings correct', imp['inheritedConfigurationSHA256'] == h.sha(config.read_bytes()) and imp['inheritedExtrasSHA256'] == h.sha(extras.read_bytes()))
    original_build = h.load(D / 'f3b-original-assembly-package-build-v2.json')
    check('originalv2 actualbuild confirms specific vs generic exactroles', original_build['actualExitCode'] == 0 and original_build['builderSHA256'] == imp['inheritedConfigurationGeneratorOriginalSHA256'] and original_build['preparerSHA256'] == imp['inheritedGenericProjectionModuleOriginalSHA256'] and original_build['config'] == str(config) and original_build['extras'] == str(extras))
    first_dir = S / 'geometry-assembly-v4-independent-publication-review'
    supplement_dir = S / 'geometry-assembly-v4-independent-publication-supplement'
    first, supplement = h.load(first_dir / 'report.json'), h.load(supplement_dir / 'report.json')
    check('original failed1152/3 actualexit1 report remains immutable', h.sha((first_dir / 'report.json').read_bytes()) == '8cc1e456e1244067da47dd6ee64c92fc04e8cc1992d9f175bc8d0bcb8e020a6a' and first['actualExitCode'] == 1 and first['passedMetadataChecks'] == 1152 and first['failedMetadataChecks'] == 3 and h.sha((first_dir / 'command.raw.log').read_bytes()) == first['rawLog']['sha256'] and h.sha(H.read_bytes()) == first['reviewSourceSHA256'])
    check('original132/0 supplement actualexit0 report immutable', h.sha((supplement_dir / 'report.json').read_bytes()) == '73abb1b1ebdb88e33a300146f1e9926d3f7ebeebc9a7fa654efc6f35e907a9b6' and supplement['actualExitCode'] == 0 and supplement['passedMetadataChecks'] == 132 and supplement['failedMetadataChecks'] == 0 and h.sha((supplement_dir / 'command.raw.log').read_bytes()) == supplement['rawLog']['sha256'] and h.sha((S / 'geometry-assembly-packet-review-v4-supplement.py').read_bytes()) == supplement['reviewSourceSHA256'])
    check('only actual v4 metadata role finding required fresh packet correction', fix['originalExecutedSourceOrResultChanged'] is False and fix['productExecuted'] is False and fix['oldV1ThroughV4Preserved'] is True and 'V4 named inherited generic v7 module as configurationPreparer' in fix['reason'])
    check('150 partial original result not expanded golden/full not claimed', m['productGate']['passedAssertions'] == 150 and m['productGate']['failedAssertions'] == 0 and m['productGate']['skippedAssertions'] == 0 and m['productGate']['sections'] == {'P77': 134, 'P82': 16} and m['productGate']['actualNodeExitCode'] == m['productGate']['gateExitCode'] == 0 and m['productGate']['completed'] is True and m['productGate']['executionVerified'] is True and m['productGate']['fullAcceptance'] is False and m['productGate']['goldenCompare'] == 'not compared (partial mode)')
    check('controller1 original missing terminal serviceunknown vs recovery0/Z retained', m['originalLifecycle']['parentReportedActualControllerExitCode'] == 1 and m['originalLifecycle']['actualControllerExitCodeFromOriginalFiles'] is None and m['originalLifecycle']['originalTerminalMissing'] is True and m['originalLifecycle']['originalServiceActualExitCode'] is None and m['separateStopRecovery']['actualExitCode'] == 0 and m['separateStopRecovery']['replacesOriginalLifecycleTerminal'] is False and all(x['state'] == 'Z' for x in m['separateStopRecovery']['processObservations'] if x['pid'] != 252395))
    check('retained source closure125 copies distinction plus7helper7dependency refs', m['sourceClosure']['capturedWebFiles'] == 125 and m['sourceClosure']['committedHelperReferenceFiles'] == m['sourceClosure']['committedDependencyReferenceFiles'] == 7 and m['sourceClosure']['committedHelpersAreSeparateSourceReferences'] is True and m['sourceClosure']['sourceCopiesWereExecutedForPublication'] is False)
    check('freshv5 manifest unchanged afteraudit', h.sha((P / 'manifest.json').read_bytes()) == MANIFEST)
    failures = [x for x in checks if not x['passed']]
    raw = ''.join(('PASS ' if x['passed'] else 'FAIL ') + x['name'] + '\n' for x in checks)
    (OUT / 'command.raw.log').write_text(raw)
    result = {'schema': 'geometry-assembly-v5-independent-publication-review/1', 'actor': '/root/publication_final_review/assembly_packet_review', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': [sys.executable, '-B', str(Path(__file__).resolve())], 'actualPython': str(Path(sys.executable).resolve()), 'actualPythonSHA256': h.sha(Path(sys.executable).resolve().read_bytes()), 'reviewSourceSHA256': h.sha(Path(__file__).read_bytes()), 'parserHelperSourceSHA256': h.sha(H.read_bytes()), 'actualExitCode': 1 if failures else 0, 'passedMetadataChecks': len(checks) - len(failures), 'failedMetadataChecks': len(failures), 'countsAreProductTests': False, 'productOrBrowserOrServiceExecuted': False, 'repoOrGitHubWritten': False, 'packetOrOriginalsChanged': False, 'manifestSHA256': MANIFEST, 'finalPacketAcceptance': not failures, 'priorActualFailPreserved': True, 'priorValidatorAssumptionsCorrectedSeparately': True, 'priorRealMetadataFindingFixedByFreshV5': not failures, 'freshReviserActualToolExit': {'value': 0, 'source': 'delivery author reports actual unified exec chunk d89e49; fresh packet itself does not provide a separate process terminal receipt'}, 'priorReviews': [{'path': str(first_dir / 'report.json'), 'sha256': h.sha((first_dir / 'report.json').read_bytes()), 'actualExitCode': 1}, {'path': str(supplement_dir / 'report.json'), 'sha256': h.sha((supplement_dir / 'report.json').read_bytes()), 'actualExitCode': 0}], 'rawLog': {'path': str(OUT / 'command.raw.log'), 'sha256': h.sha((OUT / 'command.raw.log').read_bytes()), 'bytes': (OUT / 'command.raw.log').stat().st_size}, 'findings': failures, 'checks': checks}
    (OUT / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:result[k] for k in ['actualExitCode', 'passedMetadataChecks', 'failedMetadataChecks', 'reviewSourceSHA256', 'rawLog', 'findings', 'finalPacketAcceptance']}))
    return result['actualExitCode']


if __name__ == '__main__':
    raise SystemExit(main())
