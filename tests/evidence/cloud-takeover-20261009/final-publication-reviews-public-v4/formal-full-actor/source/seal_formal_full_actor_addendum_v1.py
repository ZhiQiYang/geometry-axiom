"""Seal existing actual FULL/publication reviewers, preserving red and unknown.
Scratch-only metadata indexing. No reviewer/product/browser/service rerun.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

B = Path('<workspace-path>')
S = Path('<workspace-path>')
D = S / 'geometry-delivery-closeout-20261009'
OUT = Path(sys.argv[1])
HEAD = 'f3b8285729b42cd22451c98cba1e2ec4514517f3'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
def identity(path):
    p = Path(path); raw = p.read_bytes()
    return {'path': str(p), 'sha256': sha(raw), 'bytes': len(raw)}
def load(path): return json.loads(Path(path).read_text())
previous = identity(B / 'actor-index-v1/actor-index.json')
assert previous['sha256'] == '304f7db805963db8a5b03b1603d4bd1cb52c75f05abc64493c0a67e3bb878eef'
reviews = []
for name, source, report, raw, outer in [
    ('formal-full-v3-primary', B/'review_formal_full_packet_v3.py', B/'formal-full-v3-review/report.json', B/'formal-full-v3-review.raw.log', B/'formal-full-v3-review.execution.json'),
    ('formal-full-v3-source-actor-initial', S/'geometry-formal-full-v3-source-actor-closure-review.py', S/'geometry-formal-full-v3-source-actor-closure-review/report.json', S/'geometry-formal-full-v3-source-actor-closure-review/command.raw.log', None),
    ('formal-full-v3-golden-envelope-supplement', S/'geometry-formal-full-v3-golden-envelope-supplement.py', S/'geometry-formal-full-v3-golden-envelope-supplement/report.json', S/'geometry-formal-full-v3-golden-envelope-supplement/command.raw.log', None),
    ('publication-history-v3-primary', B/'review_publication_history_v3.py', B/'publication-history-v3-review/report.json', B/'publication-history-v3-review.raw.log', B/'publication-history-v3-review.execution.json')]:
    j = load(report); source_ref = identity(source); report_ref = identity(report); raw_ref = identity(raw)
    assert source_ref['sha256'] == j.get('reviewerSourceSHA256', j.get('reviewSourceSHA256'))
    command = j.get('actualCommand', j.get('command'))
    assert command and str(source) in command
    code = j.get('computedReviewerExitCode', j.get('actualExitCode'))
    entry = {'name': name, 'actor': j['actor'], 'executedReviewerSource': source_ref, 'report': report_ref, 'rawLog': raw_ref, 'actualCommand': command, 'actualReviewExitCode': code, 'passedMetadataChecks': j['passedMetadataChecks'], 'failedMetadataChecks': j['failedMetadataChecks'], 'countsAreProductAssertions': False, 'actualPython': j['actualPython'], 'actualPythonSHA256': j['actualPythonSHA256'], 'originalFindingsPreserved': j.get('findings', []), 'originalPID': j.get('actualPID', 'unknown-not-originally-captured'), 'originalCmdlineHex': j.get('actualCmdlineHex', 'unknown-not-originally-captured')}
    if outer:
        o = load(outer)
        assert o['actualExitCode'] == code and o['originalSourceSHA256'] == source_ref['sha256'] and o['rawSHA256'] == raw_ref['sha256']
        entry['outerSubprocessExecutionReceipt'] = identity(outer)
        entry['exitProvenance'] = 'Original independent outer subprocess.returncode, report and raw identity agreement.'
    else:
        assert j['rawLog']['sha256'] == raw_ref['sha256']
        entry['exitProvenance'] = 'Original child executed tool return and independently sealed report/raw; no separate original outer PID/executable/exit receipt invented.'
    if name.endswith('initial'):
        dep = S / 'geometry-assembly-packet-review-v4-independent.py'
        entry['readonlyParserDependency'] = identity(dep)
        assert entry['readonlyParserDependency']['sha256'] == j['parserHelperSourceSHA256']
    if name.endswith('supplement'):
        entry['correctedReviewerAssumption'] = j['correctedReviewerAssumption']
        entry['originalFailedReviewRetained'] = j['originalFailedReviewRetained']
    reviews.append(entry)
assert [(r['passedMetadataChecks'],r['failedMetadataChecks'],r['actualReviewExitCode']) for r in reviews] == [(7360,0,0),(330,1,1),(10,0,0),(643,0,0)]
packets = []
for name, manifest, expected in [
    ('formal-full-v3', D/'f3b-durable-full-public-v3/manifest.json', 'f33d0032d3bfd33cec02f9790a90104892e8a4bbd8803b8349105544571c7b93'),
    ('publication-history-v3', D/'final-publication-reviews-public-v3/manifest.json', '0b448d857d76a02b0a7a464b4ec1574c34c85d8fc3311a834b4a4672b704c28c')]:
    pin=identity(manifest);assert pin['sha256']==expected
    packets.append({'name':name,'manifest':pin,'actualPrimaryReadOnlyReviewExitCode':0,'productTestsExecutedByReview':False})
OUT.mkdir(parents=True, exist_ok=False)
index = {'schema':'geometry-formal-full-final-readonly-actor-index-addendum/1', 'actor':'/root/publication_final_review', 'sealedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actualIndexCommand':[sys.executable,'-B',str(Path(__file__).resolve()),str(OUT)], 'indexSourceSHA256':sha(Path(__file__).read_bytes()), 'actualIndexPID':os.getpid(), 'actualPython':os.readlink('/proc/self/exe'), 'actualPythonSHA256':sha(Path('/proc/self/exe').read_bytes()), 'indexDecisionExitCode':0, 'productFullSHAForContext':HEAD, 'priorActorIndexRetained':previous, 'reviews':reviews, 'packets':packets, 'publicationRoleClarification':{'packet':'publication-history-v3','exactOriginalPhrase':'v2 wrapper reads original v1 recipe, narrows scalar index and appends source43 immutable role index; complete reports/raw are unchanged separately.', 'observedLimit':'This describes retired v2 generation history. Actual current v3 source is direct materialized21b76, and does not execute v1/v2. Top-level placement is ambiguous; producer confirmed freshv4 will clarify actual and historical roles. v3 original text remains unchanged.', 'requiresProductRetest':False}, 'formalFullFinalizerEvidenceLimit':{'actualSourceSHA256':'c138e53bd79fc289f7f421ff6e4f973dd3702d3f461082f7043d0886227181a8','originalAuthorToolChunk':'a4cf04','originalAuthorToolReportedExitCode':0,'originalStandaloneSubprocessReceipt':'unknown-not-originally-captured','originalProcessPID':'unknown-not-originally-captured','originalProcessProcExe':'unknown-not-originally-captured','limit':'Original author tool return is distinct from an original independently captured process receipt; source/current process never used to backfill.'},'limits':['No original reviewer or product/browser/service/native/GH/API rerun while sealing this index.','These reviewer metadata counts never product2207/150/228/40 assertions.','Original330/1 reader golden-envelope mistake stays retained; separate10/0 source-bound supplement resolves the exact predicate.','Previous304f actor-index-v1 and all historical reports/source/raw remain unchanged.','Original old unreceipted full actualactor/exits remain unknown; fresh formal result never retrofits old receipt.','Original launch null/pending remains; new dated originalsamePID/starttimekernel0 is distinct.'], 'releaseApproved':False}
(OUT/'actor-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
assert identity(previous['path']) == previous
for review in reviews:
    for key in ['executedReviewerSource','report','rawLog','readonlyParserDependency','outerSubprocessExecutionReceipt']:
        if key in review: assert identity(review[key]['path']) == review[key]
print(json.dumps({'actualIndexExitCode':0,'actorIndexPath':str(OUT/'actor-index.json'),'actorIndexSHA256':sha((OUT/'actor-index.json').read_bytes()),'reviewRecords':len(reviews),'packets':len(packets),'productExecuted':False}))
