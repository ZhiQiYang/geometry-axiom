#!/usr/bin/env python3
"""Append four completed native receipts without rewriting their sealed predecessor."""
import argparse
from collections import defaultdict
import datetime
import hashlib
import io
import json
import lzma
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

RUNS = ['native-candidate-6f1fd92f-v1', 'section-runs-diagnostic-6f1fd92f-v1',
        'native-candidate-14ab395d-v1', 'timeout-diagnostic-14ab395d-v1']
RUNNER_DIRS = ['native-next-6f1fd92f', 'section-runs-diagnostic-6f1fd92f',
               'native-next-14ab395d', 'timeout-diagnostic-14ab395d']
EXTRA_FILES = ['extract-14ab-readonly.py',
               'shared-lock-native-candidate-6f1fd92f-v1.log', 'native-candidate-6f1fd92f-v1-launcher-exit.txt',
               'shared-lock-section-runs-diagnostic-6f1fd92f-v1.log', 'section-runs-diagnostic-6f1fd92f-v1-launcher-exit.txt',
               'shared-lock-native-candidate-14ab395d-v1.log', 'native-candidate-14ab395d-v1-launcher-exit.txt',
               'shared-lock-timeout-diagnostic-14ab395d-v1.log', 'timeout-diagnostic-14ab395d-v1-launcher-exit.txt']
TEXT_SUFFIXES = {'.json', '.log', '.txt', '.py', '.sh', '.md', '.c', '.h', '.inc', '.cmd', '.scene', '.cjs'}
PREDECESSOR_COMMIT = '3de118155ae4ee4233db473e67ea39caf1769396'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def hashes_in(value, label=''):
    if isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value):
        yield label, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from hashes_in(item, label + '/' + key)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--predecessor', type=Path, required=True)
    args = parser.parse_args()
    evidence, output, predecessor = args.evidence.resolve(), args.out.resolve(), args.predecessor.resolve()
    selected = {}
    for name in RUNS:
        if not (evidence / name / 'summary.json').is_file() or not (evidence / name / 'exit.txt').is_file():
            raise RuntimeError('Incomplete original receipt: ' + name)
    for name in RUNS + RUNNER_DIRS + ['14ab-readonly-diagnostics']:
        for path in sorted((evidence / name).rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            relative = path.relative_to(evidence).as_posix()
            if path.is_symlink() or ('mutations' in path.parts and 'source' in path.parts):
                raise RuntimeError('Unpermitted source tree or symlink: ' + relative)
            if path.suffix not in TEXT_SUFFIXES and path.name not in ('stdout.bin', 'stderr.bin'):
                raise RuntimeError('Unexpected selected evidence format: ' + relative)
            selected[relative] = path
    for name in EXTRA_FILES:
        path = evidence / name
        if not path.is_file():
            raise RuntimeError('Missing explicit launcher or extraction helper: ' + name)
        selected[name] = path
    selected['runtime/wsl_locked3.sh'] = predecessor / 'readable/runtime/wsl_locked3.sh'
    old_manifest_raw = (predecessor / 'PACKAGE-SHA256.json').read_bytes()
    old_manifest = json.loads(old_manifest_raw)
    old_files = dict(old_manifest['files'])
    old_files['PACKAGE-SHA256.json'] = {'sha256': sha(old_manifest_raw), 'bytes': len(old_manifest_raw)}
    actual_old = {p.relative_to(predecessor).as_posix() for p in predecessor.rglob('*') if p.is_file()}
    assert set(old_files) == actual_old
    assert len(old_files) == 203
    for name, record in old_files.items():
        raw = (predecessor / name).read_bytes()
        assert sha(raw) == record['sha256'] and len(raw) == record['bytes'], name
    old_catalog = json.loads((predecessor / 'CONTENT-MANIFEST.json').read_bytes())
    assert len(old_catalog['completedReceipts']) == 24
    output.mkdir(parents=True, exist_ok=False)
    records, blobs = {}, {}
    for relative, path in selected.items():
        raw = path.read_bytes()
        raw.decode('utf-8')  # .bin here is captured text output, never an executable.
        digest = sha(raw)
        record = {'sha256': digest, 'bytes': len(raw), 'archiveEntry': 'blobs/' + digest}
        records[relative] = record
        blobs.setdefault(digest, raw)
        parts = Path(relative).parts
        is_raw_overview = parts[0] == '14ab-readonly-diagnostics' or len(parts) == 1
        is_runner = parts[0] in RUNNER_DIRS or parts[0] == 'runtime'
        is_receipt_top = parts[0] in RUNS and len(parts) == 2 and path.name not in ('source-before.json', 'source-after.json', 'original-receipt-before.json', 'original-receipt-after.json', 'native-build-artifacts.json', 'build-artifacts.json', 'build-log.json')
        is_measurement = parts[0] == 'timeout-diagnostic-14ab395d-v1' and len(parts) == 3
        if is_raw_overview or is_runner or is_receipt_top or is_measurement:
            target = output / 'readable' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            record['readableCopy'] = target.relative_to(output).as_posix()
    digest_paths = defaultdict(list)
    for name, record in records.items():
        digest_paths[record['sha256']].append(name)
    summaries = {name: json.loads(blobs[records[name + '/summary.json']['sha256']]) for name in RUNS}
    claims, plans, commits = [], [], set()
    for name, summary in summaries.items():
        for key, value in summary.items():
            if 'runner' in key.lower().replace('_', '') and 'sha256' in key.lower():
                for pointer, digest in hashes_in(value, '/' + key):
                    matches = [p for p in digest_paths[digest] if Path(p).suffix in ('.py', '.sh', '.json')]
                    claims.append({'receipt': name, 'field': pointer, 'expectedSha256': digest,
                                   'retainedMatchingFiles': matches, 'bytesRecovered': bool(matches)})
        source = summary['source']
        commits.add(source)
        manifest = name + '/source-before.json'
        plans.append({'receipt': name, 'source': source, 'manifest': manifest,
                      'fileCount': len(json.loads(blobs[records[manifest]['sha256']])),
                      'coverage': 'complete-archived-or-clean-checkout-source', 'allowCrlfCheckoutVariant': False,
                      'judgeSource': None, 'judgeOnlyAddedFiles': {}, 'baselineAdapterSource': None,
                      'rawSummary': name + '/summary.json'})
    missing = [claim for claim in claims if not claim['bytesRecovered']]
    if missing:
        raise RuntimeError('Unresolved original runner identity: ' + repr(missing))
    save(output / 'RUNNER-PROVENANCE.json', {'claims': claims, 'missing': missing})
    commit_records = {}
    for commit in sorted(commits):
        raw = subprocess.check_output(['git', '-C', str(args.repo), 'cat-file', 'commit', commit])
        object_id = hashlib.sha1(b'commit ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        assert object_id == commit
        target = output / 'source-commits' / (commit + '.commit')
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(raw)
        commit_records[commit] = {'file': target.relative_to(output).as_posix(), 'sha256': sha(raw),
                                  'bytes': len(raw), 'gitCommitObjectId': object_id,
                                  'tree': raw.splitlines()[0].decode().removeprefix('tree ')}
    save(output / 'SOURCE-PROVENANCE.json', {'plans': plans, 'commits': commit_records,
         'note': 'All four receipts retain complete source manifests; Git archive comparison verifies both exact source commits without executing product code.'})
    save(output / 'PREDECESSOR.json', {'schema': 'geometry-p1-append-only-predecessor/1',
         'siblingDirectory': predecessor.name, 'publishedCommit': PREDECESSOR_COMMIT,
         'pullRequest': 'https://github.com/ZhiQiYang/geometry-axiom/pull/286',
         'completedReceiptCount': 24, 'fileCount': len(old_files), 'files': old_files,
         'archiveSha256': old_catalog['archive']['sha256'], 'newReceiptCount': 4,
         'sourceRuns': 2, 'diagnosticRuns': 2, 'defaultDumpIsExtractionOnly': True})
    archive_path = output / 'raw-evidence.tar.xz'
    with lzma.open(archive_path, 'wb', preset=6) as compressed:
        with tarfile.open(fileobj=compressed, mode='w|') as archive:
            for digest, raw in blobs.items():
                info = tarfile.TarInfo('blobs/' + digest)
                info.size, info.mtime, info.mode = len(raw), 0, 0o644
                archive.addfile(info, io.BytesIO(raw))
    unchanged = all(sha(path.read_bytes()) == records[name]['sha256'] for name, path in selected.items())
    assert unchanged
    catalog = {'schema': 'geometry-p1-portable-evidence/1', 'capturedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'completedReceipts': RUNS, 'files': records, 'omitted': [],
               'rawFiles': len(records), 'rawBytes': sum(r['bytes'] for r in records.values()),
               'uniqueBlobs': len(blobs), 'uniqueBytes': sum(map(len, blobs.values())),
               'archive': {'file': archive_path.name, 'sha256': sha(archive_path.read_bytes()), 'bytes': archive_path.stat().st_size},
               'originalEvidenceUnchanged': unchanged, 'fullAcceptanceClaimed': False,
               'binariesIncluded': False, 'sourceCheckoutsIncluded': False,
               'newProductTestsExecutedByPackaging': False, 'missingRunnerClaimCount': 0,
               'predecessor': 'PREDECESSOR.json', 'appendOnly': True,
               'unexecutedContinuations': ['PF-3 original 50 methods and original 19-mutation driver', 'original 27-method section-profile suite']}
    save(output / 'CONTENT-MANIFEST.json', catalog)
    for name in ('prepare_publication.py', 'verify_publication.py', 'verify_followup.py', 'extract_evidence.py', 'README.md', '.gitattributes'):
        shutil.copyfile(Path(__file__).parent / name, output / name)
    print(json.dumps({key: value for key, value in catalog.items() if key not in ('files', 'omitted')}, indent=2))


if __name__ == '__main__':
    main()
