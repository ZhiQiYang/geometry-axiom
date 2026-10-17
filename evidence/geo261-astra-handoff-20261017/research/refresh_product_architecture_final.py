"""Bounded, staged static-architecture refresh; nothing runs on import.

Set a full GEOMETRY_ARCH_AUDIT_HEAD and a fresh GEOMETRY_ARCH_AUDIT_WORK
directly under RESEARCH. Run before, refresh, product_tests, report, seal in
that order. An attempted stage cannot be retried in the same run directory.
Only the four AUDIT outputs may change. This is not native/runtime acceptance.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


ROOT = Path('D:/geometry-axiom-work/geo261-integration')
RESEARCH = Path('D:/geometry-axiom-work/geo261-research')
AUDIT_REL = 'geometry-core/domain-decoupling/'
AUDIT = ROOT / AUDIT_REL
HEAD = None
WORK = None
ROOTS = ['geometry-core', 'geometry-app', 'geometry-templates', 'geometry-web', 'geometry-guide']
STANDALONE = ['current_geometry.c', 'tests/__init__.py', 'tests/binaries.py']
SUFFIXES = {'.c', '.h', '.inc', '.py', '.js', '.mjs', '.cjs', '.html', '.htm', '.ts', '.jsx', '.tsx', '.cc', '.cpp', '.cxx', '.hpp', '.hh'}
STAGES = ('before', 'refresh', 'product_tests', 'report', 'seal')
OUTPUTS = ('product-architecture.json', 'product-architecture-scan.json', 'product-architecture-receipt.json', 'PRODUCT-ARCHITECTURE.md')
OLD_HEAD = '47d3bb4bcccddeeb034dd5899a7aa15c9cab0768'
PYTHON_HEAD = '8f36f1a0dd7e1244c92aca926c0a80079451e7f0'
PORTABILITY_HEAD = '43305271770760a690e360ce18ce11cc07f35ea2'
OLD_CLOSURE = '401670b9f56655b29e367706e6602b70ee3344518c8cc4210ef45f7ef4b32dc2'
OLD_OUTPUT_PINS = {
    'product-architecture.json': '119e153590b9ecf5ea23d4a54fb6845528a302291f819c979a803d79712b3b33',
    'product-architecture-scan.json': '900894fedb455683ed9276157dd7db772b03363afc6c9f5c48a717637eb24bf2',
    'product-architecture-receipt.json': 'a4166fd433cb9477e87756f635b5491d5dfe457035974b10b03d6b33ddc676e7',
    'PRODUCT-ARCHITECTURE.md': 'b43dd0bd2d3d76a9b679d1df3e99c37a5eb1f6a319d4de99702240b11e7211d9',
}
TOOL_PINS = {
    'tests/architecture_contract.py': 'bbd54265d0df88497228e1c362c904a495ed7ea986a3568adbeeb753e19d8f5e',
    'tests/test_architecture_contract.py': '17ffb47f6f18db4967087459bb6d563e4d7487b0e30b23101b38fe5d36a7f9e3',
    'tests/test_product_architecture.py': '12e83386323afbffda89babcaea46eaa337ade1383f85cf63ec17e114238713e',
}
EXPECTED_CHANGED = {
    'geometry-app/geometry_app/model_native.py': 'python',
    'geometry-core/modeling/base.py': 'python',
    'geometry-core/modeling/engine.py': 'python',
    'geometry-app/native/model_sources.inc': 'c',
}
NEW_EXCLUDED = {
    'geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/extract_evidence.py': {
        'reason': 'Historical fourth-package extraction helper: recovers catalog-selected retained evidence bytes without executing them. Not a product-loaded module or current product entry point; final architecture audit reads/hashes this exact file only.',
        'sha256': 'ac626b84cc3cc6d029ecb95cceb2d3098b3a8cf084e8f8b69a3e98bd9d7e90f7',
        'gitBlob': '3ba9a76b6285974af6d274c18cd12f406e7515ce',
    },
    'geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/finalize_publication.py': {
        'reason': 'Historical fourth-package sealing helper: writes the package SHA-256 seal after original-byte verification. Not a product-loaded module or current product entry point; final architecture audit does not invoke it or replace the old package seal.',
        'sha256': '13fe9eb20dd2827859866cf61a83d2badd6236f53eb322b8b79a37dafa865e87',
        'gitBlob': 'dff0d160abbf07e5adfa08c03917df8038587a3b',
    },
    'geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/prepare_publication.py': {
        'reason': 'Historical fourth-package publication helper for the frozen 370-file closed-receipt allowlist. Not a product-loaded module or current product entry point; final architecture audit does not republish or execute retained evidence.',
        'sha256': '37cb07dbc7af6f453c056b7ccec2e777fe3dd991fda531def42112d16aa2a695',
        'gitBlob': 'c42f36885a5472284fcb770e51abde82f5765bc9',
    },
    'geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/readable/watchdog-envelope-v1/recovered-selftest-source-868c0864cbf91da304ca37e7ebee140cfe68542fccc3d6f764f0d27a7f8dd9ac.py': {
        'reason': 'Historical recovered synthetic watchdog self-test source retained by its content hash. It imports a sibling watchdog and creates synthetic run output when executed; it is evidence, not a product module. Final architecture audit reads/hashes it and never imports or runs it.',
        'sha256': '868c0864cbf91da304ca37e7ebee140cfe68542fccc3d6f764f0d27a7f8dd9ac',
        'gitBlob': '828d36e5c3630dccda55404752af212bb9cb4d62',
    },
    'geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/verify_publication.py': {
        'reason': 'Historical fourth-package byte/catalog verification helper. Not a product-loaded module or current product entry point; its original verification and seal remain historical records, and final architecture audit only hashes this exact source.',
        'sha256': '79ff75e1ab60dba1e9c0008fc806b517159f952f677864da461b1dc9eec3406c',
        'gitBlob': 'b30daec04dd243c96a858b756fff6d9753aac4a3',
    },
}
UPDATED_EXCLUDED = {
    'geometry-web/feedback_resize_observer_test.js': {
        'previousSha256': '4598612a3f2aaafab69e061b2f7179530024dab8f99d35c750c783b3336db0d5',
        'currentSha256': '3f183e95fa968e9c81520e292e8d604727a49e2e77626103c0935f14484d434d',
        'reviewReason': 'Still the dedicated ResizeObserver acceptance driver. The reviewed two-line portability change documents and appends whitespace-separated GEOMETRY_CHROME_FLAGS when launching Chrome; assertions, test counts and timeouts are unchanged. This static audit only hashes the committed driver and does not execute its browser flow.',
    },
}
SCAN = ['python', '-B', 'tests/architecture_contract.py', '--root', '.', '--manifest', AUDIT_REL + OUTPUTS[0]]
PRODUCT_TESTS = ['python', '-B', 'tests/test_product_architecture.py']
GENERIC_COMMAND = 'python -B tests/test_architecture_contract.py'
LAYERS = {'H': 190, 'K': 69, 'W': 67, 'vendor': 6}
LANGUAGES = {'c': 189, 'python': 75, 'javascript': 64, 'html': 4}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(raw, mode='lf'):
    require(mode in ('lf', 'raw'), 'Unknown hash mode')
    return hashlib.sha256(raw.replace(b'\r\n', b'\n') if mode == 'lf' else raw).hexdigest()


def hashes(raw):
    return {'rawSha256': digest(raw, 'raw'), 'lfSha256': digest(raw), 'bytes': len(raw)}


def sha(path, mode='lf'):
    return digest(Path(path).read_bytes(), mode)


def load(path):
    return json.loads(Path(path).read_bytes())


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def write_new(path, raw):
    with Path(path).open('xb') as stream:
        stream.write(raw)


def save_new(path, value):
    write_new(path, json_bytes(value))


def closure_hash(inputs):
    return digest(json.dumps(inputs, ensure_ascii=False, separators=(',', ':')).encode('utf-8'), 'raw')


def path_map(inputs):
    result = {row['path']: row['sha256'] for row in inputs}
    require(len(result) == len(inputs), 'Duplicate source path')
    return result


def is_link(path):
    path = Path(path)
    return path.is_symlink() or bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400)


def configure():
    global HEAD, WORK
    require(sys.flags.optimize == 0 and not os.environ.get('PYTHONOPTIMIZE'), 'Run without Python optimization')
    HEAD = os.environ.get('GEOMETRY_ARCH_AUDIT_HEAD', '')
    require(re.fullmatch(r'[0-9a-f]{40}', HEAD) is not None, 'GEOMETRY_ARCH_AUDIT_HEAD must be an explicit full lowercase 40-character Git SHA')
    supplied = os.environ.get('GEOMETRY_ARCH_AUDIT_WORK', '')
    require(bool(supplied), 'GEOMETRY_ARCH_AUDIT_WORK is required')
    candidate = Path(supplied)
    require(candidate.is_absolute(), 'WORK must be absolute')
    require(RESEARCH.is_dir() and not is_link(RESEARCH), 'Research directory is missing or redirected')
    require(candidate.parent.resolve() == RESEARCH.resolve(), 'WORK must be a new direct child of the external research directory')
    require(candidate.name.startswith('manifest-refresh-final-'), 'Use a distinct manifest-refresh-final-* run directory')
    require(not candidate.exists() or not is_link(candidate), 'WORK must not be a symbolic link or junction')
    WORK = candidate.resolve()
    require(ROOT.is_dir() and not is_link(ROOT), 'Integration checkout is missing or redirected')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def head():
    observed = git('rev-parse', 'HEAD').decode('ascii').strip()
    require(observed == HEAD, 'Frozen HEAD changed: ' + observed)
    actual_root = Path(git('rev-parse', '--show-toplevel').decode('utf-8').strip()).resolve()
    require(actual_root == ROOT.resolve(), 'Unexpected repository root')
    return observed


def status_entries():
    entries = {}
    raw = git('status', '--porcelain=v1', '-z', '--untracked-files=all')
    for record in raw.split(b'\0'):
        if not record:
            continue
        require(len(record) > 3 and record[2:3] == b' ', 'Unexpected Git status record')
        code = record[:2].decode('ascii')
        require(code == ' M', 'Staged, untracked, renamed, deleted or conflicted path: ' + repr(record))
        path = record[3:].decode('utf-8')
        require(path not in entries, 'Duplicate Git status path')
        entries[path] = code
    return entries


def raise_walk_error(error):
    raise error


def inventory():
    names = set(STANDALONE)
    for name in ROOTS:
        source_root = ROOT / name
        require(source_root.is_dir() and not is_link(source_root), 'Missing or redirected source root: ' + name)
        for folder, dirs, files in os.walk(source_root, onerror=raise_walk_error):
            for directory in dirs:
                require(not is_link(Path(folder) / directory), 'Redirected source directory: ' + str(Path(folder) / directory))
            for filename in files:
                path = Path(folder) / filename
                if path.suffix.lower() in SUFFIXES:
                    names.add(path.relative_to(ROOT).as_posix())
    lf, raw = [], []
    for name in sorted(names):
        path = ROOT / name
        require(path.is_file() and not is_link(path), 'Missing or redirected executable input: ' + name)
        data = path.read_bytes()
        lf.append({'path': name, 'sha256': digest(data)})
        raw.append({'path': name, 'sha256': digest(data, 'raw')})
    return lf, raw


def tool_hashes():
    result = {}
    for name in TOOL_PINS:
        require(not is_link(ROOT / name), 'Redirected tool: ' + name)
        result[name] = hashes((ROOT / name).read_bytes())
    return result


def output_hashes():
    result = {}
    for name in OUTPUTS:
        require(not is_link(AUDIT / name), 'Redirected audit output: ' + name)
        result[name] = hashes((AUDIT / name).read_bytes())
    return result


def stale(manifest):
    items = []
    for row in manifest['exclusions']:
        if sha(ROOT / row['path'], row.get('hashMode', 'raw')) != row['sha256']:
            items.append(row['path'])
    for row in manifest['sources']:
        if row['layer'] == 'vendor' and sha(ROOT / row['path'], 'raw') != row['sha256']:
            items.append(row['path'])
    for route in manifest['htmlEmbedRoutes']:
        for field in ('driver', 'router'):
            if sha(ROOT / route[field]) != route[field + 'Sha256']:
                items.append(route[field])
    return sorted(set(items))


def committed_provenance(path, expected=None):
    raw = (ROOT / path).read_bytes()
    committed = git('show', HEAD + ':' + path)
    blob = git('rev-parse', HEAD + ':' + path).decode('ascii').strip()
    require(raw.replace(b'\r\n', b'\n') == committed.replace(b'\r\n', b'\n'), 'Working file differs from frozen blob: ' + path)
    if expected is not None:
        require(digest(raw) == expected['sha256'] and blob == expected['gitBlob'], 'Reviewed exclusion bytes/blob changed: ' + path)
    return {'path': path, 'sourceHead': HEAD, 'gitBlob': blob, **hashes(raw),
            'gitBlobRawSha256': digest(committed, 'raw'), 'gitBlobLfSha256': digest(committed)}


def ancestry(ancestor):
    result = subprocess.run(['git', 'merge-base', '--is-ancestor', ancestor, HEAD], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(result.returncode in (0, 1), 'Cannot verify ancestry: ' + result.stderr.decode('utf-8', errors='replace'))
    return {'ancestor': ancestor, 'descendant': HEAD, 'isAncestor': result.returncode == 0,
            'command': 'git merge-base --is-ancestor ' + ancestor + ' ' + HEAD, 'exitCode': result.returncode, 'checkedUtc': utc()}


def expected_exclusions():
    return [{'path': path, 'reason': row['reason'], 'sha256': row['sha256'], 'hashMode': 'lf'} for path, row in NEW_EXCLUDED.items()]


def expected_manifest(previous):
    expected = deepcopy(previous)
    for path, update in UPDATED_EXCLUDED.items():
        entries = [row for row in expected['exclusions'] if row['path'] == path]
        require(len(entries) == 1 and entries[0]['hashMode'] == 'lf' and entries[0]['sha256'] == update['previousSha256'], 'Reviewed existing exclusion basis changed: ' + path)
        entries[0]['sha256'] = update['currentSha256']
    expected['exclusions'] += expected_exclusions()
    return expected


def exclusion_provenance():
    result = [committed_provenance(path, expected) for path, expected in NEW_EXCLUDED.items()]
    for path, update in UPDATED_EXCLUDED.items():
        require(sha(ROOT / path) == update['currentSha256'], 'Reviewed harness portability bytes changed: ' + path)
        result.append(committed_provenance(path))
    return result


def validate_manifest_delta(previous, current):
    expected = expected_manifest(previous)
    require(current == expected, 'Manifest change exceeds five exact additions and the one reviewed exclusion digest update')
    require(len(current['sources']) == 332 and len(current['exclusions']) == 249, 'Unexpected final inventory sizes')
    require(Counter(row['layer'] for row in current['sources']) == LAYERS, 'Layer ownership changed')
    require(Counter(row['language'] for row in current['sources']) == LANGUAGES, 'Language inventory changed')
    require(len(current['policy']['forbiddenIdentifiers']) == 916 and len(current['policy']['forbiddenStrings']) == 55, 'Policy counts changed')


def frozen(state):
    require(head() == state['headBefore'], 'HEAD changed')
    require(state['root'] == str(ROOT.resolve()) and state['work'] == str(WORK), 'State belongs to another checkout or run')
    require(hashes(Path(__file__).read_bytes()) == state['driverHashes'], 'Refresh driver changed during this run')
    lf, raw = inventory()
    require(lf == state['inputsBefore'], 'LF source closure changed')
    require(raw == state['rawInputsBefore'], 'Raw source closure changed')
    require(tool_hashes() == state['toolHashesBefore'], 'Scanner/test bytes changed')
    require(output_hashes() == state['currentOutputHashes'], 'Audit outputs changed outside their completed stage')
    for name in OUTPUTS:
        require(hashes((WORK / 'previous' / name).read_bytes()) == state['previousOutputHashes'][name], 'Preserved previous output changed: ' + name)
    changed = {AUDIT_REL + name for name in OUTPUTS if state['currentOutputHashes'][name] != state['previousOutputHashes'][name]}
    require(set(status_entries()) == changed, 'Git changes do not match only the stage-owned audit outputs')


def write_output(state, name, raw):
    require(name in OUTPUTS, 'Unapproved repository output')
    require(hashes((AUDIT / name).read_bytes()) == state['currentOutputHashes'][name], 'Output changed before write: ' + name)
    (AUDIT / name).write_bytes(raw)
    require((AUDIT / name).read_bytes() == raw, 'Output read-back failed: ' + name)
    state['currentOutputHashes'][name] = hashes(raw)


def run(command, label):
    require(command in (SCAN, PRODUCT_TESTS), 'Unapproved execution command')
    directory = WORK / label
    directory.mkdir()
    execution = [sys.executable, *command[1:]]
    start = {'command': ' '.join(command), 'argv': execution, 'cwd': str(ROOT.resolve()), 'sourceBaseHead': HEAD, 'startedUtc': utc()}
    save_new(directory / 'started.json', start)
    tick = time.monotonic()
    child_env = os.environ.copy()
    child_env['PYTHONDONTWRITEBYTECODE'] = '1'
    try:
        with (directory / 'stdout').open('xb') as stdout_stream, (directory / 'stderr').open('xb') as stderr_stream:
            completed = subprocess.run(execution, cwd=ROOT, env=child_env, stdout=stdout_stream, stderr=stderr_stream)
    except BaseException as error:
        failure = {**start, 'complete': False, 'exitCode': None, 'error': repr(error), 'finishedUtc': utc(), 'seconds': round(time.monotonic() - tick, 3)}
        for stream in ('stdout', 'stderr'):
            path = directory / stream
            if path.is_file():
                failure[stream] = {'path': str(path), **hashes(path.read_bytes())}
        save_new(directory / 'run.json', failure)
        raise
    result = subprocess.CompletedProcess(execution, completed.returncode, (directory / 'stdout').read_bytes(), (directory / 'stderr').read_bytes())
    record = {**start, 'complete': True, 'exitCode': result.returncode, 'finishedUtc': utc(), 'seconds': round(time.monotonic() - tick, 3),
              'stdout': {'path': str(directory / 'stdout'), **hashes(result.stdout)},
              'stderr': {'path': str(directory / 'stderr'), **hashes(result.stderr)}}
    save_new(directory / 'run.json', record)
    return result, record


def read_run(label, command):
    directory = WORK / label
    record = load(directory / 'run.json')
    require(record['complete'] is True, 'Recorded command did not complete')
    require(record['command'] == ' '.join(command) and record['sourceBaseHead'] == HEAD, 'Unexpected recorded command/head')
    require(record['argv'] == [sys.executable, *command[1:]] and record['cwd'] == str(ROOT.resolve()), 'Recorded interpreter or working directory changed')
    for stream in ('stdout', 'stderr'):
        require(record[stream] == {'path': str(directory / stream), **hashes((directory / stream).read_bytes())}, 'Captured raw output changed')
    return record


def previous_generic(old):
    matches = [row for row in old['validation'] if row['command'] == GENERIC_COMMAND]
    require(len(matches) == 1, 'Missing unique previous generic validation')
    result = matches[0]
    require(tuple(result[key] for key in ('tests', 'passed', 'failed', 'skipped')) == (205, 204, 0, 1), 'Previous generic result must remain 204 pass and one skip')
    require(result['sha256'] == TOOL_PINS['tests/test_architecture_contract.py'], 'Generic test pin changed')
    require(old['scannerSha256'] == TOOL_PINS['tests/architecture_contract.py'], 'Previous scanner pin changed')
    return result


def before(state):
    observed = head()
    require(not status_entries(), 'Initial checkout must be clean')
    outputs = output_hashes()
    require({name: row['lfSha256'] for name, row in outputs.items()} == OLD_OUTPUT_PINS, 'Previous audit baseline changed; review a new plan')
    previous = WORK / 'previous'
    previous.mkdir()
    for name in OUTPUTS:
        write_new(previous / name, (AUDIT / name).read_bytes())
        require(hashes((previous / name).read_bytes()) == outputs[name], 'Raw backup mismatch')
    save_new(previous / 'hashes.json', outputs)
    manifest = load(previous / OUTPUTS[0])
    old = load(previous / OUTPUTS[2])
    old_scan = load(previous / OUTPUTS[1])
    require(manifest['schema'] == 'geometry-architecture/1', 'Unexpected manifest schema')
    require(manifest['sourceRoots'] == ROOTS and manifest['sourceFiles'] == STANDALONE, 'Product roots changed')
    require(len(manifest['sources']) == 332 and len(manifest['exclusions']) == 244, 'Previous manifest count changed')
    require(old['sourceBaseHead'] == OLD_HEAD and old['inputClosureSha256'] == OLD_CLOSURE, 'Previous receipt basis changed')
    require(closure_hash(old['inputs']) == OLD_CLOSURE, 'Previous input closure is inconsistent')
    require(old['manifestSha256'] == OLD_OUTPUT_PINS[OUTPUTS[0]] and old['scanSha256'] == OLD_OUTPUT_PINS[OUTPUTS[1]] and old['reportSha256'] == OLD_OUTPUT_PINS[OUTPUTS[3]], 'Previous output pins disagree')
    require(old_scan['ok'] and not old_scan['diagnostics'] and len(old_scan['sources']) == 332 and len(old_scan['edges']) == 796, 'Unexpected previous scan record')
    previous_generic(old)
    validate_manifest_delta(manifest, expected_manifest(manifest))
    lf, raw = inventory()
    known = {row['path'] for row in manifest['sources'] + manifest['exclusions']}
    current = path_map(lf)
    old_inputs = path_map(old['inputs'])
    require(len(known) == 576 and set(old_inputs) == known, 'Previous receipt inventory differs from manifest')
    require(len(lf) == 581 and set(current) - known == set(NEW_EXCLUDED) and not known - set(current), 'Unexpected new/missing executable paths; do not self-approve them')
    require(set(stale(manifest)) == set(UPDATED_EXCLUDED), 'Stale digests differ from the sole reviewed test-driver update')
    changed = [{'path': path, 'previousSha256': old_inputs[path], 'currentSha256': current[path]} for path in sorted(known) if old_inputs[path] != current[path]]
    require({row['path'] for row in changed} == set(EXPECTED_CHANGED) | set(UPDATED_EXCLUDED), 'Changed sealed inputs must be exactly four H paths and the one reviewed excluded test driver')
    sources = {row['path']: row for row in manifest['sources']}
    for path, language in EXPECTED_CHANGED.items():
        require(sources[path]['layer'] == 'H' and sources[path]['language'] == language, 'Expected changed source ownership differs: ' + path)
    w_paths = sorted(row['path'] for row in manifest['sources'] if row['layer'] == 'W')
    require(len(w_paths) == 67 and all(current[path] == old_inputs[path] for path in w_paths), 'W sources changed; policy reuse is not authorized')
    tools = tool_hashes()
    require({path: row['lfSha256'] for path, row in tools.items()} == TOOL_PINS, 'Scanner or architecture tests changed; do not reuse old generic result')
    exclusions_provenance = exclusion_provenance()
    changed_provenance = [committed_provenance(path) for path in sorted(EXPECTED_CHANGED)]
    prior_ancestry = ancestry(OLD_HEAD)
    require(prior_ancestry['isAncestor'], 'Frozen head does not descend from the previous source basis')
    python_ancestry = ancestry(PYTHON_HEAD)
    require(python_ancestry['isAncestor'], 'Frozen head does not contain the reviewed Python default source commit')
    portability_ancestry = ancestry(PORTABILITY_HEAD)
    require(portability_ancestry['isAncestor'], 'Frozen head does not contain the reviewed launch-portability commit')
    policy_reuse = {
        'method': 'Compare every W-owned file LF hash with the previous sealed input closure; preserve the exact manifest policy without a fresh lexical inventory or new guard probes.',
        'executedNewLexicalInventory': False, 'unchangedWFiles': w_paths,
        'unchangedWInputClosureSha256': closure_hash([{'path': path, 'sha256': current[path]} for path in w_paths]),
        'identifierCountBefore': 916, 'identifierCountAfter': 916, 'stringCountBefore': 55, 'stringCountAfter': 55,
        'addedIdentifiers': [], 'addedStrings': [],
        'reusedFrom': {'receiptSha256': OLD_OUTPUT_PINS[OUTPUTS[2]], 'createdUtc': old['createdUtc'], 'sourceBaseHead': old['sourceBaseHead'],
                       'policyField': 'manifestRefresh.policyGuards', 'probeField': 'supplementalStaticGuardProbes'},
    }
    state.update(headBefore=observed, root=str(ROOT.resolve()), work=str(WORK), startedUtc=utc(),
                 driverHashes=hashes(Path(__file__).read_bytes()), driverPath=str(Path(__file__).resolve()),
                 inputsBefore=lf, rawInputsBefore=raw, previousManifest=manifest, previousReceipt=old,
                 previousReport=(previous / OUTPUTS[3]).read_bytes().decode('utf-8').replace('\r\n', '\n'),
                 previousOutputHashes=outputs, currentOutputHashes=deepcopy(outputs), toolHashesBefore=tools,
                 changedPreviouslySealedInputs=changed, changedSourceProvenance=changed_provenance,
                 exclusionProvenance=exclusions_provenance, staleDigestsBeforeRefresh=sorted(UPDATED_EXCLUDED), policyReuse=policy_reuse,
                 previousSourceAncestry=prior_ancestry, pythonSourceAncestry=python_ancestry, portabilitySourceAncestry=portability_ancestry)
    frozen(state)
    result, record = run(SCAN, 'prior-manifest')
    scan = json.loads(result.stdout)
    require(result.returncode == 1 and not scan['ok'] and len(scan['diagnostics']) == 1, 'Prior manifest did not fail closed as expected')
    diagnostic = scan['diagnostics'][0]
    require((diagnostic['code'] == 'SOURCE_UNREGISTERED' and diagnostic['path'] in NEW_EXCLUDED)
            or (diagnostic['code'] == 'EXCLUSION_DIGEST' and diagnostic['path'] in UPDATED_EXCLUDED), 'Unexpected prior-manifest diagnostic')
    state['priorManifestCheck'] = {**record, 'diagnostics': scan['diagnostics']}
    frozen(state)
    return {'head': observed, 'inputs': len(lf), 'newExclusions': len(NEW_EXCLUDED), 'changedPreviouslySealedInputs': changed, 'priorManifestCheck': state['priorManifestCheck']}


def refresh(state):
    frozen(state)
    manifest = expected_manifest(state['previousManifest'])
    validate_manifest_delta(state['previousManifest'], manifest)
    require(not stale(manifest), 'Final manifest has a stale pin')
    require(exclusion_provenance() == state['exclusionProvenance'], 'Reviewed exclusion provenance changed')
    write_output(state, OUTPUTS[0], json_bytes(manifest))
    state['addedExclusions'] = expected_exclusions()
    state['updatedExclusions'] = [{'path': path, **update} for path, update in UPDATED_EXCLUDED.items()]
    frozen(state)
    result, record = run(SCAN, 'final-scan')
    scan = json.loads(result.stdout)
    require(result.returncode == 0 and scan['ok'] and not scan['diagnostics'] and len(scan['sources']) == 332, 'Actual final CLI scan failed')
    write_output(state, OUTPUTS[1], json_bytes(scan))
    state['edges'] = len(scan['edges'])
    state['actualCliScan'] = record
    frozen(state)
    return {'actualCliScan': record, 'sources': len(scan['sources']), 'exclusions': len(manifest['exclusions']), 'edges': state['edges'], 'diagnostics': len(scan['diagnostics'])}


def product_tests(state):
    frozen(state)
    result, record = run(PRODUCT_TESTS, 'product-tests')
    output = (result.stdout + result.stderr).decode('utf-8', errors='replace')
    matches = re.findall(r'^Ran (\d+) tests in ([\d.]+)s\s*$', output, re.MULTILINE)
    require(result.returncode == 0 and len(matches) == 1 and int(matches[0][0]) == 18 and re.search(r'^OK\s*$', output, re.MULTILINE) is not None, 'Expected actual 18-test success with no skip; inspect preserved raw output')
    record = {**record, 'tests': 18, 'passed': 18, 'failed': 0, 'skipped': 0, 'unittestSeconds': float(matches[0][1]),
              'sha256': TOOL_PINS['tests/test_product_architecture.py'],
              'scope': 'Actual-root inventory, static full product graph, actual-file controls, audited iframe controls and all 69 K sources without H/W; no native/product execution.'}
    state['productTests'] = record
    save_new(WORK / 'product-tests' / 'validated.json', record)
    frozen(state)
    return record


def replace_once(text, before_text, after_text):
    require(text.count(before_text) == 1, 'Report anchor missing or duplicated: ' + before_text)
    return text.replace(before_text, after_text)


def render_report(previous, state):
    text = replace_once(previous, 'contains 576 executable files: 332 owned sources and 244', 'contains 581 executable files: 332 owned sources and 249')
    text = replace_once(text, 'There are 115 historical evidence programs,', 'There are 120 historical evidence programs,')
    text = replace_once(text, 'The latest host-authority and train19-evidence refresh freezes source HEAD', 'The preceding host-authority and train19-evidence refresh froze source HEAD')
    text = replace_once(text, 'change in #289 is not part of this frozen source and is not certified here.', 'change in #289 was not part of that 47d3bb4 frozen source and was not certified by that historical audit.')
    diagnostic = state['priorManifestCheck']['diagnostics'][0]
    added_paths = '\n'.join('- `' + path + '`' for path in NEW_EXCLUDED)
    changed_paths = '\n'.join('- `' + row['path'] + '`' for row in state['changedPreviouslySealedInputs'] if row['path'] in EXPECTED_CHANGED)
    if state['pythonSourceAncestry']['isAncestor']:
        python_note = ('Git ancestry verifies that Python default source commit `' + PYTHON_HEAD + '`\n'
                       'is included in the frozen HEAD. Its three changed H Python files are included\n'
                       'in this static closure. Their runtime behavior and native coverage require\n'
                       'their independent execution receipts; this audit does not certify them.\n')
    else:
        python_note = ('Git ancestry does not establish that Python default source commit `' + PYTHON_HEAD + '`\n'
                       'is included in the frozen HEAD. This audit seals the observed four H file\n'
                       'hashes without claiming that branch integration or its runtime acceptance.\n')
    latest = ('The final bounded architecture refresh freezes source HEAD\n`' + state['headBefore'] + '`. '
              'The previous manifest\nactually exits 1 with `' + diagnostic['code'] + '` for\n`' + diagnostic['path'] + '`. Independent enumeration\n'
              'finds exactly five newly retained historical Python evidence files:\n\n' + added_paths + '\n\n'
              'Each receives its reviewed exact path, purpose and LF digest. The receipt\n'
              'records raw/LF hashes and the matching committed Git blob. None is imported\n'
              'or executed. The 332 owned sources, existing exclusion purposes, vendor\n'
              'pins, routes and search roots remain identical. One existing exclusion\n'
              'receives the reviewed digest update described below; all other existing\n'
              'exclusion entries remain identical. No directory or filename-pattern\n'
              'exclusion is introduced.\n\n'
              'Exactly five previously sealed inputs have changed. Four are existing H sources:\n\n' + changed_paths + '\n\n'
              'The fifth is the dedicated excluded test driver\n'
              '`geometry-web/feedback_resize_observer_test.js`. Its reviewed portability\n'
              'change documents and appends `GEOMETRY_CHROME_FLAGS` to the Chrome launch.\n'
              'Assertions, test counts and timeouts remain unchanged. Only its exact LF\n'
              'digest is updated; its exclusion reason and test-only responsibility stay\n'
              'the same. The receipt records the old/new digest and committed blob.\n'
              'This static audit does not execute that browser flow.\n\n'
              'All 67 W source LF hashes still match the preceding sealed closure. The\n'
              'exact policy is reused with 916 forbidden identifiers and 55 strings, zero\n'
              'new guards and no new supplemental probes. The preceding lexical inventory\n'
              'and three probes remain historical evidence with their original source and\n'
              'timestamps; they are not reported as executions at the final HEAD.\n\n' + python_note + '\n'
              'The previous four audit outputs are preserved byte-for-byte in the external\n'
              'run directory. The new receipt links their raw/LF digests and the previous\n'
              'receipt source and creation time. Existing evidence packages and seals are\n'
              'untouched, including their original PASS, FAIL and UNRUN classifications.\n\n')
    text = replace_once(text, 'The manifest, scan, report and receipt are excluded from the product\n', latest + 'The manifest, scan, report and receipt are excluded from the product\n')
    start = text.index('At the latest sealed source HEAD,')
    end = text.index('\nWhen new provider files are integrated,', start)
    summary = ('At the latest sealed source HEAD `' + state['headBefore'] + '`,\n'
               'the actual CLI scan exits 0 with 332 owned sources, ' + str(state['edges']) + '\n'
               'dependency edges and no diagnostics. All 18 actual product tests pass with\n'
               'no skips. Independent enumeration matches all 581 input hashes, both raw\n'
               'and LF-normalized. The generic scanner suite is not rerun at this HEAD:\n'
               'its previous 205-test result remains 204 passes and one Windows symlink\n'
               'permission skip. Reuse is limited to the unchanged scanner and generic-test\n'
               'LF hashes; the receipt retains the full prior provenance chain. No new\n'
               'supplemental guard probes run. HEAD and all product/scanner/test raw and LF\n'
               'hashes remain fixed throughout this finite refresh.\n')
    return text[:start] + summary + text[end:]


def report(state):
    frozen(state)
    require(read_run('final-scan', SCAN) == state['actualCliScan'], 'Final scan metadata changed')
    product_raw = read_run('product-tests', PRODUCT_TESTS)
    require(all(state['productTests'][key] == value for key, value in product_raw.items()), 'Product execution metadata changed')
    text = render_report(state['previousReport'], state)
    write_output(state, OUTPUTS[3], text.encode('utf-8'))
    frozen(state)
    return {'reportHashes': state['currentOutputHashes'][OUTPUTS[3]]}


def seal(state):
    frozen(state)
    old = state['previousReceipt']
    manifest = load(AUDIT / OUTPUTS[0])
    scan = load(AUDIT / OUTPUTS[1])
    validate_manifest_delta(state['previousManifest'], manifest)
    require(scan == json.loads((WORK / 'final-scan' / 'stdout').read_bytes()) and scan['ok'] and not scan['diagnostics'] and not stale(manifest), 'Final actual scan does not match saved output')
    scan_run = read_run('final-scan', SCAN)
    prior_run = read_run('prior-manifest', SCAN)
    require(all(state['priorManifestCheck'][key] == value for key, value in prior_run.items()), 'Prior fail-closed execution metadata changed')
    require(json.loads((WORK / 'prior-manifest' / 'stdout').read_bytes())['diagnostics'] == state['priorManifestCheck']['diagnostics'], 'Prior fail-closed diagnostics changed')
    product_run = read_run('product-tests', PRODUCT_TESTS)
    require(scan_run == state['actualCliScan'] and scan_run['exitCode'] == 0, 'Scan metadata changed')
    product = deepcopy(state['productTests'])
    require(all(product[key] == value for key, value in product_run.items()) and product_run['exitCode'] == 0, 'Product execution metadata changed')
    require(tuple(product[key] for key in ('tests', 'passed', 'failed', 'skipped')) == (18, 18, 0, 0), 'Product result must be 18 actual passes')
    require(load(WORK / 'product-tests' / 'validated.json') == product, 'Product validation record changed')
    require(state['policyReuse']['addedIdentifiers'] == [] and state['policyReuse']['addedStrings'] == [] and not (WORK / 'guards.run.json').exists(), 'No new guards/probes are authorized')
    generic = deepcopy(previous_generic(old))
    generic['reusedFrom'] = {'receiptSha256': OLD_OUTPUT_PINS[OUTPUTS[2]], 'createdUtc': old['createdUtc'], 'sourceBaseHead': old['sourceBaseHead'], 'priorProvenance': deepcopy(generic['reusedFrom'])}
    generic['reuseReason'] = 'Scanner and generic-test LF hashes exactly match the preceding sealed receipt and raw/LF bytes stay fixed throughout this run. This 205-test suite was not rerun at the final source HEAD: 204 passes plus one skip. Current manifest additions are covered by the actual 18 product tests. No new supplemental guard probes run.'
    generic['scannerSha256AtReuse'] = TOOL_PINS['tests/architecture_contract.py']
    generic['executedAtCurrentHead'] = False
    lf, raw = inventory()
    require(lf == state['inputsBefore'] and raw == state['rawInputsBefore'], 'Independent final source closure changed')
    require(set(path_map(lf)) == {row['path'] for row in manifest['sources'] + manifest['exclusions']}, 'Final inventory is not exact')
    counts = {'executableFiles': len(lf), 'ownedSources': len(manifest['sources']), 'exclusions': len(manifest['exclusions']),
              'edges': len(scan['edges']), 'diagnostics': len(scan['diagnostics']),
              'layers': dict(sorted(Counter(row['layer'] for row in manifest['sources']).items())),
              'languages': dict(sorted(Counter(row['language'] for row in manifest['sources']).items())),
              'forbiddenIdentifiers': len(manifest['policy']['forbiddenIdentifiers']), 'forbiddenStrings': len(manifest['policy']['forbiddenStrings'])}
    receipt = {key: deepcopy(old[key]) for key in ('schema', 'headBinding', 'hashMode', 'inputClosureHashSerialization', 'inputClosureExcludes', 'inputClosureExclusionReason', 'notClaimed')}
    receipt.update(
        createdUtc=utc(), basis='Committed integration product sources at sourceBaseHead, plus this finite manifest/scan/report/receipt refresh.',
        sourceBaseHead=HEAD, headObservedBefore=state['headBefore'], headObservedAfter=head(),
        manifestSha256=state['currentOutputHashes'][OUTPUTS[0]]['lfSha256'], scannerSha256=TOOL_PINS['tests/architecture_contract.py'],
        scanSha256=state['currentOutputHashes'][OUTPUTS[1]]['lfSha256'], reportSha256=state['currentOutputHashes'][OUTPUTS[3]]['lfSha256'],
        inputClosureSha256=closure_hash(lf), counts=counts,
        manifestRefresh={
            'previousManifestSha256': OLD_OUTPUT_PINS[OUTPUTS[0]], 'previousReceiptSha256': OLD_OUTPUT_PINS[OUTPUTS[2]],
            'previousReceiptCreatedUtc': old['createdUtc'], 'previousSourceBaseHead': old['sourceBaseHead'], 'firstObservedHead': HEAD,
            'previousOutputsPreserved': {'directory': str(WORK / 'previous'), 'hashes': state['previousOutputHashes']},
            'priorManifestCheck': state['priorManifestCheck'], 'addedSources': [], 'addedExclusions': state['addedExclusions'], 'updatedExclusions': state['updatedExclusions'],
            'exclusionProvenance': state['exclusionProvenance'], 'policyGuards': state['policyReuse'],
            'changedPreviouslySealedInputs': state['changedPreviouslySealedInputs'], 'changedSourceProvenance': state['changedSourceProvenance'],
            'staleExcludedVendorOrEmbedDigestsBefore': state['staleDigestsBeforeRefresh'], 'staleExcludedVendorOrEmbedDigestsAfter': [],
            'sourceFix': 'No product source, scanner or test changes are made by this audit. Preserve ownership, policy, routes and all exclusion purposes; add five individually reviewed hash-locked historical evidence exclusions and update only the reviewed ResizeObserver test-driver digest. Seal four already integrated H source changes plus that one test-driver change without claiming runtime acceptance.',
            'previousSourceAncestry': state['previousSourceAncestry'], 'pythonSourceAncestry': state['pythonSourceAncestry'], 'portabilitySourceAncestry': state['portabilitySourceAncestry'],
        },
        scanPassed=True, actualCliScan=scan_run, validation=[generic, product],
        supplementalStaticGuardProbes={
            'executedAtCurrentHead': False, 'identifierProbes': 0, 'stringProbes': 0, 'addedIdentifiers': [], 'addedStrings': [],
            'reason': 'All W source LF hashes and the complete policy are unchanged; no new guard or fresh probe is authorized.',
            'historicalEvidence': {'receiptSha256': OLD_OUTPUT_PINS[OUTPUTS[2]], 'createdUtc': old['createdUtc'], 'sourceBaseHead': old['sourceBaseHead'], 'originalRecord': deepcopy(old['supplementalStaticGuardProbes'])},
        },
        nativeAcceptance='Not evaluated by this static audit. C/native/WSL/Node aggregate and product behavior were not executed. Historical receipts retain their original source SHA, timestamps and PASS/FAIL/UNRUN. Python default and native coverage runtime acceptance require separate execution receipts; static closure and ancestry do not certify them.',
        inputs=lf,
        completeInventoryVerification={
            'method': 'Independent os.walk of all executable suffixes under five roots plus three exact standalone sources, without importing scanner inventory or deriving paths from manifest. Compare full raw/LF closures, tool bytes, HEAD and Git status at every stage.',
            'sourceRoots': ROOTS, 'sourceFiles': STANDALONE, 'executableSuffixes': sorted(SUFFIXES), 'filesBefore': len(state['inputsBefore']), 'filesAfter': len(lf),
            'unregisteredBeforeRefresh': sorted(NEW_EXCLUDED), 'unregisteredAfter': [], 'missingAfter': [], 'changedInputs': [],
            'inputClosureSha256Before': closure_hash(state['inputsBefore']), 'inputClosureSha256After': closure_hash(lf),
            'rawInputClosureSha256Before': closure_hash(state['rawInputsBefore']), 'rawInputClosureSha256After': closure_hash(raw),
            'toolHashesBefore': {path: row['lfSha256'] for path, row in state['toolHashesBefore'].items()},
            'toolHashesAfter': {path: row['lfSha256'] for path, row in tool_hashes().items()},
            'rawToolHashesBefore': {path: row['rawSha256'] for path, row in state['toolHashesBefore'].items()},
            'rawToolHashesAfter': {path: row['rawSha256'] for path, row in tool_hashes().items()},
            'headObservedAfterIndependentAudit': head(), 'checkedUtc': utc(),
        },
        refreshDriver={'path': state['driverPath'], **state['driverHashes'], 'runDirectory': str(WORK)},
    )
    write_output(state, OUTPUTS[2], json_bytes(receipt))
    require(load(AUDIT / OUTPUTS[2]) == receipt, 'Receipt read-back failed')
    require(receipt['notClaimed'] == old['notClaimed'], 'Scope exclusions changed')
    frozen(state)
    changed_outputs = set(status_entries())
    allowed_outputs = {AUDIT_REL + name for name in OUTPUTS}
    required_changes = {AUDIT_REL + OUTPUTS[index] for index in (0, 2, 3)}
    require(required_changes <= changed_outputs <= allowed_outputs, 'Only audit outputs may change; manifest/report/receipt must be refreshed')
    for name, key in ((OUTPUTS[0], 'manifestSha256'), (OUTPUTS[1], 'scanSha256'), (OUTPUTS[3], 'reportSha256')):
        require(sha(AUDIT / name) == receipt[key], 'Final output pin mismatch: ' + name)
    result = {'head': HEAD, 'counts': counts, 'inputClosureSha256': receipt['inputClosureSha256'], 'rawInputClosureSha256': closure_hash(raw),
              'outputHashes': output_hashes(), 'actualProductTests': product, 'genericReusedOnly': True, 'genericPassed': 204, 'genericSkipped': 1,
              'newGuardProbesExecuted': False, 'allRawAndLfInputsUnchanged': True}
    save_new(WORK / 'final-output-hashes.json', result)
    return result


def begin_stage(stage):
    index = STAGES.index(stage)
    if index == 0:
        require(not WORK.exists(), 'WORK already exists; never overwrite an old or failed run')
        WORK.mkdir()
        state = {'completedStages': []}
    else:
        require(WORK.is_dir() and not is_link(WORK), 'Missing or redirected run directory')
        state = load(WORK / 'state.json')
        require(state['completedStages'] == list(STAGES[:index]), 'Stage order mismatch or stage already completed')
        previous_snapshot = WORK / (STAGES[index - 1] + '.state.json')
        require(load(previous_snapshot) == state, 'Mutable state differs from the immutable completed-stage snapshot')
        require(hashes(previous_snapshot.read_bytes()) == load(WORK / (STAGES[index - 1] + '.complete.json'))['stateHashes'], 'Completed-stage state seal changed')
        frozen(state)
    attempt = WORK / (stage + '.attempt')
    attempt.mkdir()
    save_new(attempt / 'started.json', {'stage': stage, 'sourceBaseHead': HEAD, 'startedUtc': utc(), 'driverHashes': hashes(Path(__file__).read_bytes())})
    return state, attempt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=STAGES)
    stage = parser.parse_args().stage
    configure()
    state, attempt = begin_stage(stage)
    try:
        result = {'before': before, 'refresh': refresh, 'product_tests': product_tests, 'report': report, 'seal': seal}[stage](state)
        frozen(state)
        state['completedStages'].append(stage)
        snapshot = WORK / (stage + '.state.json')
        save_new(snapshot, state)
        (WORK / 'state.json').write_bytes(json_bytes(state))
        require(load(WORK / 'state.json') == load(snapshot), 'Stage state read-back failed')
        save_new(WORK / (stage + '.complete.json'), {'stage': stage, 'finishedUtc': utc(), 'stateHashes': hashes(snapshot.read_bytes()), 'result': result})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except BaseException as error:
        save_new(attempt / 'failed.json', {'stage': stage, 'finishedUtc': utc(), 'error': repr(error), 'policy': 'Keep raw outputs; do not retry or widen scope in this run directory.'})
        raise


if __name__ == '__main__':
    main()
