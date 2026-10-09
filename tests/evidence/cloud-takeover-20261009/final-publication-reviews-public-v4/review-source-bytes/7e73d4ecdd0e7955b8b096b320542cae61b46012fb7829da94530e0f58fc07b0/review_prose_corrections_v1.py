"""Independent inverse byte review; no producer is imported or executed."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

B = Path('<workspace-path>')
P = B / 'public-prose-corrections-public-v1'
PRIVATE = B / 'public-prose-corrections-build-v1'
ROOT = Path('<workspace-path>')
PUBLIC_BASE = ROOT / 'tests/evidence/cloud-takeover-20261009'
OUT = Path(sys.argv[1])
MANIFEST = 'c0a5c3287614b4f4720958ca6179634a22ebd64d7a3de43748ee699d80e48043'
checks = []
findings = []
protected = {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    path = Path(path)
    raw = path.read_bytes()
    protected[str(path)] = (len(raw), sha(raw))
    return raw


def pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError('duplicate JSON key: ' + key)
        value[key] = item
    return value


def load(raw):
    return json.loads(raw, object_pairs_hook=pairs)


def check(condition, name, detail=None):
    checks.append({'name': name, 'passed': bool(condition)})
    if not condition:
        findings.append({'name': name, 'detail': detail})


ALPHABET = r'[A-Za-z0-9._~%+@:=/\-]+'
TOKEN = re.compile(r'(?:/workspace/|/tmp/geometry-|/opt/codex/|/tmp/playwright_chromiumdev_profile-)' + ALPHABET)


def concrete_tokens(text):
    return list(TOKEN.finditer(text))


def json_location(value, path):
    assert path.startswith('$')
    for match in re.finditer(r'\.([^\.\[]+)|\[(\d+)\]', path[1:]):
        value = value[match.group(1)] if match.group(1) is not None else value[int(match.group(2))]
    return value


started = datetime.datetime.now(datetime.timezone.utc).isoformat()
OUT.mkdir(parents=True, exist_ok=False)
manifest_raw = read(P / 'manifest.json')
manifest = load(manifest_raw)
check(sha(manifest_raw) == MANIFEST, 'exact final-ready correction manifest identity')
files = manifest['publicFiles']
names = [item['path'] for item in files]
check(len(set(names)) == len(names) == 25, 'exact unique25 public file list')
actual = {item.relative_to(P).as_posix() for item in P.rglob('*') if item.is_file()}
check(actual == set(names) | {'manifest.json'}, 'exact26 file census')
check(not any(item.is_symlink() for item in P.rglob('*')), 'no correction evidence symlinks')
for item in files:
    name = item['path']
    raw = read(P / name)
    check(not Path(name).is_absolute() and '..' not in Path(name).parts, 'safe correction path ' + name)
    check(len(raw) == item['bytes'] and sha(raw) == item['sha256'], 'correction public bytes/hash ' + name)
    if Path(name).suffix == '.json':
        load(raw)
    elif Path(name).suffix == '.py':
        ast.parse(raw.decode(), filename=name)

receipt = load(read(PRIVATE / 'execution-receipt.private.json'))
runtime = load(read(PRIVATE / 'actual-builder-runtime.private.json'))
check(sha(read(PRIVATE / 'execution-receipt.private.json')) == 'f9a76e96480a76b2c7329fbafcd4b088a9351fe968ad4b1c7e5d5cf38d23604f', 'exact separately retained real builder receipt')
check(sha(read(PRIVATE / 'actual-builder-runtime.private.json')) == receipt['actualBuilderRuntimeSHA256'], 'actual builder runtime closure hash')
actual_builder = read(PRIVATE / 'build_corrections.py')
check(sha(actual_builder) == manifest['actualExecutedBuilderSHA256'] == receipt['actualSourceBeforeSHA256'] == receipt['actualSourceAfterSHA256'] == runtime['actualBuilderBefore']['sha256'] == runtime['actualBuilderAfter']['sha256'], 'actual builder source unchanged with one full original identity')
check(receipt['actualExitCode'] == 0 and receipt['actualSourceUnchanged'] is True, 'real builder actual0 separate from producer checks')
check(receipt['actualPython'] == runtime['actualPython'] and receipt['actualPython']['procCmdline'] == receipt['command'], 'actual builder interpreter/proc/command same execution')
check(receipt['actualPython']['pid'] == 287105 and receipt['actualPython']['ppid'] == 287102 and receipt['cwd'] == '/workspace', 'saved builder PID/parent/cwd retained')
check(receipt['actualPython']['sha256'] == 'fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7', 'saved actual Python hash not configured browser identity')
check(sha(read(PRIVATE / 'run_builder.py')) == receipt['runnerSourceSHA256'], 'actual producer runner source hash')
for item in receipt['rawLogs']:
    raw = read(item['path'])
    check(len(raw) == item['bytes'] and sha(raw) == item['sha256'], 'producer actual raw stream binding ' + item['stream'])
check(receipt['publicManifest']['sha256'] == sha(manifest_raw) and receipt['publicManifest']['bytes'] == len(manifest_raw), 'actual executed builder receipt binds this exact public manifest')
check(receipt['producerSelfChecksOnly'] is True and receipt['independentReview'] is False and receipt['productTestsExecuted'] is False and receipt['browserOrNativeExecuted'] is False and receipt['repositoryOrGitMutations'] is False and receipt['apiOrCiReads'] is False, 'producer checks self-only no product/Git/browser/API claim')

sources = manifest['sourceCorrections']
check(len(sources) == len({item['originalSHA256'] for item in sources}) == 16, 'exact16 original source identities')
check(sum(Path(item['originalBasename']).suffix == '.md' for item in sources) == 7 and sum(Path(item['originalBasename']).suffix == '.py' for item in sources) == 9, 'exact7 Markdown and9 Python original identities')
source_map = {item['originalSHA256']: item for item in sources}
token_total = 0
for item in sources:
    identity = item['originalSHA256']
    extension = Path(item['originalBasename']).suffix
    original = read(PRIVATE / 'original-source-bytes' / (identity + extension))
    corrected = read(P / item['correctedPublicPath'])
    check(sha(original) == identity and len(original) == item['originalBytes'], 'exact retained original source ' + identity)
    check(sha(corrected) == item['correctedPublicSHA256'] and len(corrected) == item['correctedPublicBytes'], 'corrected source byte identity ' + identity)
    for binding in runtime['privateOriginalSources'][identity]:
        raw = read(binding['path'])
        check(sha(raw) == identity and len(raw) == binding['bytes'], 'authoritative older saved original binding ' + identity + '/' + Path(binding['path']).name)
    text = original.decode()
    matches = concrete_tokens(text)
    token_total += len(matches)
    check(len(matches) == item['explicitTokenCount'] == len(item['tokenSpans']), 'exact independent concrete path token census ' + identity)
    segments = item['unchangedSegments']
    check(len(segments) == len(matches) + 1, 'exact complete unchanged segment census ' + identity)
    original_cursor = public_cursor = 0
    reconstructed = []
    for i, match in enumerate(matches):
        span = item['tokenSpans'][i]
        segment = segments[i]
        original_start = len(text[:match.start()].encode())
        original_end = len(text[:match.end()].encode())
        raw_token = original[original_start:original_end]
        replacement = '<workspace-path>' if match.group().startswith('/workspace/') else '<execution-runtime-path>' if match.group().startswith('/opt/') else '<isolated-test-directory>'
        replacement_bytes = replacement.encode()
        unchanged = original[original_cursor:original_start]
        check(segment['originalStartByte'] == original_cursor and segment['originalEndByte'] == original_start and segment['publicStartByte'] == public_cursor and segment['publicEndByte'] == public_cursor + len(unchanged), 'independent complete unchanged segment ranges ' + identity + '/' + str(i))
        check(unchanged == corrected[segment['publicStartByte']:segment['publicEndByte']] and len(unchanged) == segment['bytes'] and sha(unchanged) == segment['sha256'], 'every non-token original byte unchanged ' + identity + '/' + str(i))
        public_cursor += len(unchanged)
        check(span['originalStartByte'] == original_start and span['originalEndByte'] == original_end and span['originalStartCharacter'] == match.start() and span['originalEndCharacter'] == match.end(), 'independent original token byte/character ranges ' + identity + '/' + str(i))
        check(span['originalTokenBytes'] == len(raw_token) and span['originalTokenSha256'] == sha(raw_token) and span['replacement'] == replacement, 'explicit concrete original token and replacement identity ' + identity + '/' + str(i))
        check(span['publicStartByte'] == public_cursor and span['publicEndByte'] == public_cursor + len(replacement_bytes) and corrected[public_cursor:public_cursor + len(replacement_bytes)] == replacement_bytes, 'independent public token ranges ' + identity + '/' + str(i))
        reconstructed.extend([unchanged, replacement_bytes])
        original_cursor = original_end
        public_cursor += len(replacement_bytes)
    last = segments[-1]
    tail = original[original_cursor:]
    check(last['originalStartByte'] == original_cursor and last['originalEndByte'] == len(original) and last['publicStartByte'] == public_cursor and last['publicEndByte'] == len(corrected), 'final segment exact full source coverage ' + identity)
    check(tail == corrected[public_cursor:] and len(tail) == last['bytes'] and sha(tail) == last['sha256'], 'every trailing non-token byte unchanged ' + identity)
    reconstructed.append(tail)
    check(b''.join(reconstructed) == corrected, 'independent full inverse byte reconstruction ' + identity)
    check(item['allNonTokenBytesRetained'] is True and item['correctedPublicWasExecuted'] is False, 'corrected source is projection only not execution ' + identity)
    if extension == '.py':
        ast.parse(original.decode(), filename=identity)
        ast.parse(corrected.decode(), filename=item['correctedPublicPath'])
    for prefix in manifest['projectionPolicy']['machineRootDetectorPrefixes']:
        prefix_only = re.compile(re.escape(prefix) + r'(?=[\x22\x27\[\]])')
        check(len(prefix_only.findall(text)) == len(prefix_only.findall(corrected.decode())), 'generic detector prefix code literals unchanged ' + identity + '/' + prefix)

refs = manifest['affectedReferences']
check(len(refs) == len({(item['packet'], item['relativePath']) for item in refs}) == 36, 'exact36 affected old public path references')
check(len([item for item in refs if item['originalPublicationSHA'] is not None]) == 29 and len([item for item in refs if item['originalPublicationSHA'] is None]) == 7, '29 previously published and7 READY reference separation')
for item in refs:
    source = source_map[item['originalSHA256']]
    base = PUBLIC_BASE / item['packet'] if item['originalPublicationSHA'] is not None else B / item['packet']
    old_manifest_raw = read(base / 'manifest.json')
    old_manifest = load(old_manifest_raw)
    old = read(base / item['relativePath'])
    check(sha(old_manifest_raw) == item['originalManifestSHA256'], 'old affected manifest unchanged ' + item['packet'])
    check(sha(old) == item['priorPublicSHA256'] and len(old) == item['priorPublicBytes'], 'old affected public bytes unchanged ' + item['packet'] + '/' + item['relativePath'])
    check(source['correctedPublicPath'] == item['correctedPublicPath'] and source['correctedPublicSHA256'] == item['correctedPublicSHA256'] and source['correctedPublicBytes'] == item['correctedPublicBytes'], 'exact one original to corrected identity binding ' + item['relativePath'])
    check(item['correctedPublicWasExecuted'] is False and item['allConfirmedSuffixesASCII'] is True and all(suffix.isascii() for suffix in item['confirmedRemovedSuffixes']), 'prior text findings ASCII and no corrected execution claim ' + item['relativePath'])
    for location in item['manifestReferenceLocations']:
        oldref = json_location(old_manifest, location)
        check(oldref['originalSha256'] == item['originalSHA256'] and oldref['sha256'] == item['priorPublicSHA256'] and oldref['path'] == item['relativePath'], 'original manifest exact reference location ' + item['packet'] + location)
    if item['originalPublicationSHA'] is not None:
        command = ['git', '-C', str(ROOT), 'show', item['originalPublicationSHA'] + ':tests/evidence/cloud-takeover-20261009/' + item['packet'] + '/' + item['relativePath']]
        actual = subprocess.run(command, capture_output=True)
        check(actual.returncode == 0 and actual.stdout == old, 'exact previously published Git blob unchanged ' + item['relativePath'])
    else:
        check(item['publicationStatus'] == 'not_yet_published_READY_original_manifest', 'READY not asserted published ' + item['relativePath'])
    if item['sourceHead'] and item['repositoryPath']:
        actual = subprocess.run(['git', '-C', str(ROOT), 'show', item['sourceHead'] + ':' + item['repositoryPath']], capture_output=True)
        check(actual.returncode == 0 and sha(actual.stdout) == item['originalSHA256'], 'original committed reference exact head retained ' + item['relativePath'])

for key in ['sevenPublishedImmutableManifests', 'fiveOriginalReadyManifests']:
    check(len(manifest[key]) == (7 if key.startswith('seven') else 5), 'exact prior manifest census ' + key)
    for item in manifest[key]:
        base = PUBLIC_BASE / item['packet'] if key.startswith('seven') else B / item['packet']
        raw = read(base / 'manifest.json')
        check(sha(raw) == item['manifestSHA256'], 'all prior published/READY manifests unchanged ' + item['packet'])
for item in runtime['inputs']:
    raw = read(item['snapshotPath'])
    check(len(raw) == item['bytes'] and sha(raw) == item['sha256'], 'actual builder saved original input identity ' + Path(item['snapshotPath']).name)
for item in runtime['oldManifestsBeforeAfter'] + runtime['oldPublicFilesBeforeAfter']:
    raw = read(item['path'])
    check(len(raw) == item['bytes'] and sha(raw) == item['sha256'], 'actual builder preserved old input closure ' + Path(item['path']).name)

summary = manifest['summary']
check(token_total == summary['concretePathTokenReplacements'] == 194, 'exact independent194 concrete path replacements')
check(sum(item['originalSHA256'] == 'a211fd0d066b8a5138855c4773373f9f526717f26264de909c0f61f997ac9aba' for item in refs) == 21, '21 old binaries paths share one corrected original identity')
check(manifest['releaseApproved'] is False and summary['productTestsExecuted'] is False and summary['source43Included'] is False and manifest['projectionPolicy']['publicCopiesWereExecuted'] is False, 'no release/product/source43/executed copy claims')
for name, binding in list(protected.items()):
    current = Path(name).read_bytes()
    check((len(current), sha(current)) == binding, 'evidence unchanged after independent review ' + name)

exit_code = 0 if not findings else 1
actual_exe = Path('/proc/self/exe').resolve()
report = {
    'schema': 'geometry-independent-bounded-prose-correction-review/1',
    'reviewerActor': '/root/publication_final_review',
    'startedUtc': started,
    'finishedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'manifestSHA256': sha(manifest_raw),
    'reviewCommand': [sys.executable, '-B', str(Path(__file__)), str(OUT)],
    'reviewSourceSHA256': sha(Path(__file__).read_bytes()),
    'actualReviewerPID': os.getpid(),
    'actualPython': str(actual_exe),
    'actualPythonSHA256': sha(actual_exe.read_bytes()),
    'actualProcessCmdline': [item.decode() for item in Path('/proc/self/cmdline').read_bytes().split(b'\0')[:-1]],
    'reviewDecisionExitCode': exit_code,
    'metadataChecksPassed': sum(item['passed'] for item in checks),
    'metadataChecksFailed': len(findings),
    'checksAreProductAssertions': False,
    'findings': findings,
    'checks': checks,
    'protectedInputBindings': [{'path': name, 'bytes': value[0], 'sha256': value[1]} for name, value in protected.items()],
    'scope': 'Only correction16 original sources/36 old refs, concrete194 tokens and every inverse non-token byte. Old packet projections remain historically lossy and unchanged; this addendum does not assert their non-token bytes were unchanged.',
    'browserExecuted': False,
    'serviceStartedOrStopped': False,
    'productOrRepositoryWritten': False,
    'githubOrNetworkUsed': False,
}
output = OUT / 'report.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'report': str(output), 'reportSHA256': sha(output.read_bytes()), 'manifestSHA256': sha(manifest_raw), 'metadataChecksPassed': report['metadataChecksPassed'], 'metadataChecksFailed': len(findings), 'reviewDecisionExitCode': exit_code, 'findings': findings}, ensure_ascii=False))
sys.exit(exit_code)
