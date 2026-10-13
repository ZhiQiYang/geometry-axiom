"""Readonly public manager-availability packet audit.

Does not execute the availability checker, CLI, packaging engine or API and
never reads private receipts, root inventories, database/export payloads.
"""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import sys

S = Path('<workspace-path>')
D = S / 'geometry-delivery-closeout-20261009'
P = D / 'manager-availability-f3-public-v3'
OLD = D / 'manager-availability-f3-public-v2'
HELPER = S / 'geometry-assembly-packet-review-v4-independent.py'
assert hashlib.sha256(HELPER.read_bytes()).hexdigest() == '0c7d16eac138b21ec9a2d70235e5e8ba8b57336a5c449cea2e66aa6583f35e60'
spec = importlib.util.spec_from_file_location('readonly_parser_helpers', HELPER)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
OUT = S / 'geometry-manager-availability-v3-independent-review'
MANIFEST = '151c1fd14b5d1e85566871911c5f4e9e348d6b75a94a055577feea7e80935de0'


def main():
    assert not OUT.exists()
    OUT.mkdir()
    checks = []
    def check(n, v, detail=None):
        checks.append({'name': n, 'passed': bool(v), 'detail': detail})
    m, old = h.load(P / 'manifest.json'), h.load(OLD / 'manifest.json')
    entries = m['publicFiles']
    paths = [x['path'] for x in entries]
    census = {x.relative_to(P).as_posix() for x in P.rglob('*') if x.is_file()}
    check('final-ready exact manifest SHA256', h.sha((P / 'manifest.json').read_bytes()) == MANIFEST)
    check('exact8listed + manifest9 files no omitted extras', len(paths) == len(set(paths)) == 8 and census == set(paths) | {'manifest.json'})
    for row in entries:
        f = P / row['path']
        data = f.read_bytes()
        check('safe public path ' + row['path'], not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts and not f.is_symlink())
        check('public bytes/hash exact ' + row['path'], len(data) == row['bytes'] and h.sha(data) == row['sha256'])
        if f.suffix == '.json':
            try:
                h.loads(data)
                check('unique structured JSON keys ' + row['path'], True)
            except Exception as exc:
                check('unique structured JSON keys ' + row['path'], False, repr(exc))
    extras = h.load(D / 'manager-availability-extras-v2.json')
    bindings = {x['destination']: Path(x['path']) for x in extras}
    for ref in m['historyReviewsAndExecutorSources']:
        original = bindings[ref['path']]
        original_data = original.read_bytes()
        public = (P / ref['path']).read_bytes()
        check('retained original identity ' + ref['path'], len(original_data) == ref['originalBytes'] and h.sha(original_data) == ref['originalSha256'])
        check('all nonpath-token text/value associations exact ' + ref['path'], h.equal_projection(original_data, public, original.suffix))
        check('original/public projection flags accurate ' + ref['path'], ref['byteIdenticalOriginal'] == (original_data == public) and ref['publicProjection'] == (original_data != public))
    availability = h.load(P / 'availability.public.json')
    selected = h.load(P / 'selected-execution.public.json')
    command = h.load(P / 'cli-help/existing-cli-help-only.command.json')
    check('exact public summary source SHA f13f', h.sha((P / 'availability.public.json').read_bytes()) == m['availabilityOriginalSHA256'] == 'f13f606c62ac6b49f4e5c9a7c0ae18f5fdd67c504ac9884fe45e5506b6602749')
    check('original19:31:13 clean fullf3 beforeafter', availability['checkedAt'] == '2026-10-09T19:31:13.293104+00:00' and availability['candidateFullSHA'] == 'f3b8285729b42cd22451c98cba1e2ec4514517f3' and availability['dirtyBefore'] == availability['dirtyAfter'] == '')
    check('current real queue unknown no real ledger accessible', availability['currentRealQueueStatus'] == selected['currentRealQueueStatus'] == m['currentRealQueueStatus'] == 'unknown' and availability['originalRealLedgerOrValidCompleteExportAccessible'] is m['originalRealLedgerOrValidCompleteExportAccessible'] is False)
    check('reconcile/list-ready/list-alerts NOT_EXECUTED honest', all(selected[k] == 'NOT_EXECUTED' and availability[k] == 'not executed: existing real ledger unavailable' for k in ['reconcile', 'listReady', 'listAlerts']))
    check('no emptyDB Store/import/owner/approval mutation', availability['oldDataPreserved'] is True and availability['newEmptyDatabaseCreated'] is availability['storeConstructed'] is availability['importsAssignmentsApprovalsReviewsGitOrProductWrites'] is selected['storeConstructed'] is False)
    check('incremental199roots84DB not new exhaustive fullscan', availability['incrementalScope'] == {'newOrDirectoryEntryChangedRoots': 199, 'newDatabaseFiles': 84, 'newWorkManagerLedgerCandidates': 0, 'newExactNonSyntheticExportCandidates': 0, 'existingDefaultOrKnownOriginalLocationsPresent': 0} and 'reuses the prior fullscan' in availability['limits'][0])
    check('historical synthetic14empty1exports8 not recovery', availability['historicalQaCandidates'] == {'syntheticLedgers': 14, 'emptyQaLedger': 1, 'syntheticPortableExports': 8} and availability['qaCandidatesNotUsedAsRecovery'] is True)
    check('historicalv5 ready59/0write alerts374 not current', availability['historicalPublicV5']['notCurrentObservation'] is True and availability['historicalPublicV5']['ready'] == '59 read_only / 0 write, historical only' and availability['historicalPublicV5']['alerts'] == '374, historical only')
    check('explicit selected document not full private receipt', selected['schema'] == 'geometry-manager-selected-execution-public-projection/1' and selected['originalPrivateReceiptPublished'] is m['publicSelectionIsFullPrivateReceipt'] is False and selected['privateDatabaseOrExportContentsPublished'] is False and 'not the full private receipt' in selected['scope'])
    check('original private receipt is hash reference only and omitted file', len(selected['originalPrivateReceiptSHA256']) == 64 and not any('private' in x.lower() or x.endswith(('.db', '.sqlite', '.sqlite3', '.zip')) for x in census))
    check('original missing PID/proc/live exe limit remains honest', 'not /proc argv' in selected['actualInvocationLimit'] and 'process PID/proc invocation/live executable bytes were not independently captured' in selected['actualInvocationLimit'])
    check('original availability tool0 is ROOT-reported distinctprovenance', selected['rootReportedAvailabilityToolExitCode'] == 0 and 'ROOT delivery instruction' in selected['rootReportedToolExitProvenance'] and selected['checksAreProductAssertions'] is selected['productOrBrowserExecuted'] is False)
    help_original = h.load(bindings['cli-help/existing-cli-help-only.command.json'])
    check('actual existing CLI command solely --help exit0', help_original['command'][-1] == '--help' and len(help_original['command']) == 4 and help_original['command'][1] == '-B' and help_original['exitCode'] == command['exitCode'] == selected['actualCliHelpSubprocessExitCode'] == 0 and h.sha(bindings['cli-help/existing-cli-help-only.command.json'].read_bytes()) == selected['actualCliHelpOriginalCommandSHA256'])
    for stream in ['stdout', 'stderr']:
        log = P / ('cli-help/existing-cli-help-only.' + stream + '.log')
        record = next(x for x in command['logs'] if x['stream'] == stream)
        check('actual --help original raw stdout/stderr bindings ' + stream, record['bytes'] == log.stat().st_size and record['sha256'] == h.sha(log.read_bytes()) == selected['actualCliHelpOriginal' + stream.title() + 'SHA256'])
    check('actual help stdout retained490bytes stderr0', (P / 'cli-help/existing-cli-help-only.stdout.log').stat().st_size == 490 and (P / 'cli-help/existing-cli-help-only.stderr.log').stat().st_size == 0)
    checker = bindings['source/geometry-check-final-manager-availability-f3b.py']
    preparer = bindings['source/geometry-prepare-final-manager-availability-f3b.py']
    check('checker original sourceeadcc matches selectedexecutoridentity', h.sha(checker.read_bytes()) == selected['originalRecordedExecutor']['scriptSHA256'] == 'eadcc728ce9d8c283f27e42752ea76ff049cf0aa10cd4f4c48a47a2cfd192259')
    check('preparer original source61e reference not fabricatedreceipt', selected['sourceBindings'][1]['originalSHA256'] == h.sha(preparer.read_bytes()) == '61e166ccd4c368c27cd6da6291e1598e56c9410128be95c31eea0f04b3f83d06' and 'no fabricated execution receipt' in selected['sourceBindings'][1]['role'])
    imp = m['publicationImplementation']
    source_names = {'finalMetadataReviserSHA256': 'finalize_manager_availability_public_f3_v3.py', 'actualPackagingWrapperOriginalSHA256': 'prepare_manager_availability_public_f3_v2.py', 'dynamicInputBuilderOriginalSHA256': 'prepare_manager_availability_public_f3_v1.py', 'projectionEngineOriginalSHA256': 'prepare_ui_history_packet_v8.py'}
    for field, name in source_names.items():
        check('publication source role identity exact ' + field, h.sha((D / name).read_bytes()) == imp[field])
    for field, name in {'configurationSHA256': 'manager-availability-config-v2.json', 'extrasSHA256': 'manager-availability-extras-v2.json', 'metadataSHA256': 'manager-availability-metadata-v2.json', 'originalBuildReceiptSHA256': 'manager-availability-package-build-v2.json'}.items():
        check('publication input/receipt SHA exact ' + field, h.sha((D / name).read_bytes()) == imp[field])
    wrapper = (D / 'prepare_manager_availability_public_f3_v2.py').read_text()
    v1 = (D / 'prepare_manager_availability_public_f3_v1.py').read_text()
    check('immutablev1 dynamicinput dependency actually explicit inwrapper', "old=Path('<workspace-path>')" in wrapper and 'source=old.read_text().replace' in wrapper and 'exec(compile(source' in wrapper and 'all(private[\'checks\'].values())' in v1)
    check('v2 corrects original preflight list schema without touchingoriginal', "all(r['ok'] for r in private['checks'])" in wrapper and "next(r for r in help_command['logs'] if r['stream']==k)" in wrapper and '.write_text' not in wrapper)
    build = h.load(D / 'manager-availability-package-build-v2.json')
    check('actual packaging0 sourcev2 wrapper vs child boundedv8 command clear', build['actualExitCode'] == imp['actualPackagingExitCode'] == 0 and build['builderSHA256'] == imp['actualPackagingWrapperOriginalSHA256'] == m['publicationSourceSHA256'] and Path(build['command'][2]).name == 'prepare_ui_history_packet_v8.py' and build['productExecuted'] is build['privateReceiptPublished'] is False)
    check('actual package buildstdout names immutablev2 SHA', old['schema'] == m['schema'] and m['supersededScratchV2ManifestSHA256'] == h.sha((OLD / 'manifest.json').read_bytes()) == h.loads(build['stdout'])['manifestSha256'])
    check('freshv3 metadata time valid later than v2', datetime.datetime.fromisoformat(m['preparedUtc']) > datetime.datetime.fromisoformat(old['preparedUtc']))
    check('all original summary/selection/help/source files unchanged fromv2', all((OLD / relative).read_bytes() == (P / relative).read_bytes() for relative in set(paths) - {'README.md'}))
    check('all original metadata unchanged exceptfresh roles/time/census', all(m[k] == v for k, v in old.items() if k not in {'preparedUtc', 'publicFiles'}))
    check('README original prose remains unchanged explicitv1/v2history', (P / 'README.md').read_text().startswith((OLD / 'README.md').read_text()) and 'v1 schema-reader preflight failed before publication' in (P / 'README.md').read_text())
    check('no product acceptance release approval or testcounts invented', m['rounds'] == [] and m['fullTestedCommitSourceCopies'] == [] and m['historicalFullCdp'] is m['windows173'] is None and m['releaseApproved'] is imp['productExecuted'] is False and all(x['ok'] for x in selected['checks']) and len(selected['checks']) == 9)
    check('manifest and parser source immutable throughout', h.sha((P / 'manifest.json').read_bytes()) == MANIFEST and h.sha(HELPER.read_bytes()) == '0c7d16eac138b21ec9a2d70235e5e8ba8b57336a5c449cea2e66aa6583f35e60')
    failures = [x for x in checks if not x['passed']]
    raw = ''.join(('PASS ' if x['passed'] else 'FAIL ') + x['name'] + '\n' for x in checks)
    (OUT / 'command.raw.log').write_text(raw)
    result = {'schema': 'geometry-manager-availability-v3-independent-review/1', 'actor': '/root/publication_final_review/assembly_packet_review', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': [sys.executable, '-B', str(Path(__file__).resolve())], 'actualPython': str(Path(sys.executable).resolve()), 'actualPythonSHA256': h.sha(Path(sys.executable).resolve().read_bytes()), 'reviewSourceSHA256': h.sha(Path(__file__).read_bytes()), 'parserHelperSourceSHA256': h.sha(HELPER.read_bytes()), 'actualExitCode': 1 if failures else 0, 'passedMetadataChecks': len(checks) - len(failures), 'failedMetadataChecks': len(failures), 'countsAreProductTests': False, 'productOrBrowserOrServiceOrCLIOrAPIExecuted': False, 'privateReceiptOrDatabaseOrExportOrRootInventoryInspected': False, 'selectedFullPrivateReceiptVerified': False, 'repositoryOrGitHubWritten': False, 'packetOrOriginalsChanged': False, 'manifestSHA256': MANIFEST, 'originalV1PreflightExitHistory': {'claimedActualExitCode': 1, 'producerReportedOriginalToolChunk': 'e619f8', 'producerReportedOriginalError': 'AttributeError list.values before packet/material inputs created', 'originalSeparateTerminalReceiptSeen': False, 'originalIndependentRawErrorFileSeen': False, 'basis': 'Original tool-only failure reported by producer in this thread; immutable v1 list-schema bug remains in source and corrected dynamically by v2. This reviewer does not fabricate/reproduce a missing original terminal or error file.'}, 'producerReportedLaterToolResults': {'v2Packaging': {'toolChunk': '59d25f', 'exitCode': 0, 'basis': 'Producer declaration; original subprocess build-v2 receipt verified separately'}, 'v3MetadataFinalizer': {'toolChunk': 'c38f44', 'exitCode': 0, 'basis': 'Producer declaration only; source/hash closure and final artifact bytes verified separately'}}, 'currentRealQueueStatus': 'unknown', 'reconcile': 'NOT_EXECUTED', 'listReady': 'NOT_EXECUTED', 'listAlerts': 'NOT_EXECUTED', 'rawLog': {'path': str(OUT / 'command.raw.log'), 'bytes': (OUT / 'command.raw.log').stat().st_size, 'sha256': h.sha((OUT / 'command.raw.log').read_bytes())}, 'findings': failures, 'checks': checks}
    (OUT / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:result[k] for k in ['actualExitCode', 'passedMetadataChecks', 'failedMetadataChecks', 'reviewSourceSHA256', 'rawLog', 'findings']}))
    return result['actualExitCode']


if __name__ == '__main__':
    raise SystemExit(main())
