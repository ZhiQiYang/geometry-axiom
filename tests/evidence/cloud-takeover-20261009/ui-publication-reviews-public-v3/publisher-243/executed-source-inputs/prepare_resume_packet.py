"""Publish retained Resume evidence into a fresh scratch bundle, without retesting.

No repo or GitHub mutations. Synthetic package archives are inspected before
publication; original receipts/logs and historical SHA/dirty/results remain intact.
"""
import argparse
import datetime
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('publication', HERE / 'prepare_cdp_diagnosis.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
UNIT = Path('<unit-evidence-root>')
OLD = Path('<old-unit-evidence-root>')
EXEC = p.BASE / 'resume-128afbec-evidence-packet'
REPO = Path('<resume-repository-root>')
HEAD = '128afbec9240f36ae149682830e6b3a96ea02101'
EARLY = 'f5638ec4288eeec4e014c5618eed3fd1886080ea'
p.REPLACEMENTS.update({str(UNIT): '<unit-evidence-root>', str(OLD): '<old-unit-evidence-root>'})
original_redact = p.redact_text


def redact_text(text):
    return re.sub(r'<isolated-browser-profile>"\x27<>]+', '<isolated-browser-profile>', original_redact(text))


p.redact_text = redact_text
original_private = p.private
p.private = lambda text: original_private(text) or '<isolated-profile-prefix>' in text


def publish_receipt(original, target, output):
    j = json.loads(original.read_text())
    published = p.project(j)
    published['publicProjection'] = {
        'originalPathLabel': p.redact_text(str(original)),
        'originalSha256': p.sha(original),
        'originalBytes': original.stat().st_size,
        'originalRetainedOutsideGit': True,
        'changes': 'Machine root, executable and isolated feedback/profile paths only; historical SHA, dirty, identity, command, exit and original hashes/results preserved.',
    }
    p.write(target, published)
    return j


def unit_round(output, label, folder, head, expected):
    directory = UNIT / folder
    original = directory / 'receipt.json'
    destination = output / 'units' / label
    j = publish_receipt(original, destination / 'receipt.public.json', output)
    assert j['before']['head'] == j['after']['head'] == head
    assert j['before']['dirty'] == j['after']['dirty'] == ''
    assert j['sourceHashesBefore'] == j['sourceHashesAfter']
    assert j['sourceUnchanged'] and j['identityUnchanged']
    assert j['execution']['exitCode'] == expected
    logs = []
    for entry in j['logs']:
        source = Path(entry['path'])
        assert p.sha(source) == entry['sha256'] and source.stat().st_size == entry['bytes']
        logs.append(p.copy_projection(source, destination / (entry['stream'] + '.public.log'), output,
                                     'Actual complete unit command stream; originals and separate results preserved.'))
    selected = [arg for arg in j['command'] if arg.startswith('tests/')]
    sources = []
    for relative in selected:
        original_source = HERE / 'retained-unit-source-snapshots' / head / relative
        original_source.parent.mkdir(parents=True, exist_ok=True)
        original_source.write_bytes(subprocess.check_output(['git', 'show', head + ':' + relative], cwd=REPO))
        assert p.sha(original_source) == j['sourceHashesBefore'][relative]
        entry = p.copy_projection(original_source, destination / 'source' / relative, output,
                                  'Executed committed source; explicit publication path projection where needed. Published copy was not executed.')
        entry.update(repositoryPath=relative, sourceHead=head, publishedCopyWasExecuted=False)
        sources.append(entry)
    return {'name': label, 'testedHead': head, 'dirty': False, 'command': p.project(j['command']),
            'scope': j['scope'], 'result': j['result'], 'exitCode': j['execution']['exitCode'],
            'originalReceiptSha256': p.sha(original),
            'receiptPath': (destination / 'receipt.public.json').relative_to(output).as_posix(),
            'logs': logs, 'sources': sources, 'nativeMeaning': j['limits'], 'releaseApproved': False}


def old_override_round(output, name):
    original = OLD / (name + '-receipt.json')
    destination = output / 'override-units' / name
    j = publish_receipt(original, destination / 'receipt.public.json', output)
    assert j['testedSHA'] == EARLY and j['dirtyAtProductSourceCapture'] is False
    assert j['executionCheckoutDirtyState'].startswith('not captured')
    source = Path(j['productExecutionSource'])
    driver = Path(j['driverExecutionSnapshot'])
    log = Path(j['rawLog'])
    assert p.sha(source) == j['productSourceSha256']
    assert p.sha(driver) == j['driverSha256']
    assert p.sha(log) == j['rawLogSha256']
    sources = [p.copy_projection(driver, destination / 'driver.public.cjs', output,
                                 'Exact retained driver snapshot; reconstructed historical versions explicitly labeled in original receipt, not substituted for actual product source.')]
    logs = [p.copy_projection(log, destination / 'command.public.log', output, 'Original source-override controlled unit result, not clean formal checkout execution.')]
    return {'name': name, 'testedProductSourceHead': EARLY, 'dirtyAtProductSourceCapture': False,
            'executionCheckoutDirty': 'unknown', 'executionCheckoutDirtyMeaning': j['executionCheckoutDirtyState'],
            'sourceOverride': p.project(j['productExecutionSource']),
            'productSourceSha256': j['productSourceSha256'],
            'tests': j['tests'], 'pass': j['pass'], 'fail': j['fail'], 'skip': j['skip'],
            'completed': j['completed'], 'exitCode': j['exitCode'], 'note': j['note'],
            'originalReceiptSha256': p.sha(original),
            'receiptPath': (destination / 'receipt.public.json').relative_to(output).as_posix(),
            'logs': logs, 'driverSources': sources, 'releaseApproved': False}


def browser_round(output, folder):
    original_directory = p.BASE / folder
    retained = EXEC / folder
    original = original_directory / 'receipt.json'
    destination = output / 'browser' / folder
    assert p.sha(original) == p.sha(retained / 'receipt.json')
    j = publish_receipt(original, destination / 'receipt.public.json', output)
    assert j['before']['git']['head'] == HEAD and j['before']['git']['status'] == ''
    if j.get('after'):
        assert j['after']['git']['head'] == HEAD and j['after']['git']['status'] == ''
        assert j['before']['sources'] == j['after']['sources']
    log = original_directory / 'command.log'
    assert p.sha(log) == j['log']['sha256']
    logs = [p.copy_projection(log, destination / 'command.public.log', output, 'Actual command log; r3 is empty because preflight rejected before execution.')]
    artifacts = []
    artifact_dir = retained / 'original-temp-artifacts'
    for source in sorted(artifact_dir.rglob('*')) if artifact_dir.exists() else []:
        if not source.is_file() or source.suffix not in {'.json', '.gcanvas'}:
            continue
        target = destination / 'synthetic-artifacts' / source.relative_to(artifact_dir)
        if source.suffix == '.gcanvas':
            with zipfile.ZipFile(source) as z:
                entries = z.namelist()
                assert not any(item.startswith('/') or '..' in Path(item).parts for item in entries)
                manifest = json.loads(z.read('manifest.json'))
                assert manifest['sources'] and all(entry['name'] == 'resume-synthetic.pdf' for entry in manifest['sources'])
                assert not p.private(json.dumps(manifest, ensure_ascii=False))
                assert not p.private(z.read('world.scene').decode())
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            assert p.sha(source) == p.sha(target)
            artifacts.append({'path': target.relative_to(output).as_posix(), 'originalBytes': source.stat().st_size,
                              'sha256': p.sha(target), 'originalSha256': p.sha(source), 'byteIdenticalOriginal': True,
                              'scope': 'Full synthetic package with generated resume-synthetic.pdf source; no user document.'})
        else:
            artifacts.append(p.copy_projection(source, target, output, 'Synthetic browser state/network/results or actual run executable identity; no private user state.'))
    result_path = Path(j['probeCensus']['resultsPath'])
    if j['probeCensus'].get('resultsSha256'):
        assert p.sha(result_path) == j['probeCensus']['resultsSha256']
    if '-r4-' in folder:
        assert j['execution']['exitCode'] == j['gateExitCode'] == 0 and j['problems'] == []
        assert j['probeCensus']['actualCases'] == j['probeCensus']['pass'] == 4
        assert j['probeCensus']['fail'] == 0 and j['probeCensus']['completed'] and j['probeVerified']
        results = json.loads(result_path.read_text())
        assert len(results) == 4 and sum(len(x['assertions']) for x in results) == 56
        assert all(x['ok'] and not x['pageErrors'] and all(a['passed'] for a in x['assertions']) for x in results)
    return {'name': folder, 'testedHead': HEAD, 'dirty': False, 'status': j['status'],
            'executionExitCode': j.get('execution', {}).get('exitCode') if j.get('execution') else None,
            'gateExitCode': j['gateExitCode'], 'probeCensus': p.project(j['probeCensus']),
            'identityProblems': p.project(j['problems']), 'actualBrowserExecutionIdentity': p.project(j.get('browserExecutionIdentity')),
            'originalReceiptSha256': p.sha(original),
            'receiptPath': (destination / 'receipt.public.json').relative_to(output).as_posix(),
            'logs': logs, 'syntheticArtifacts': artifacts, 'releaseApproved': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    output = parser.parse_args().output.resolve()
    assert not output.exists() and output.is_relative_to(HERE)
    output.mkdir(parents=True)
    units = [unit_round(output, 'resolve-05e59392', 'serve-unit-05e59392', '05e59392e7c933c16268c711b450c5970aef7270', 0),
             unit_round(output, 'resolve-f5638ec4', 'serve-unit-f5638ec4', EARLY, 0),
             unit_round(output, 'scenario-f5638ec4-original-three', 'scenario-units-f5638ec4', EARLY, 1),
             unit_round(output, 'scenario-128afbec-formal-four', 'scenario-units-128afbec', HEAD, 0)]
    overrides = [old_override_round(output, name) for name in ('original-driver', 'corrected-fixture-driver', 'corrected-package-oracle-driver', 'metadata-negative-control')]
    shared_sources = []
    for source in sorted((OLD / 'geometry-web').rglob('*')) + sorted((OLD / 'fixture-closure').rglob('*')):
        if source.is_file():
            shared_sources.append(p.copy_projection(source, output / 'override-units' / 'retained-source-closure' / source.relative_to(OLD), output,
                                                    'Original captured f563 product override / controlled fixture closure; original hashes retained.'))
    shared_sources.append(p.copy_projection(OLD / 'source-identity.json', output / 'override-units' / 'source-identity.public.json', output, 'Product source clean capture receipt; each execution checkout dirty remains unknown.'))
    browsers = [browser_round(output, folder) for folder in ('after-resume-128afbec-20261009', 'after-resume-128afbec-r2-20261009', 'after-resume-128afbec-r3-20261009', 'after-resume-128afbec-r4-20261009')]
    executor = json.loads((EXEC / 'executor-review.json').read_text())
    assert executor['testedHead'] == HEAD and executor['validScope']['assertions'] == 56
    sources = []
    for entry in executor['executedSourceClosure']:
        source = Path(entry['path'])
        assert p.sha(source) == entry['sha256']
        sources.append(p.copy_projection(source, output / 'executed-source-closure' / source.relative_to(EXEC / 'executed-source-closure'), output,
                                         'Byte/hash-bound executed 128afbec committed source closure; paths projected only where needed.'))
    for entry in executor['harnessSources']:
        source = Path(entry['copyPath'])
        assert p.sha(source) == entry['sha256']
        sources.append(p.copy_projection(source, output / 'harness-sources' / source.name, output,
                                         'Actually executed scratch probe/runner snapshots or explicit correction metadata; publication copies not executed.'))
    sources.append(p.copy_projection(EXEC / 'executor-review.json', output / 'executor-byte-review.public.json', output,
                                     'Same executor consistency review; not independent actor acceptance.'))
    formal_log = (UNIT / 'scenario-units-128afbec' / 'stdout.log').read_text()
    # Node selected its native spec reporter in this recorded invocation.
    # Verify successful named rows rather than assuming a TAP renderer.
    formal_names = re.findall(r'^✔ (.+) \([0-9.]+ms\)$', formal_log, re.M)
    source = subprocess.check_output(['git', 'show', HEAD + ':tests/test_scenario_resume_checkpoint.js'], cwd=REPO).decode()
    resume_names = re.findall(r"unit\('([^']+)'", source)
    assert len(resume_names) == 15 and all(name in formal_names for name in resume_names)
    manifest = {'schema': 'geometry-safe-resume-public/1', 'preparedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'preparerActor': '/root/delivery_closeout', 'testedProductHead': HEAD, 'dirty': False,
                'scope': 'Complete four-file Node unit command plus four synthetic same-parent/same-native-session explicit Pause/Resume Finish/Cancel browser lifecycles at 1280 and 390px. Historical failures retained separately; no full CDP or general crash recovery claim.',
                'units': units, 'historicalControlledOverrides': overrides, 'overrideSourceClosure': shared_sources,
                'formalResume15': {'enclosingRun': 'scenario-128afbec-formal-four', 'names': resume_names, 'pass': 15, 'fail': 0,
                                   'separateCommandExecuted': False, 'meaning': 'Subset of the actual 132-test complete command; never added to 131 passes.'},
                'browserAttempts': browsers, 'executedSourceAndHarnessCopies': sources,
                'historicalFullCdp': {'testedHead': '5174a8dafd8c48329d7166abbd3d104e3c28c0c4', 'pass': 2207, 'fail': 0, 'skip': 0, 'rebound': False},
                'windows173': {'pass': 1692, 'fail': 2, 'exitCode': 1, 'completed': False, 'rawReceivedInCloud': False, 'partialResultsAggregated': False, 'goldenComparedByThisTask': False},
                'limitations': executor['limitations'] + ['Unit counts/partial passes are not added into full acceptance.', 'Override execution checkout dirty state not captured; unknown despite clean immutable product source capture.', 'No abrupt reload/crash, service restart, cross-session/profile/origin, physical device/IME/OS chooser or full CDP/Space/golden acceptance.', 'Private queue v6 missing: preserve historical v5, current unknown; no empty DB created.', 'Original identity gaps never rebound to current executable.'],
                'omissions': ['Private feedback/user documents', 'Browser traces/profiles/screenshots', 'Native binary/sidecar bytes', 'Private work-manager DB/events/owner thread'], 'releaseApproved': False}
    shutil.copyfile(HERE / 'resume-README.md', output / 'README.md')
    manifest['publicFiles'] = [{'path': path.relative_to(output).as_posix(), 'bytes': path.stat().st_size, 'sha256': p.sha(path)} for path in sorted(output.rglob('*')) if path.is_file()]
    p.write(output / 'manifest.json', manifest)
    for path in output.rglob('*'):
        if path.is_file() and path.suffix != '.gcanvas':
            assert not p.private(path.read_text()), path
    print(json.dumps({'bundle': str(output), 'manifestSha256': p.sha(output / 'manifest.json'), 'files': len(manifest['publicFiles']) + 1,
                      'bytes': sum(path.stat().st_size for path in output.rglob('*') if path.is_file()), 'units': len(units), 'browserAttempts': len(browsers)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
