"""Read-only public inventory of completed UI/room/projection regression history.

Writes only a fresh scratch bundle. Result scopes and tested SHAs stay separate.
This preparer does not execute tests or mutate repository/remote/service state.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('projection', HERE / 'prepare_resume_packet.py')
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
p = shared.p
REPO = Path('<workspace-path>')
VERIFY = Path('<workspace-path>')
PROJ = Path('<workspace-path>')
SAME = Path('<workspace-path>')
HOLE = Path('<workspace-path>')
UNITS = Path('<unit-evidence-root>/scenario-units-c0f05baa')
F980 = 'f98078dc150c22960cbe2d212afb3ded61954bb9'
C0 = 'c0f05baade2424482fab94c72f0592f7b02326ae'
EARLY = '2703e4738ae308b2a268096f666f326f1e9a9b2f'
COMMON_SOURCES = ['geometry-web/app.js', 'geometry-web/app.css', 'geometry-web/index.html',
                  'geometry-web/workspace-shell.js', 'geometry-web/workspace-shell.css',
                  'geometry-web/space-workspace.js', 'geometry-web/space-workspace.css',
                  'geometry-web/grid-system-workspace.js', 'geometry-web/grid-system-workspace.css',
                  'geometry-web/grid-inspector.css', 'geometry-web/room-outline-workspace.js',
                  'geometry-web/reference-workspace.js', 'geometry-web/model-viewer.js',
                  'geometry-web/scenario-workspace.js', 'geometry-web/serve.py', 'tests/binaries.py']


def collision_safe_projection(value):
    """Replace path labels without merging distinct absolute-path map keys."""
    if isinstance(value, dict):
        key_labels = [p.redact_text(key) for key in value]
        repeats = {key for key in key_labels if key_labels.count(key) > 1}
        projected = {}
        for key, item in value.items():
            label = p.redact_text(key)
            if label in repeats:
                key_hash = hashlib.sha256(key.encode()).hexdigest()
                label += '|basename=' + Path(key).name + '|originalKeySha256=' + key_hash
            assert label not in projected
            projected[label] = collision_safe_projection(item)
        assert len(projected) == len(value)
        return projected
    if isinstance(value, list):
        return [collision_safe_projection(item) for item in value]
    if isinstance(value, str):
        return p.redact_text(value)
    return value


def projection_key_audit(value, at='$'):
    """Record affected dictionaries so public readers can reconstruct mappings."""
    result = []
    if isinstance(value, dict):
        labels = [p.redact_text(key) for key in value]
        if len(set(labels)) != len(labels):
            result.append({'dictionaryLocation': at, 'originalEntries': len(value),
                           'publicEntries': len(collision_safe_projection(value)),
                           'rule': 'Colliding public path keys retain basename plus full SHA256 of original key; values retained one-to-one',
                           'mapping': [{'originalKeySha256': hashlib.sha256(key.encode()).hexdigest(),
                                        'originalBasename': Path(key).name,
                                        'publicKey': public_key}
                                       for key, public_key in zip(value, collision_safe_projection(value))]})
        for key, item in value.items():
            result += projection_key_audit(item, at + '.' + p.redact_text(key))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            result += projection_key_audit(item, at + '[' + str(i) + ']')
    return result


def structured_public_text(text, name):
    """Preserve valid JSON/JSONL syntax while replacing decoded path strings."""
    suffix = Path(name).suffix.lower()
    if suffix in {'.json', '.stacks'}:
        original = json.loads(text)
        return json.dumps(collision_safe_projection(original), ensure_ascii=False, indent=2) + '\n'
    if suffix in {'.jsonl', '.trace', '.network'}:
        values = [json.loads(line) for line in text.splitlines() if line.strip()]
        return ''.join(json.dumps(collision_safe_projection(value), ensure_ascii=False, separators=(',', ':')) + '\n' for value in values)
    return p.redact_text(text)


def copy_file(source, destination, output, purpose):
    source = Path(source)
    suffix = source.suffix.lower()
    if suffix in {'.zip', '.gcanvas'}:
        assert source.stat().st_size <= 10 * 1024 * 1024, ('Publication archive exceeds agreed per-file bound', source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if suffix == '.gcanvas':
            with zipfile.ZipFile(source) as z:
                assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
                assert not p.private(z.read('manifest.json').decode())
                assert not p.private(z.read('world.scene').decode())
            shutil.copyfile(source, destination)
            changes = []
        else:
            changes = []
            with zipfile.ZipFile(source) as original:
                entries = original.infolist()
                assert all(not n.filename.startswith('/') and '..' not in Path(n.filename).parts for n in entries)
                projected = []
                for entry in entries:
                    data = original.read(entry)
                    # Playwright trace source/JSONL/network entries may include
                    # machine paths. Binary screenshot/resource bytes remain intact.
                    try:
                        text = data.decode('utf-8')
                    except UnicodeDecodeError:
                        projected.append((entry, data))
                        continue
                    # No work-manager/private feedback payload is part of these
                    # explicitly synthetic owned test traces.
                    assert not any(term in text for term in ('closure-evidence/queue/', 'owner_thread_id', 'PRIVATE_QUEUE_DATABASE'))
                    if p.private(text):
                        new = structured_public_text(text, entry.filename).encode()
                        changes.append({'entry': entry.filename, 'originalBytes': len(data),
                                        'originalSha256': hashlib.sha256(data).hexdigest(),
                                        'publicBytes': len(new), 'publicSha256': hashlib.sha256(new).hexdigest()})
                        projected.append((entry, new))
                    else:
                        projected.append((entry, data))
                if changes:
                    with zipfile.ZipFile(destination, 'w') as public:
                        for entry, data in projected:
                            public.writestr(entry, data)
                else:
                    shutil.copyfile(source, destination)
        return {'path': destination.relative_to(output).as_posix(), 'bytes': destination.stat().st_size,
                'sha256': p.sha(destination), 'originalPathLabel': p.redact_text(str(source)),
                'originalBytes': source.stat().st_size, 'originalSha256': p.sha(source),
                'byteIdenticalOriginal': not changes, 'publicProjection': bool(changes),
                'traceEntryProjections': changes, 'originalRetainedOutsideGit': True, 'purpose': purpose}
    if suffix in {'.png', '.pdf'}:
        # Only bounded generated fixture source assets, not standalone screenshots.
        assert source.stat().st_size <= 16384
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        return {'path': destination.relative_to(output).as_posix(), 'bytes': destination.stat().st_size,
                'sha256': p.sha(destination), 'originalSha256': p.sha(source), 'byteIdenticalOriginal': True,
                'purpose': 'Generated synthetic fixture source asset; no user source document.'}
    if suffix == '.json' and p.private(source.read_text()):
        original = json.loads(source.read_text())
        public = collision_safe_projection(original)
        p.write(destination, public)
        return {'path': destination.relative_to(output).as_posix(), 'bytes': destination.stat().st_size,
                'sha256': p.sha(destination), 'originalPathLabel': p.redact_text(str(source)),
                'originalBytes': source.stat().st_size, 'originalSha256': p.sha(source),
                'byteIdenticalOriginal': False, 'publicProjection': True,
                'projectionChanges': ['Machine/executable/isolated path labels; colliding dictionary path keys retain stable original-key SHA256 IDs without dropping entries.'],
                'projectionDictionaryKeyAudit': projection_key_audit(original),
                'originalRetainedOutsideGit': True, 'purpose': purpose}
    if suffix == '.jsonl' and p.private(source.read_text()):
        original_text = source.read_text()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(structured_public_text(original_text, source.name))
        return {'path': destination.relative_to(output).as_posix(), 'bytes': destination.stat().st_size,
                'sha256': p.sha(destination), 'originalPathLabel': p.redact_text(str(source)),
                'originalBytes': source.stat().st_size, 'originalSha256': p.sha(source),
                'byteIdenticalOriginal': False, 'publicProjection': True,
                'projectionChanges': ['StructuredJSONL path string projection preserves valid JSON rows and one-to-one dictionary keys.'],
                'originalRetainedOutsideGit': True, 'purpose': purpose}
    return p.copy_projection(source, destination, output, purpose)


def collect_tree(directory, target, output):
    refs = []
    if not directory.exists():
        return refs
    for source in sorted(directory.rglob('*')):
        if not source.is_file() or '__pycache__' in source.parts:
            continue
        if source.suffix.lower() not in {'.json', '.jsonl', '.log', '.scene', '.js', '.cjs', '.py', '.zip', '.gcanvas', '.pdf', '.png', '.patch', '.md', '.c', '.h', '.inc', '.css', '.html', '.txt', '.sh'}:
            continue
        if source.suffix.lower() == '.png' and source.stat().st_size > 16384:
            continue
        if any(part in {'feedback', 'queue', 'profile', 'profiles', 'node_modules'} for part in source.parts):
            continue
        destination = target / source.relative_to(directory)
        if {'executed-sources', 'executed-harness-sources'} & set(source.parts):
            # Preserve every source snapshot reference without publishing three
            # copies of the same committed bytes in adjacent gate archives.
            destination = output / 'executed-source-bytes' / p.sha(source) / source.name
        ref = copy_file(source, destination, output,
                        'Retained completed synthetic run artifact, original World/trace/source/raw result identity preserved.')
        ref['artifactRelativePath'] = source.relative_to(directory).as_posix()
        refs.append(ref)
    return refs


def head_dirty(receipt):
    if 'run' in receipt:
        return receipt['run']['head'], receipt['run']['dirty']
    before = receipt.get('before', {})
    if 'fullSHA' in before:
        return before['fullSHA'], before['dirty']
    if 'git' in before:
        return before['git']['head'], before['git']['status']
    return before.get('head'), before.get('dirty')


def receipt_ref(source, target, output):
    original = json.loads(source.read_text())
    j = collision_safe_projection(original)
    j['publicProjection'] = {'originalSha256': p.sha(source), 'originalBytes': source.stat().st_size,
                             'originalPathLabel': p.redact_text(str(source)), 'originalRetainedOutsideGit': True,
                             'changes': 'Machine/executable/isolated source, feedback and profile path labels; colliding absolute-path dictionary keys retain basename and original-key SHA256, preserving all entries. Result, full SHA, dirty, command, exit and original hashes remain.',
                             'dictionaryKeyAudit': projection_key_audit(original)}
    p.write(target, j)
    return original


def pack_round(output, item):
    label = item['name']
    dest = output / 'rounds' / label
    receipt = Path(item['receipt'])
    j = receipt_ref(receipt, dest / 'receipt.public.json', output)
    head, dirty = head_dirty(j)
    assert head == item['head'] and dirty in ('', False), (label, head, dirty)
    if j.get('run'):
        run = j['run']
        assert run.get('headAfter') == head and run.get('dirtyAfter') == '', (label, 'after-run')
        assert j.get('passed') == item['result'].get('pass') and j.get('failed') == item['result'].get('fail')
        assert j['completed'] == item['result']['completed'] and run['exitCode'] == item['result']['actualExitCode']
        assert p.sha(Path(run['rawLogPath'])) == run['rawLogSHA256']
    elif 'pass' in j and 'actualExitCode' in item['result']:
        assert j['pass'] == item['result']['pass'] and j['fail'] == item['result']['fail']
        assert j['completed'] == item['result']['completed'] and j['exitCode'] == item['result']['actualExitCode']
    if 'acceptanceResult' in j:
        accepted = j['acceptanceResult']
        assert accepted['passed'] == item['result']['pass'] and accepted['failed'] == item['result']['fail']
        assert accepted['completed'] == item['result']['completed']
        assert j['execution']['exitCode'] == item['result']['actualExitCode']
    if j.get('formalResult'):
        assert j['formalResult']['verified'] is True
        assert j['formalResult']['canonical'] == [{'passed': item['result']['pass'], 'failed': item['result']['fail'], 'completed': item['result']['completed']}]
        assert j['execution']['exitCode'] == item['result']['actualExitCode']
    canonical = j.get('evidence', {}).get('canonicalResult')
    if canonical:
        assert canonical.get('passedAssertions', canonical.get('passed')) == item['result']['pass'] and canonical.get('failedAssertions', canonical.get('failed')) == item['result']['fail']
        assert canonical['completed'] == item['result']['completed']
        assert j['execution']['exitCode'] == item['result']['actualExitCode']
    if item.get('canonicalLogPrefix'):
        lines = Path(j['log']['path']).read_text().splitlines()
        matches = [json.loads(line[len(item['canonicalLogPrefix']):]) for line in lines if line.startswith(item['canonicalLogPrefix'])]
        assert len(matches) == 1, (label, 'unique canonical record', len(matches))
        actual = matches[0]
        assert actual[item.get('canonicalPassKey', 'passed')] == item['result']['pass']
        assert actual[item.get('canonicalFailKey', 'failed')] == item['result']['fail']
        assert actual['completed'] == item['result']['completed']
        assert j['execution']['exitCode'] == item['result']['actualExitCode']
        p.write(dest / 'canonical-original-result.public.json', collision_safe_projection(actual))
    if item.get('expectedProbeCompleted') is not None:
        probe = json.loads(Path(j['acceptanceResult']['probePath']).read_text())
        assert probe['completed'] == item['expectedProbeCompleted']
    if j.get('probeCensus'):
        census = j['probeCensus']
        assert census['pass'] == item['result']['pass'] and census['fail'] == item['result']['fail']
        assert census['completed'] == item['result']['completed']
        assert j.get('exitCode', j.get('execution', {}).get('exitCode')) == item['result']['actualExitCode']
        assert p.sha(Path(census['resultsPath'])) == census['resultsSha256']
    if j.get('after'):
        after = j['after']; end_head = after.get('git', after).get('head', after.get('fullSHA'))
        end_dirty = after.get('git', after).get('status', after.get('dirty'))
        assert end_head == head and end_dirty in ('', False), (label, 'after', after)
    refs = []
    for path in item.get('logs', []):
        source = Path(path)
        refs.append(copy_file(source, dest / 'raw-streams' / source.name, output, 'Original command/log stream; actual and wrapper exit distinction preserved.'))
    if j.get('log'):
        assert p.sha(Path(j['log']['path'])) == j['log']['sha256']
    for key in ['rawLog', 'originalCommandRawLog', 'innerOriginalGate']:
        if j.get(key):
            assert p.sha(Path(j[key]['path'])) == j[key]['sha256']
    for log in j.get('logs', []):
        assert p.sha(Path(log['path'])) == log['sha256']
    for wrapper in item.get('wrappers', []):
        source = Path(wrapper)
        receipt_ref(source, dest / 'wrapper-receipts' / source.name, output)
        refs.append({'path': (dest / 'wrapper-receipts' / source.name).relative_to(output).as_posix(),
                     'originalSha256': p.sha(source), 'purpose': 'Original independent outer command identity/exit receipt; not substituted for product case result.'})
    for directory in item.get('artifacts', []):
        source = Path(directory)
        refs += collect_tree(source, dest / 'artifacts' / source.name, output)
    return {'name': label, 'testedHead': item['head'], 'dirty': False, 'declaredScope': item['scope'],
            'declaredResult': item['result'], 'originalReceiptSha256': p.sha(receipt),
            'receiptPath': (dest / 'receipt.public.json').relative_to(output).as_posix(),
            'rawEvidence': refs, 'releaseApproved': False}


def config():
    return [
        {'name': 'ui123-2703-original-six', 'head': EARLY, 'receipt': '<isolated-test-directory>',
         'scope': 'Original six adopted UI groups; probe completed means all groups attempted, acceptance incomplete; not all 43 checklist items/full CDP/Space', 'result': {'pass': 85, 'fail': 5, 'completed': True, 'probeCompletedMeaning': 'All six groups attempted', 'acceptanceCompleted': False, 'actualExitCode': 1},
         'logs': ['<isolated-test-directory>'], 'wrappers': [str(VERIFY / 'ui123-2703e473-gate/receipt.json')], 'artifacts': ['<isolated-test-directory>']},
        {'name': 'ui123-f980-six', 'head': F980, 'receipt': '<isolated-test-directory>',
         'scope': 'Six adopted UI groups at f980, preceding header hit assertion; not full acceptance', 'result': {'pass': 194, 'fail': 0, 'completed': True, 'actualExitCode': 0},
         'logs': ['<isolated-test-directory>'], 'wrappers': [str(VERIFY / 'ui123-f98078dc-gate/receipt.json')], 'artifacts': ['<isolated-test-directory>']},
        {'name': 'room54-f980-incomplete-ten', 'head': F980, 'receipt': str(VERIFY / 'room54-f98078dc-gate/receipt.json'),
         'scope': 'Original ten normal scenarios plus original negatives; six same-start/end room-direct-row measurements. Ten-scenario command incomplete.', 'result': {'pass': 208, 'fail': 1, 'completed': False, 'actualExitCode': 1},
         'logs': [str(VERIFY / 'room54-f98078dc-gate/command.log')], 'artifacts': ['<isolated-test-directory>']},
        {'name': 'ui123-c0-six', 'head': C0, 'receipt': '<isolated-test-directory>',
         'scope': 'Six adopted UI groups at c0; original header visibility oracle incorrectly required hidden right toggle visible/hittable at900 although persistent panel breakpoint680; no hidden click timeout; header widths600/390 not reached; acceptance incomplete', 'result': {'pass': 174, 'fail': 1, 'completed': True, 'probeCompletedMeaning': 'All six groups attempted', 'acceptanceCompleted': False, 'actualExitCode': 1},
         'logs': ['<isolated-test-directory>'], 'wrappers': [str(VERIFY / 'ui123-c0f05baa-gate/receipt.json')], 'artifacts': ['<isolated-test-directory>']},
        {'name': 'grid-c0-incomplete', 'head': C0, 'receipt': str(p.BASE / 'after-final-c0f05baa-grid-20261009/receipt.json'),
         'scope': 'Existing GRID_SYSTEM_ONLY partial mode, stopped during P70 draft visibility/selection regression; no full or golden claim', 'result': {'pass': 99, 'fail': 1, 'completed': False, 'actualExitCode': 1},
         'logs': [str(p.BASE / 'after-final-c0f05baa-grid-20261009/command.log')], 'artifacts': [str(p.BASE / 'after-final-c0f05baa-grid-20261009')]},
        {'name': 'projection-f980-original-ten', 'head': F980, 'receipt': str(PROJ / 'baseline-f980-r2/receipt.json'),
         'scope': 'Original 10 projection/owner/header controls; exact old expected hole order retained', 'result': {'pass': 3, 'fail': 7, 'completed': True, 'actualExitCode': 1},
         'logs': [str(PROJ / 'baseline-f980-r2.log')], 'wrappers': [str(PROJ / 'baseline-f980-r2-wrapper-receipt.json')], 'artifacts': [str(PROJ / 'baseline-f980-r2')]},
        {'name': 'projection-c0-original-ten', 'head': C0, 'receipt': str(PROJ / 'after-c0f05baa-r1/receipt.json'),
         'scope': 'Original unchanged 10 projection/owner/header controls; 2 old guessed hole-order failures preserved', 'result': {'pass': 8, 'fail': 2, 'completed': True, 'actualExitCode': 1},
         'logs': [str(PROJ / 'after-c0f05baa-r1.log')], 'wrappers': [str(PROJ / 'after-c0f05baa-r1-wrapper-receipt.json')], 'artifacts': [str(PROJ / 'after-c0f05baa-r1')]},
        {'name': 'same-owner-f980', 'head': F980, 'receipt': str(SAME / 'baseline-f980-r1/receipt.json'),
         'scope': 'Separate same-owner operation ordering control at desktop and390', 'result': {'pass': 0, 'fail': 2, 'completed': True, 'actualExitCode': 1},
         'logs': [str(SAME / 'baseline-f980-r1.log')], 'wrappers': [str(SAME / 'baseline-f980-r1-wrapper-receipt.json')], 'artifacts': [str(SAME / 'baseline-f980-r1')]},
        {'name': 'same-owner-c0', 'head': C0, 'receipt': str(SAME / 'after-c0f05baa-r1/receipt.json'),
         'scope': 'Separate same-owner operation ordering control at desktop and390', 'result': {'pass': 2, 'fail': 0, 'completed': True, 'actualExitCode': 0},
         'logs': [str(SAME / 'after-c0f05baa-r1.log')], 'wrappers': [str(SAME / 'after-c0f05baa-r1-wrapper-receipt.json')], 'artifacts': [str(SAME / 'after-c0f05baa-r1')]},
        {'name': 'normal-hole-f980', 'head': F980, 'receipt': str(HOLE / 'baseline-f980-r1/receipt.json'),
         'scope': 'Independent normal hole gesture at both widths; no held reply. Proof of exact historical ordered native output.', 'result': {'historicalControl': True},
         'logs': [str(HOLE / 'baseline-f980-r1.log')], 'wrappers': [str(HOLE / 'baseline-f980-r1-wrapper-receipt.json')], 'artifacts': [str(HOLE / 'baseline-f980-r1')]},
        {'name': 'normal-hole-c0', 'head': C0, 'receipt': str(HOLE / 'after-c0f05baa-r1/receipt.json'),
         'scope': 'Same fixed coordinates, unchanged ordered native World compared to f980 normal control; original 8/2 remains separate.', 'result': {'historicalControl': True},
         'logs': [str(HOLE / 'after-c0f05baa-r1.log')], 'wrappers': [str(HOLE / 'after-c0f05baa-r1-wrapper-receipt.json')], 'artifacts': [str(HOLE / 'after-c0f05baa-r1')]},
        {'name': 'resume-c0-four', 'head': C0, 'receipt': str(PROJ / 'after-c0f05baa-resume-r4/receipt.json'),
         'scope': 'Explicit same-parent/same-native-session Pause→Resume→Finish/Cancel desktop390 four lifecycles; not abrupt/cross-session/full CDP', 'result': {'pass': 4, 'fail': 0, 'assertions': 56, 'completed': True, 'actualExitCode': 0},
         'logs': [str(PROJ / 'after-c0f05baa-resume-r4/command.log')], 'wrappers': [str(PROJ / 'after-c0f05baa-resume-r4-wrapper-receipt.json')], 'artifacts': [str(PROJ / 'after-c0f05baa-resume-r4'), '<isolated-test-directory>']},
        {'name': 'scenario-c0-formal-four', 'head': C0, 'receipt': str(UNITS / 'receipt.json'),
         'scope': 'Four unit files incl Resume15; 132 total tests, one original named skip; actual native process supplemental review, no rerun.',
         'result': {'pass': 131, 'fail': 0, 'skip': 1, 'completed': True, 'actualNodeExitCode': 0, 'originalWrapperExitCode': 1,
                    'wrapperReason': 'Metadata matcher assumed registry path; original executor intentionally spawned byte-identical native copy. Original wrapper receipt retained; supplemental process-byte identity review accepted.'},
         'logs': [str(UNITS / 'stdout.log'), str(UNITS / 'stderr.log'), str(UNITS / 'python-backend-spawns.jsonl')], 'artifacts': [str(UNITS)]},
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--extra-config', type=Path)
    parser.add_argument('--only-extra', action='store_true')
    parser.add_argument('--extra-evidence', type=Path)
    parser.add_argument('--readme', type=Path)
    parser.add_argument('--metadata', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    assert not output.exists() and output.is_relative_to(HERE)
    output.mkdir(parents=True)
    items = [] if args.only_extra else config()
    if args.extra_config:
        items += json.loads(args.extra_config.read_text())
    rounds = [pack_round(output, item) for item in items]
    extras = []
    files = [] if args.only_extra else [PROJ / 'baseline-f980-first.log', PROJ / 'baseline-f980-first-wrapper-receipt.json',
             PROJ / 'harness-r1-projection_supplement.py', PROJ / 'baseline-f980-first/before-runtime.raw.json',
             PROJ / 'baseline-independent-actor-review.json', PROJ / 'after-c0f05baa-independent-actor-review.json',
             HOLE / 'normal-hole-historical-order-proof.json']
    for source in files:
        extras.append(copy_file(source, output / 'history-review' / source.name, output,
                                'Original preflight failure or separately scoped actor/proof review; no product run relabeling.'))
    for folder in ([] if args.only_extra else [PROJ / 'executed-r2-sources', SAME, HOLE]):
        for name in ['projection_supplement.py', 'projection_instrumentation.js', 'fixture.json']:
            source = folder / name
            extras.append(copy_file(source, output / 'executors' / folder.name / name, output,
                                    'Actually used historical executor/probe/fixture snapshot; publication projection not executed.'))
    if args.extra_evidence:
        for item in json.loads(args.extra_evidence.read_text()):
            source = Path(item['path'])
            target = output / item['destination']
            if source.is_dir():
                extras += collect_tree(source, target, output)
            else:
                extras.append(copy_file(source, target, output, item.get('purpose', 'Separate executor/oracle/identity evidence; original receipt remains unchanged.')))
    source_refs = []
    for head in sorted(set(item['head'] for item in items)):
        for relative in COMMON_SOURCES + ['tests/issue123_adopted_slices_browser.cjs', 'tests/room_outline_direct_rows_browser.js',
                                           'tests/test_scenario_editor_tickets.js', 'tests/test_scenario_recovery_owner.js',
                                           'tests/test_reference_workspace_races.js', 'tests/test_scenario_resume_checkpoint.js']:
            result = subprocess.run(['git', 'show', head + ':' + relative], cwd=REPO, capture_output=True)
            if result.returncode:
                continue
            original = HERE / 'ui-retained-source-snapshots' / head / relative
            original.parent.mkdir(parents=True, exist_ok=True)
            original.write_bytes(result.stdout)
            ref = copy_file(original, output / 'source' / head / relative, output,
                            'Full committed source at the exact tested SHA; original bytes/hash vs publication path projection recorded separately.')
            ref.update(repositoryPath=relative, sourceHead=head, publishedCopyWasExecuted=False)
            source_refs.append(ref)
    manifest = {'schema': 'geometry-ui-single-room-history-public/1',
                'preparedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'preparerActor': '/root/delivery_closeout',
                'scope': 'Prior completed scope-specific UI/room/projection/normal-control/Resume/unit executions; original product failures and metadata-only wrapper errors retained. Not full integration or final delivery acceptance.',
                'rounds': rounds, 'historyReviewsAndExecutorSources': extras, 'fullTestedCommitSourceCopies': source_refs,
                'historicalFullCdp': {'testedHead': '5174a8dafd8c48329d7166abbd3d104e3c28c0c4', 'pass': 2207, 'fail': 0, 'skip': 0, 'rebound': False},
                'windows173': {'pass': 1692, 'fail': 2, 'exitCode': 1, 'completed': False, 'cloudOriginalsReceived': False, 'partialsAggregated': False, 'goldenComparedByThisPacket': False},
                'omissions': ['Private queue DB/events/owner threads', 'Private feedback and user source files', 'Standalone large screenshots/profile directories', 'Native binary/sidecar bytes'],
                'limits': ['Each scope stands alone; counts are never summed into full CDP/Space acceptance.', 'Old original projection 3/7 and8/2 remain unmodified; separately controlled hole-order proof does not relabel them.', 'Declared/UI/projection oracle versions retained at their original hashes.', 'Current source and executables never rebound to historical gaps.', 'Synthetic trace screenshots/resources retained only as part of their actual trace; machine path projections preserve original per-entry/file hashes.', 'Missing queue v6 remains currentunknown with historicalv5; no empty DB created.'],
                'releaseApproved': False}
    if args.metadata:
        manifest.update(json.loads(args.metadata.read_text()))
    shutil.copyfile(args.readme or (HERE / 'ui-history-README.md'), output / 'README.md')
    manifest['publicFiles'] = [{'path': path.relative_to(output).as_posix(), 'bytes': path.stat().st_size, 'sha256': p.sha(path)} for path in sorted(output.rglob('*')) if path.is_file()]
    p.write(output / 'manifest.json', manifest)
    for path in output.rglob('*'):
        if path.is_file() and path.suffix.lower() not in {'.png', '.pdf', '.zip', '.gcanvas'}:
            assert not p.private(path.read_text()), path
    print(json.dumps({'bundle': str(output), 'manifestSha256': p.sha(output / 'manifest.json'), 'files': len(manifest['publicFiles']) + 1,
                      'bytes': sum(path.stat().st_size for path in output.rglob('*') if path.is_file()), 'rounds': len(rounds)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
