"""Seal existing independent reviews, including failed reviewer assumptions."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

BASE = Path('<workspace-path>')
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=False)
ROOT_SCRATCH = Path('<workspace-path>')


def binding(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


reviews = [
    ('asm-v4-first', ROOT_SCRATCH / 'geometry-assembly-v4-independent-publication-review', ROOT_SCRATCH / 'geometry-assembly-packet-review-v4-independent.py', 1, 1152, 3),
    ('asm-v4-projection-supplement', ROOT_SCRATCH / 'geometry-assembly-v4-independent-publication-supplement', ROOT_SCRATCH / 'geometry-assembly-packet-review-v4-supplement.py', 0, 132, 0),
    ('asm-v5-first', ROOT_SCRATCH / 'geometry-assembly-v5-independent-publication-review', ROOT_SCRATCH / 'geometry-assembly-packet-review-v5-independent.py', 1, 629, 1),
    ('asm-v5-time-supplement-final', ROOT_SCRATCH / 'geometry-assembly-v5-independent-time-supplement', ROOT_SCRATCH / 'geometry-assembly-packet-review-v5-time-supplement.py', 0, 21, 0),
    ('space-v2', ROOT_SCRATCH / 'geometry-space-v2-independent-publication-review', ROOT_SCRATCH / 'geometry-space-packet-review-v2-independent.py', 0, 1111, 0),
    ('space-v2-source-bindings', ROOT_SCRATCH / 'geometry-space-v2-independent-source-bindings-review', ROOT_SCRATCH / 'geometry-space-packet-review-v2-source-bindings.py', 0, 64, 0),
    ('qualified-first-full', BASE / 'qualified-full-v1-review', BASE / 'review_qualified_full_v1.py', 0, 2320, 0),
    ('prose-correction', BASE / 'prose-correction-v1-review', BASE / 'review_prose_corrections_v1.py', 0, 1709, 0),
    ('shell-first', BASE / 'shell-packet-v1-review', BASE / 'review_shell_packet_v1.py', 1, 14075, 3),
    ('shell-annotation-mobile-supplement', BASE / 'shell-packet-v1-supplement', BASE / 'review_shell_packet_v1_supplement.py', 1, 587, 1),
    ('shell-visible-create-final', BASE / 'shell-visible-create-resolution-v1', BASE / 'review_shell_visible_create_resolution_v1.py', 0, 569, 0),
    ('manager-availability-v3', ROOT_SCRATCH / 'geometry-manager-availability-v3-independent-review', ROOT_SCRATCH / 'geometry-manager-availability-v3-independent-review.py', 0, 78, 0),
]
records = []
for name, directory, source, actual_exit, passed, failed in reviews:
    report = directory / 'report.json'
    data = json.loads(report.read_bytes())
    raw = directory / 'command.raw.log'
    if not raw.exists():
        raw = BASE / (directory.name + '.raw.log')
    exit_field = data.get('actualExitCode', data.get('reviewDecisionExitCode'))
    passed_field = data.get('passedMetadataChecks', data.get('metadataChecksPassed'))
    failed_field = data.get('failedMetadataChecks', data.get('metadataChecksFailed'))
    assert (exit_field, passed_field, failed_field) == (actual_exit, passed, failed), name
    source_hash = data.get('reviewSourceSHA256', data.get('sourceSHA256'))
    assert binding(source)['sha256'] == source_hash, name
    record = {'name': name, 'actor': data.get('actor', data.get('reviewerActor')), 'actualReviewExitCode': actual_exit, 'actualExitProvenance': 'Actual tool result received by this actor or its child and matching immutable executed reviewer terminal/raw report; not an original product exit.', 'passedMetadataChecks': passed, 'failedMetadataChecks': failed, 'countsAreProductAssertions': False, 'report': binding(report), 'rawLog': binding(raw), 'executedReviewerSource': binding(source), 'actualPython': data.get('actualPython'), 'actualPythonSHA256': data.get('actualPythonSHA256'), 'command': data.get('actualCommand', data.get('reviewCommand', data.get('command'))), 'manifestSHA256': data.get('manifestSHA256'), 'originalFindingsPreserved': data.get('findings', data.get('originalFindingsPreserved', data.get('priorFindingsPreserved', [])))}
    if data.get('parserHelperSourceSHA256'):
        dependency = ROOT_SCRATCH / 'geometry-assembly-packet-review-v4-independent.py'
        assert binding(dependency)['sha256'] == data['parserHelperSourceSHA256']
        record['readonlyParserDependency'] = binding(dependency)
    records.append(record)

packets = [
    ('ASM', 'f3b-original-assembly-public-v5', 'a8254cb4fab9151008f2c65ed37e01646e1542c828a8c59f2f9bc1532d8688a6', True, 'Fresh v5 fixes a true metadata role label. Old1152/3 includes two public-JS byte-equality reviewer assumptions and one real role question;132/0 clarifies projection. New629/1 was fresh preparedUtc equality assumption;21/0 fixes that reviewer premise without changing198 original artifact bytes.'),
    ('Space', 'f3b-durable-space-public-v2', 'dbd3e468c878b2bea7c48b54ea578a795cbdb142939b115c903c732461a4bd4a', True, '228/0 five declared groups; two timber groups omitted. Actual Node/gate/controller/launcher/stop0 distinct from owned service−15 and existing Z observations.1111/0 and64/0 are separate metadata reviews.'),
    ('qualified-first-full', 'f3b-unreceipted-full-public-v1', '5279b00e7b2425e582af5c8ce62cea2675eb7f54aeffa85e86a40049ee7b5ea8', True, 'Raw2207/0/0 golden84 complete stays qualified unreceipted: original live exe/actualNode/wrapper/lifecycle exits unknown; new observation0 is not original gate0. One original EXPECTED fb-auto-probe remains. No original receipt invented.'),
    ('prose-correction', 'public-prose-corrections-public-v1', 'c0a5c3287614b4f4720958ca6179634a22ebd64d7a3de43748ee699d80e48043', True, '16 originals/36 refs/194 tokens all inverse non-token bytes checked. Old7 published and5 READY manifests/files/Git blobs remain historically lossy and unchanged; addendum does not assert old non-token bytes were intact.'),
    ('shell-return', 'f3b-shell-return-scopes-public-v1', '4ec51be9a583d025d2a1cc06e78f3a260a2241dc295a1985efa14f4aa9d12867', True, 'Original16/1 incomplete preserved versus new four-case40/0 bounded completion; genericfullcompletion false. Initial14075/3 and587/1 reviewers assumed absent annotation/mobile route/API spelling;569/0 corrects those exact premises. No source/assertion/product patch or browser rerun.'),
    ('manager', 'manager-availability-f3-public-v3', '151c1fd14b5d1e85566871911c5f4e9e348d6b75a94a055577feea7e80935de0', True, 'Currentqueue unknown. reconcile/list-ready/list-alerts NOT_EXECUTED; CLI only--help0. No private original returned or empty DB created;v1 author tool-only failure stays distinguished from v2 actual sealed builder0.'),
]
packet_records = []
for scope, directory, identity, accepted, rationale in packets:
    manifest = Path('<workspace-path>') / directory / 'manifest.json'
    ref = binding(manifest)
    assert ref['sha256'] == identity
    packet_records.append({'scope': scope, 'packetName': directory, 'manifest': ref, 'independentPacketMetadataAccepted': accepted, 'releaseApproved': False, 'rationale': rationale})

exe = Path('/proc/self/exe').resolve()
index = {'schema': 'geometry-immutable-independent-publication-actor-index/1', 'actor': '/root/publication_final_review', 'sealedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actualIndexCommand': [sys.executable, '-B', str(Path(__file__)), str(OUT)], 'indexSourceSHA256': binding(__file__)['sha256'], 'actualIndexPID': os.getpid(), 'actualPython': str(exe), 'actualPythonSHA256': binding(exe)['sha256'], 'indexDecisionExitCode': 0, 'productFullSHA': 'f3b8285729b42cd22451c98cba1e2ec4514517f3', 'reviews': records, 'packets': packet_records, 'limits': ['This index seals existing reviewers and does not perform new product acceptance or repeat any browser/native/service test.', 'Every failed reviewer result stays intact. Corrected reviewer assumptions and true metadata package-role repair have separate scope and source identity.', 'No review counts are summed into product tests, fullCDP, Space, all43, privateZIP or Windows acceptance.', 'Product/source/actor/command/native/exits remain bound to original scope receipts; no missing original exit is filled by reviewer or packaging0.', 'Only fresh scratch index files are written; no original packet, repo, GitHub, service, DB or private queue is changed.'], 'releaseApproved': False}
path = OUT / 'actor-index.json'
path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'index': str(path), 'indexSHA256': binding(path)['sha256'], 'reviewRecords': len(records), 'packetRecords': len(packet_records), 'indexDecisionExitCode': 0}, ensure_ascii=False))
