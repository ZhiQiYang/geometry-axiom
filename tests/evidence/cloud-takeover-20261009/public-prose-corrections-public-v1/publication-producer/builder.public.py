"""Append a fresh scratch evidence correction; originals and old packets stay read-only."""
from pathlib import Path
import ast
import collections
import datetime
import hashlib
import json
import os
import re
import shutil
import sys

sys.dont_write_bytecode = True
BUILD = Path(__file__).resolve().parent
BASE = BUILD.parent
OUT = BASE / 'public-prose-corrections-public-v1'
AUDIT = Path('<workspace-path>')
FOUR = Path('<workspace-path>')
EVIDENCE = Path('<workspace-path>')
PREFIXES = (b'/workspace/', b'/tmp/geometry-', b'/opt/codex/', b'/tmp/playwright_chromiumdev_profile-')
# A concrete token needs at least one ASCII suffix character after a detector root.
# Prefix-only literals before regex syntax/quotes are original code, and stay intact.
TOKEN = re.compile(rb'(?:/workspace/|/tmp/geometry-|/opt/codex/|/tmp/playwright_chromiumdev_profile-)[A-Za-z0-9._~%+@:=/\-]+')
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
sha = lambda data: hashlib.sha256(data).hexdigest()

def info(path):
    data = Path(path).read_bytes()
    return {'bytes': len(data), 'sha256': sha(data)}

def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result

def loads(data):
    return json.loads(data, object_pairs_hook=pairs, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

def label(token):
    return b'<workspace-path>' if token.startswith(b'/workspace/') else b'<execution-runtime-path>' if token.startswith(b'/opt/codex/') else b'<isolated-browser-profile>' if token.startswith(b'/tmp/playwright_') else b'<isolated-test-directory>'

def bounded(raw):
    raw.decode('utf-8')
    pieces, spans, unchanged = [], [], []
    original_at = public_at = 0
    for match in TOKEN.finditer(raw):
        keep = raw[original_at:match.start()]
        pieces.append(keep)
        unchanged.append({'originalStartByte': original_at, 'originalEndByte': match.start(), 'publicStartByte': public_at, 'publicEndByte': public_at + len(keep), 'bytes': len(keep), 'sha256': sha(keep)})
        public_at += len(keep)
        replacement = label(match.group())
        spans.append({'originalStartByte': match.start(), 'originalEndByte': match.end(), 'originalStartCharacter': len(raw[:match.start()].decode()), 'originalEndCharacter': len(raw[:match.end()].decode()), 'originalTokenBytes': len(match.group()), 'originalTokenSha256': sha(match.group()), 'replacement': replacement.decode(), 'publicStartByte': public_at, 'publicEndByte': public_at + len(replacement), 'publicStartCharacter': len(b''.join(pieces).decode()), 'publicEndCharacter': len(b''.join(pieces).decode()) + len(replacement)})
        pieces.append(replacement)
        public_at += len(replacement)
        original_at = match.end()
    keep = raw[original_at:]
    unchanged.append({'originalStartByte': original_at, 'originalEndByte': len(raw), 'publicStartByte': public_at, 'publicEndByte': public_at + len(keep), 'bytes': len(keep), 'sha256': sha(keep)})
    pieces.append(keep)
    public = b''.join(pieces)
    for segment in unchanged:
        original_segment = raw[segment['originalStartByte']:segment['originalEndByte']]
        public_segment = public[segment['publicStartByte']:segment['publicEndByte']]
        assert original_segment == public_segment
        assert sha(public_segment) == segment['sha256']
    assert not TOKEN.search(public), 'Concrete machine path remains'
    return public, spans, unchanged

assert not OUT.exists(), 'Fresh public packet required'
OUT.mkdir()
(BUILD / 'input-snapshots').mkdir()
(BUILD / 'original-source-bytes').mkdir()
input_paths = [AUDIT / 'published/private-report.json', AUDIT / 'published/public-selected-report.json', AUDIT / 'published/public-selected-report.md', AUDIT / 'published/execution-receipt.json', AUDIT / 'published/command.stdout.log', AUDIT / 'published/command.stderr.log', AUDIT / 'ready-subagent/ready5-closed-report.private.json', AUDIT / 'ready-subagent/ready5-closed-report.selected-public.json', AUDIT / 'ready-subagent/ready5-closed-report.selected-public.md', FOUR, BASE / 'prepare_ui_history_packet_v8.py']
inputs = []
for index, path in enumerate(input_paths):
    raw = path.read_bytes()
    snap = BUILD / 'input-snapshots' / (str(index).zfill(2) + '-' + path.name)
    snap.write_bytes(raw)
    inputs.append({'path': str(path), 'snapshotPath': str(snap), **info(path)})
assert info(FOUR)['sha256'] == 'c9328250041975c3373ccc75344e28b09a8d93bf89886eb978385df9789a18c6'
published = loads(input_paths[0].read_bytes())
selected = loads(input_paths[1].read_bytes())
ready = loads(input_paths[6].read_bytes())
four = loads(FOUR.read_bytes())
assert published['summary']['unknown'] == 0
assert published['summary']['allPublishedAndManifestHashesVerified'] is True
assert ready['summary']['unresolvedCount'] == 0
confirmed = [row for row in published['files'] if row['status'] == 'CONFIRMED_NON_TOKEN_LOSS']
assert len(confirmed) == 29 and len(selected['findings']) == 29
assert len(ready['findings']) == 7
packmaps = {p['pack']: p for p in published['packs']}
readymaps = {p['name']: p for p in ready['packets']}
old_manifests = []
for packet, data in packmaps.items():
    path = EVIDENCE / packet / 'manifest.json'
    assert info(path)['sha256'] == data['manifestSha256'] == data['immutableManifestSha256']
    old_manifests.append({'path': str(path), 'packet': packet, **info(path)})
for packet, data in readymaps.items():
    path = Path(data['root']) / 'manifest.json'
    assert info(path)['sha256'] == data['manifestSha256']
    old_manifests.append({'path': str(path), 'packet': packet, **info(path)})

references = []
private_sources = collections.defaultdict(list)
public_old_files = []
for row in confirmed:
    packet = row['pack']
    public_path = Path(row['publicActualPath'])
    actual = info(public_path)
    assert actual['sha256'] == row['actualPublicSha256'] == row['manifestPublicSha256'] == row['immutablePublishedSha256']
    snapshot = Path(row['auditOriginalSnapshot'])
    raw = snapshot.read_bytes()
    assert sha(raw) == row['manifestOriginalSha256'] == row['originalActualSha256'] and len(raw) == row['manifestOriginalBytes']
    private_sources[sha(raw)].append({'path': str(snapshot), 'resolvedOriginalPath': row['resolvedOriginalPath'], 'bytes': len(raw)})
    public_old_files.append({'path': str(public_path), **actual})
    references.append({'packet': packet, 'relativePath': row['publicRelativePath'], 'publicationStatus': 'previously_published_immutable', 'originalPublicationSHA': row['immutablePublishedCommit'], 'originalManifestSHA256': packmaps[packet]['manifestSha256'], 'manifestReferenceLocations': row['manifestLocations'], 'originalSHA256': sha(raw), 'originalBytes': len(raw), 'priorPublicSHA256': actual['sha256'], 'priorPublicBytes': actual['bytes'], 'sourceHead': row['sourceHead'], 'repositoryPath': row['repositoryPath'], 'confirmedFindingLines': sorted({span['line'] for span in row['overlongPrivatePathSpans']}), 'confirmedRemovedSuffixes': sorted({span['nonTokenSuffixRemoved'] for span in row['overlongPrivatePathSpans']}), 'findingSource': 'published-saved-audit', 'allConfirmedSuffixesASCII': all(not span['suffixContainsNonAscii'] for span in row['overlongPrivatePathSpans'])})

for row in ready['findings']:
    data = readymaps[row['packet']]
    public_path = Path(row['publicFile'])
    original_path = Path(row['originalFile'])
    original = original_path.read_bytes()
    assert sha(original) == row['originalSha256']
    actual = info(public_path)
    assert actual['sha256'] == row['publicSha256']
    private_sources[sha(original)].append({'path': str(original_path), 'resolvedOriginalPath': str(original_path), 'bytes': len(original)})
    public_old_files.append({'path': str(public_path), **actual})
    references.append({'packet': row['packet'], 'relativePath': public_path.relative_to(data['root']).as_posix(), 'publicationStatus': 'not_yet_published_READY_original_manifest', 'originalPublicationSHA': None, 'originalManifestSHA256': data['manifestSha256'], 'manifestReferenceLocations': [row['manifestReferenceLocation']], 'originalSHA256': sha(original), 'originalBytes': len(original), 'priorPublicSHA256': actual['sha256'], 'priorPublicBytes': actual['bytes'], 'sourceHead': row['declaredSourceHead'], 'repositoryPath': row['repositoryPath'], 'confirmedFindingLines': [row['originalLine']], 'confirmedRemovedSuffixes': sorted({change['expectedContent'] for change in row['changesOutsideBoundedPathLabels']}), 'findingSource': 'ready5-saved-audit', 'allConfirmedSuffixesASCII': True})

assert len(references) == len({(x['packet'], x['relativePath']) for x in references}) == 36
assert len(private_sources) == 16
corrections, originals = [], {}
for original_sha, evidence in sorted(private_sources.items()):
    raw = Path(evidence[0]['path']).read_bytes()
    assert sha(raw) == original_sha
    suffix = Path(evidence[0]['path']).suffix
    affected = [x for x in references if x['originalSHA256'] == original_sha]
    basename = Path(affected[0]['relativePath']).name
    relative = 'corrected-source-bytes/' + original_sha + '/' + basename
    original_snapshot = BUILD / 'original-source-bytes' / (original_sha + suffix)
    original_snapshot.write_bytes(raw)
    originals[original_sha] = raw
    public, spans, unchanged = bounded(raw)
    assert public != raw
    dest = OUT / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(public)
    if suffix == '.py':
        ast.parse(raw.decode('utf-8'))
        ast.parse(public.decode('utf-8'))
    for ref in affected:
        ref.update(correctedPublicPath=relative, correctedPublicSHA256=sha(public), correctedPublicBytes=len(public), correctedPublicWasExecuted=False)
    corrections.append({'originalSHA256': original_sha, 'originalBytes': len(raw), 'originalBasename': basename, 'originalIdentityBasis': 'Hash-verified retained original bytes; original path and full raw snapshot retained in separate scratch build evidence.', 'correctedPublicPath': relative, 'correctedPublicSHA256': sha(public), 'correctedPublicBytes': len(public), 'priorPublicSHA256s': sorted({x['priorPublicSHA256'] for x in affected}), 'affectedReferenceCount': len(affected), 'explicitTokenCount': len(spans), 'tokenSpans': spans, 'unchangedSegments': unchanged, 'allNonTokenBytesRetained': True, 'correctedPublicWasExecuted': False})

for name in ['public-selected-report.json', 'public-selected-report.md']:
    source = AUDIT / 'published' / name
    dest = OUT / 'prior-audit' / ('published-' + name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
for name in ['ready5-closed-report.selected-public.json', 'ready5-closed-report.selected-public.md']:
    shutil.copyfile(AUDIT / 'ready-subagent' / name, OUT / 'prior-audit' / name)
write(OUT / 'prior-audit/four-markdown-scope.public.json', {'originalPrivateFindingsSHA256': info(FOUR)['sha256'], 'originalPrivateFindingsBytes': info(FOUR)['bytes'], 'confirmedFormattingFindings': four['confirmedFormattingFindings'], 'additionalLexicalOrNumericOrChineseLossObserved': four['additionalLexicalOrNumericOrChineseLossObserved'], 'rows': [{'packet': row['packet'], 'relativePath': row['relativePath'], 'originalSHA256': row['original']['sha256'], 'priorPublicSHA256': row['published']['sha256'], 'boundedFinding': row['boundedFinding'], 'lexicalWordsAndNumericTokensPreserved': row['lexicalWordsAndNumericTokensPreserved'], 'ChineseCharacterSequencePreserved': row['ChineseCharacterSequencePreserved']} for row in four['rows']], 'productTestsExecuted': False, 'newFullAccepted': False})
producer_raw = Path(__file__).read_bytes()
producer_public, producer_spans, producer_unchanged = bounded(producer_raw)
(OUT / 'publication-producer').mkdir()
(OUT / 'publication-producer/builder.public.py').write_bytes(producer_public)
write(OUT / 'publication-producer/projection-map.json', {'actualExecutedBuilderSHA256': sha(producer_raw), 'actualExecutedBuilderBytes': len(producer_raw), 'publicBuilderSHA256': sha(producer_public), 'publicBuilderBytes': len(producer_public), 'publicBuilderWasExecuted': False, 'tokenSpans': producer_spans, 'unchangedSegments': producer_unchanged, 'allNonTokenBytesRetained': True})

summary = {'uniqueOriginalFiles': len(corrections), 'uniqueMarkdownOriginals': sum(x['originalBasename'].endswith('.md') for x in corrections), 'uniquePythonOriginals': sum(x['originalBasename'].endswith('.py') for x in corrections), 'affectedPublicPaths': len(references), 'previouslyPublishedPaths': sum(x['publicationStatus'] == 'previously_published_immutable' for x in references), 'notYetPublishedReadyPaths': sum(x['publicationStatus'] == 'not_yet_published_READY_original_manifest' for x in references), 'affectedPublishedPackets': len({x['packet'] for x in references if x['publicationStatus'] == 'previously_published_immutable'}), 'affectedReadyPackets': len({x['packet'] for x in references if x['publicationStatus'] == 'not_yet_published_READY_original_manifest'}), 'originalBinariesCopiesSharingOneCorrectedSource': sum(x['originalSHA256'] == 'a211fd0d066b8a5138855c4773373f9f526717f26264de909c0f61f997ac9aba' for x in references), 'confirmedAuditSpanInstances': 76, 'concretePathTokenReplacements': sum(x['explicitTokenCount'] for x in corrections), 'unknownOriginalSources': 0, 'productTestsExecuted': False, 'browserOrNativeExecuted': False, 'source43Included': False}
readme = '''# Bounded public prose corrections

This append-only evidence packet corrects 36 confirmed text projections using 16 hash-verified originals: seven Markdown files and nine Python files. It covers 29 paths in the seven immutable published packets and seven binaries.py paths in four READY packets. All affected paths map to one corrected source per original SHA256 in manifest.json. Every prior public hash, original manifest hash and full prior publication commit is retained. READY rows have no publication commit and identify their original not-yet-published manifest instead.

Only concrete ASCII machine path tokens are replaced. The token alphabet is [A-Za-z0-9._~%+@:=/\\-]; matching stops before backticks, non-ASCII prose, whitespace, quotes and other characters outside that alphabet. Generic detector-prefix literals such as /workspace/ and /tmp/geometry- immediately followed by quote or regex syntax are original code syntax and remain byte-for-byte. The public source copies are evidence projections and were not executed. Original source SHA256 and corrected public SHA256 are separate identities.

The four separately reviewed Markdown findings concern closing backticks and punctuation. That saved review observed no additional Chinese, lexical-word or numeric-token loss. The additional saved audit confirms three 243 Markdown files, the shared binaries.py closing-backtick loss, and reviewer/preparer regex-template syntax loss; its 76 affected span instances are ASCII. This packet does not reinterpret those documentation findings as product failures or Chinese prose loss.

Every replacement token records its original token hash and original/public positions. Every unchanged segment records its byte ranges and hash, allowing inverse comparison against the exact retained originals. Producer self-checks cover hashes, strict JSON, Python syntax and all non-token byte comparisons; they are not an independent review or release approval.

The seven published packets and manifests, original READY manifests and historical QA findings remain unchanged. The saved audit excerpts are retained under prior-audit. Source43 correction is handled separately and is excluded here. No product/browser/native execution, repository/Git/GitHub mutation, API/CI read, service or publication occurs in this build. Historical execution receipts remain the authority for actual executed sources, commands and results. This packet does not recover missing historical identity or approve full product acceptance.

Actual builder bytes, interpreter/proc/command identity, original byte snapshots and the real exit/raw-log receipt are retained in a separate private scratch build directory. The public builder is explicitly projected and was not executed.
'''
(OUT / 'README.md').write_text(readme)
mapping = {'schema': 'geometry-bounded-public-prose-corrections/1', 'preparedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actor': '/root/delivery_closeout/prose_correction_packet', 'releaseApproved': False, 'summary': summary, 'projectionPolicy': {'concreteTokenAlphabet': '[A-Za-z0-9._~%+@:=/\\-]+', 'machineRootDetectorPrefixes': [x.decode() for x in PREFIXES], 'prefixOnlyDetectorCodeLiteralsPreserved': True, 'allNonTokenBytesRetained': True, 'originalTokenTextPublished': False, 'publicCopiesWereExecuted': False}, 'sourceCorrections': corrections, 'affectedReferences': sorted(references, key=lambda x: (x['packet'], x['relativePath'])), 'priorAuditEvidence': [{'basename': Path(x['path']).name, 'bytes': x['bytes'], 'sha256': x['sha256']} for x in inputs], 'sevenPublishedImmutableManifests': [{'packet': p['pack'], 'originalPublicationSHA': p['immutablePublishedCommit'], 'manifestSHA256': p['manifestSha256']} for p in published['packs']], 'fiveOriginalReadyManifests': [{'packet': p['name'], 'publicationStatus': 'not_yet_published_READY_original_manifest', 'originalPublicationSHA': None, 'manifestSHA256': p['manifestSha256']} for p in ready['packets']], 'actualExecutedBuilderSHA256': sha(producer_raw), 'closureLimits': ['Exact original hash snapshots establish these source byte identities; current same-named files are not substituted for them.', 'Committed source heads are recorded only when present in the original manifest; null remains unknown.', 'Source-copy publication does not attest to actual product execution; original receipts and dated QA findings retain their separate scopes.', 'Source43, archives, structured JSON projection changes and unconfirmed files are outside this correction.', 'No original packet, manifest, product source or historical finding is rewritten.']}

self_checks = {'schema': 'geometry-correction-producer-self-check/1', 'independentReview': False, 'sourceOriginalSHA256Verified': True, 'originalAndPublicIdentitySeparated': True, 'allNonTokenByteSegmentsEqual': True, 'allOldPublicAndManifestBytesVerified': True, 'sevenImmutablePublishedManifestsUnchanged': True, 'fiveOriginalReadyManifestsUnchanged': True, 'strictJsonValidated': True, 'pythonSourceSyntaxValidated': True, 'genericRootPrefixCodeLiteralsPreserved': True, 'concreteMachinePathTokensRemain': False, 'productTestsExecuted': False, 'releaseApproved': False}
for entry in inputs:
    assert info(entry['path']) == {'bytes': entry['bytes'], 'sha256': entry['sha256']}
for entry in old_manifests + public_old_files:
    assert info(entry['path']) == {'bytes': entry['bytes'], 'sha256': entry['sha256']}
for key, evidence in private_sources.items():
    for entry in evidence:
        assert info(entry['path']) == {'bytes': entry['bytes'], 'sha256': key}
write(OUT / 'producer-self-check.json', self_checks)
mapping['publicFiles'] = [{'path': path.relative_to(OUT).as_posix(), **info(path)} for path in sorted(OUT.rglob('*')) if path.is_file()]
write(OUT / 'manifest.json', mapping)
for entry in mapping['publicFiles']:
    path = OUT / entry['path']
    assert info(path) == {'bytes': entry['bytes'], 'sha256': entry['sha256']}
    assert not TOKEN.search(path.read_bytes()), path
    if path.suffix == '.json':
        loads(path.read_bytes())
loads((OUT / 'manifest.json').read_bytes())
actual_exe = Path(os.readlink('/proc/self/exe'))
runtime = {'startedUtc': started, 'completedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actualBuilderPath': str(Path(__file__).resolve()), 'actualBuilderBefore': info(__file__), 'actualBuilderAfter': info(__file__), 'actualPython': {'requestedPath': sys.executable, 'actualProcExe': str(actual_exe), **info(actual_exe), 'version': sys.version, 'pid': os.getpid(), 'ppid': os.getppid(), 'procCmdline': Path('/proc/self/cmdline').read_bytes().decode().rstrip('\0').split('\0'), 'cwd': str(Path.cwd())}, 'inputs': inputs, 'privateOriginalSources': dict(private_sources), 'oldManifestsBeforeAfter': old_manifests, 'oldPublicFilesBeforeAfter': public_old_files, 'allSourcesAndInputsUnchanged': True, 'publicPacketPath': str(OUT), 'publicManifest': info(OUT / 'manifest.json'), 'producerSelfChecks': self_checks, 'repositoryOrGitMutations': False, 'githubOrApiWrites': False, 'apiOrCiReads': False, 'productTestsExecuted': False, 'browserOrNativeExecuted': False}
write(BUILD / 'actual-builder-runtime.private.json', runtime)
print(json.dumps({'packetBasename': OUT.name, 'manifestSHA256': info(OUT / 'manifest.json')['sha256'], 'publicFiles': len(mapping['publicFiles']), 'artifactCountIncludingManifest': len(mapping['publicFiles']) + 1, 'totalBytes': sum(path.stat().st_size for path in OUT.rglob('*') if path.is_file()), 'summary': summary, 'producerSelfChecksOnly': True}, ensure_ascii=False))
