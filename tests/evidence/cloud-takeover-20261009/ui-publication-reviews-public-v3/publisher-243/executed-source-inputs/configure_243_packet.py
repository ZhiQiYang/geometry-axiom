"""Create scratch-only scope configuration from sealed actual receipts."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
HEAD = '243326b512896ace70e068f62c8f3d6397f6000d'
BASE = Path('<workspace-path>')
EVIDENCE = Path('<original-evidence-root>')
VERIFY = Path('<workspace-path>')
REPO = Path('<workspace-path>')

def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

index = json.loads((BASE / 'completed-scopes-actor-index.json').read_text())
assert digest(BASE / 'completed-scopes-actor-index.json') == '12a36c27b2d614c51846fdccd6783922cae87614f6eda0d3043c6f919edcf263'
items = []
source_map = {}
for row in index['rows']:
    assert row['fullSHA'] == HEAD and row['dirtyBefore'] == '' and row['dirtyAfter'] == ''
    assert row['exitCode'] == 0 and row['completed'] is True and row['fail'] == 0
    receipt = Path(row['receipt']['path'])
    result = Path(row['probeResults']['path'])
    items.append({'name': row['scope'] + '-243-scoped', 'head': HEAD, 'receipt': str(receipt),
                  'scope': 'Separate original ' + row['scope'] + ' controls; actual live probe Python to Node to Chromium ELF plus owned native before/after. All nine source/runtime checks true. Not fullCDP/Space, not summed with other scopes.',
                  'result': {'pass': row['pass'], 'fail': 0, 'completed': True, 'actualExitCode': 0},
                  'logs': [row['rawObserverLog']['path'], row['rawProbeLog']['path']],
                  'artifacts': [str(receipt.parent), str(result.parent)]})
    for path, expected in row['executionSources'].items():
        if path.startswith('<workspace-root-prefix>/'):
            if path in source_map:
                assert source_map[path] == expected
            source_map[path] = expected

for name, count, completed, logprefix in [('space', [228, 0], True, 'SPACE_RESULT '), ('cdp', [1713, 6], False, 'CDP_RESULT ')]:
    folder = EVIDENCE / ('after-final-243326b5-full-' + name + '-20261009')
    item = {'name': 'full-' + name + '-243-' + ('complete-declared-five' if completed else 'terminal-failed'),
            'head': HEAD, 'receipt': str(folder / 'receipt.json'),
            'scope': ('Existing full Space five declared groups plus setup/health, timber-material and timber-source-guards explicitly omitted; no golden/CDP claim.' if name == 'space' else 'Purposeful existing unfiltered full CDP, terminal1713/6 atP75; P32 wrong host1, P64 R/Esc premise4, P75 empty selection fatal1 still diagnosing. Incomplete, golden not compared.'),
            'result': {'pass': count[0], 'fail': count[1], 'completed': completed, 'actualExitCode': 0 if completed else 1},
            'canonicalLogPrefix': logprefix, 'logs': [str(folder / 'command.log')], 'artifacts': [str(folder)]}
    if name == 'cdp':
        item.update(canonicalPassKey='passedAssertions', canonicalFailKey='failedAssertions')
        item['result'].update(skip=0, goldenCompared=False)
    else:
        item['result'].update(included=['space-height-library', 'projection-lifecycle', 'projection-placement', 'font-layout', 'space-flow'], omitted=['timber-material', 'timber-source-guards'])
    items.append(item)

for name, folder, artifact, passed, failed, completed, override, source in [
    ('ui123-four-v4-failed', 'supplement-243326b5-gate', '<isolated-test-directory>', 185, 2, False, True, 'a62999473b6ff6076e414a48d5950135998f49f653fbcfbc70c20b25aa61bd24'),
    ('ui123-four-v5-complete', 'supplement-243326b5-v5-gate', '<isolated-test-directory>', 327, 0, True, True, None),
    ('room54-original-ten-negatives', 'room54-243326b5-gate', '<isolated-test-directory>', 273, 0, True, False, 'ac2a0cd540de60ec118afc9890d5d6f6037d7eda1eae8b51da3ade498ed82b31')]:
    gate = VERIFY / folder
    receipt = json.loads((gate / 'receipt.json').read_text())
    assert receipt['acceptanceResult']['passed'] == passed and receipt['acceptanceResult']['failed'] == failed
    provenance = receipt.get('testSourceProvenance', {})
    if source is None:
        # Exact sealed executor hash is resolved from the gate, not from a short name.
        source = provenance['executedProbeSHA256']
    result = {'pass': passed, 'fail': failed, 'completed': completed, 'actualExitCode': 0 if completed else 1,
              'sourceOverride': override, 'probeCompleted': True,
              'probeCompletedMeaning': 'Actual accepted completion' if completed else 'All four groups attempted only; acceptance false'}
    if source:
        result['executorSha256'] = source
    if name.startswith('room54'):
        result.update(costPerPdfAndPng={'candidate': [12, 14, 16], 'manual': [16, 20, 24]}, costProtocol='room-direct-row-dimensions/1')
    scope = ('Reviewed-v4 four groups: API0 premise rejected legitimate source-inspect and engineering-read; hidden main toggle incorrectly assumed clickable on390. Actual185/2 false retained, no product suppression of legitimate reads.' if failed else 'Strict reviewed-v5 four groups desktop/390, exact two readonly commands allowlisted and unknown rejected, normal visible compact panel route with positive hit. Original native/World/owner/raw/dirty assertions retained, not formal six/all43/fullCDP.' if override else 'All original ten normal single-room scenarios and six named negatives, actual six same-start/end cost cases. Formal committed oracle without sourceOverride, not multiroom/other protocol or machine-time-to-human-time conversion.')
    item = {'name': name + '-243', 'head': HEAD, 'receipt': str(gate / 'receipt.json'), 'scope': scope,
            'result': result, 'logs': [str(gate / 'command.log')], 'artifacts': [str(gate), artifact]}
    if override:
        item['expectedProbeCompleted'] = True
    items.append(item)

extras = [{'path': str(BASE / 'completed-scopes-actor-index.json'), 'destination': 'actor-index/scoped-six-original.json', 'purpose': 'Same executor scoped index, not independent review or full integration.'},
          {'path': '<workspace-path>', 'destination': 'actor-index/owned-scoped-service-stop.json'},
          {'path': '<workspace-path>', 'destination': 'oracle-provenance/visible-picker-observer-v2'},
          {'path': '<workspace-path>', 'destination': 'oracle-provenance/live-observer-independent-review'},
          {'path': '<workspace-path>', 'destination': 'oracle-provenance/navigation-independent-review'},
          {'path': str(HERE / 'pr179-ci-2433-readonly'), 'destination': 'ci-readonly-243'},
          {'path': '<workspace-path>', 'destination': 'ci-readonly-root-243'}]

for basename in ['243326b5-v4-findings.md', '243326b5-v5-findings.md', '243326b5-room54-findings.md',
                 'supplementary-validation-243-supplement-v4.json', 'supplement-v5-strict-delta-mock-review.json',
                 'canonical-oracle-corrections-243-static-vm-review.json', 'review_canonical_oracles_243.cjs',
                 'supplementary-validation-243-supplement-v5-census-corrected.json', 'supplementary-validation-243-supplement-v5.json', 'supplementary-validation-243-room54.json']:
    path = VERIFY / basename
    assert path.is_file(), path
    extras.append({'path': str(path), 'destination': 'scope-review/' + basename,
                   'purpose': 'Original findings or source/mock/consistency evidence. Static proof counts are not browser acceptance assertions; historical mutable CDP midrun observation hash is not terminal raw receipt.'})

# Freeze actual measured source bytes. Changed working files are recovered solely
# by git-show of the exact original tested SHA and checked against original receipt.
snapshot = HERE / 'actual-scoped-source-retention-243'
source_ledger = []
for path, expected in sorted(source_map.items()):
    original = Path(path)
    if original.is_file() and digest(original) == expected:
        retained = original
        origin = 'Original sealed source still byte-identical to execution receipt'
    else:
        assert original.is_relative_to(REPO), ('Changed external executor bytes unavailable', original)
        relative = original.relative_to(REPO).as_posix()
        value = subprocess.run(['git', 'show', HEAD + ':' + relative], cwd=REPO, capture_output=True, check=True).stdout
        assert hashlib.sha256(value).hexdigest() == expected
        retained = snapshot / expected / original.name
        retained.parent.mkdir(parents=True, exist_ok=True)
        retained.write_bytes(value)
        origin = 'Exact tested commit git blob independently matched to sealed execution receipt; current dirty file not substituted'
    destination = 'executors/actual-source-bytes/' + expected + '/' + original.name
    extras.append({'path': str(retained), 'destination': destination, 'purpose': origin})
    source_ledger.append({'originalPath': path, 'originalPathSha256': hashlib.sha256(path.encode()).hexdigest(),
                          'executedSha256': expected, 'retainedSourcePath': str(retained), 'publicPath': destination, 'retentionOrigin': origin})
write('ui-243-source-ledger.json', {'schema': 'geometry-exact-scoped-source-retention/1', 'testedHead': HEAD, 'entries': source_ledger, 'publicationWasExecuted': False})
extras.append({'path': str(HERE / 'ui-243-source-ledger.json'), 'destination': 'executors/actual-source-ledger.public.json'})
write('ui-243-config.json', items)
write('ui-243-extra-evidence.json', extras)
write('ui-243-metadata.json', {'schema': 'geometry-ui-single-room-243-scoped-public/1',
       'scope': 'Eleven independent sealed actual scopes at clean243: six race controls, full declared-five Space, failed full CDP, failed four-v4, accepted four-v5, accepted formal full54. No sum or final integration claim.',
       'earlierBundles': [{'name': 'ui-single-room-prior-public-v4', 'manifestSha256': '3f2abb29f759de73c6e4c72323ead0c42aab763ca4e6391f63d41f9802ae8e9d'},
                          {'name': 'ui-single-room-640-public-v4', 'manifestSha256': '64a0d10728631d4e9ccdac5c4051f666a95e9104a6159e43eac72950884f0522'},
                          {'name': 'ui-single-room-0b37-failed-public-v5', 'manifestSha256': '389b1fdf3e0d8639bf192f2087f0d49de5a565799229598dc958132bdbcdaa97'}],
       'limits': ['Eleven scopes stand alone; no count sum into full integration.', 'CDP1713/6 terminal exit1 incomplete; golden not compared; P75 diagnosis pending at this packet cutoff.',
                  'Space228/0 covers five declared groups; timber-material/timber-source-guards omitted.', 'UIv4 185/2 original false remains; canonical completed means all four attempted only.',
                  'UIv5 327/0 is reviewed sourceOverride, not formal six or all43.', 'Formal full54 273/0 exact original ten plus six negatives and six same-end cost cases remains bound243 even after caption patch.',
                  'Caption source and canonical-host/Esc corrections await later clean product candidate; no243 formal-six result borrowed from640.',
                  'Source/AST/VM/mock proofs and receipt/source checks are artifact verification, not additional product test passes.',
                  'Source copies/public trace or receipt path projections are not executed bytes; original hash retained separately.',
                  'Historical Windows full1692/2 exit1 incomplete, cloud originals unreceived; historical CDP2207/0/0 remains5174 only.',
                  'Old640 actual Chrome ELF and earlier formal38 Node gaps remain unknown; no retroactive source/exe identity binding.',
                  'CurrentCI runner0/steps[] unexecuted; no retry/account changes; private queue unknown with oldv5 retained, no empty DB.']})
print(json.dumps({'items': len(items), 'extraEvidenceRefs': len(extras), 'actualSourceRefs': len(source_ledger)}))
