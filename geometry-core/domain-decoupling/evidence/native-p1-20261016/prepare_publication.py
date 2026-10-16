#!/usr/bin/env python3
"""Copy immutable completed P1 evidence into a portable, binary-free package."""
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

RUNS = [
    'baseline-adapters-a898ad6e', 'producer-retry-v2', 'grid-rename-native-v1',
    'native-kernel-ab90a56d-v1', 'native-geometry-51e9045b-v1', 'grid-rename-native-v2',
    'region-edges-old-51e9045b-v1', 'region-edges-new-be9ed3e7-v1', 'native-grid-49f03842-v1',
    'native-parameters-4aabd21c-v1', 'parameters-legacy-4aabd21c-v1', 'native-annotation-b370f753-v1',
    'native-datums-c28ea963-v1', 'rectangular-template-c6599522-v1', 'native-corrected-db65132a-v1',
    'parameters-legacy-db65132a-v1', 'grid-rename-native-v3', 'region-edges-old-51e9045b-v2',
    'region-edges-new-a88d3c57-v2', 'datum-baseline-a898-v1', 'native-groups-99eeabe1-v1',
    'native-closure-a3aeef41-v1', 'pf3-regressions-a3aeef41-v1', 'native-grid-product-b21334a2-v1',
]
RUNNER_DIRS = ['producer', 'next-batch', 'native-next-99eeabe1', 'datum-baseline-witness',
               'native-next-a3aeef41', 'pf3-a3aeef41', 'native-next-b21334a2']
EXTRA_DIRS = ['compatibility-baseline-v1', 'compatibility-baseline-v2']
SUFFIXES = {'.json', '.log', '.txt', '.py', '.sh', '.md', '.c', '.h', '.inc', '.cmd', '.scene', '.cjs', '.stdout', '.stderr'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


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
    parser.add_argument('--wrapper', type=Path, required=True)
    args = parser.parse_args()
    evidence, output = args.evidence.resolve(), args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    selected = {}
    omitted = []

    def admit(path):
        if not path.is_file() or '__pycache__' in path.parts:
            return
        relative = path.relative_to(evidence).as_posix()
        parts = Path(relative).parts
        if parts[0] == 'pf3-regressions-a3aeef41-v1' and 'mutations' in parts and 'source' in parts:
            return
        if path.suffix.lower() not in SUFFIXES and path.name not in ('stdout', 'stderr'):
            omitted.append({'path': relative, 'reason': 'outside text evidence allowlist; no binaries or full source archive copied'})
            return
        selected[relative] = path

    for name in RUNS:
        if not (evidence / name / 'summary.json').is_file() or not (evidence / name / 'exit.txt').is_file():
            raise RuntimeError('Incomplete selected receipt: ' + name)
        for path in sorted((evidence / name).rglob('*')):
            admit(path)
    for name in RUNNER_DIRS + EXTRA_DIRS:
        for path in sorted((evidence / name).rglob('*')):
            admit(path)
    for path in sorted(evidence.iterdir()):
        if path.is_file():
            admit(path)
    # This helper was imported by the completed datum witness and its hash is in that receipt.
    admit(evidence / 'fixture-reopen/run_native_pair.py')
    selected['runtime/wsl_locked3.sh'] = args.wrapper.resolve()

    records, blobs, readable, raw_bytes = {}, {}, {}, 0
    for relative, path in selected.items():
        data = path.read_bytes()
        digest = sha(data)
        records[relative] = {'sha256': digest, 'bytes': len(data), 'archiveEntry': 'blobs/' + digest}
        blobs.setdefault(digest, data)
        raw_bytes += len(data)
        parts = Path(relative).parts
        is_runner = (len(parts) == 1 and path.suffix in ('.py', '.sh')) or (parts[0] in RUNNER_DIRS and path.suffix in ('.py', '.sh', '.json')) or relative in ('fixture-reopen/run_native_pair.py', 'runtime/wsl_locked3.sh')
        is_summary = path.name in ('summary.json', 'test-result.json', 'test-discovery.json', 'exit.txt') and parts[0] in RUNS and len(parts) == 2
        is_overview = len(parts) == 1 and (path.suffix == '.md' or path.name.endswith('stage-results.json') or 'launcher-exit' in path.name)
        if is_runner or is_summary or is_overview:
            target = output / 'readable' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            readable[relative] = target.relative_to(output).as_posix()
            records[relative]['readableCopy'] = readable[relative]

    summaries = {name: json.loads(blobs[records[name + '/summary.json']['sha256']]) for name in RUNS}
    digest_paths = defaultdict(list)
    for relative, record in records.items():
        digest_paths[record['sha256']].append(relative)
    runner_claims = []
    for name, summary in summaries.items():
        for key, value in summary.items():
            normalized = key.lower().replace('_', '')
            if ('runner' in normalized or normalized == 'producerscriptsha256') and 'sha256' in normalized:
                for pointer, expected in hashes_in(value, '/' + key):
                    matches = [p for p in digest_paths[expected] if Path(p).suffix in ('.py', '.sh', '.json')]
                    runner_claims.append({'receipt': name, 'field': pointer, 'expectedSha256': expected, 'retainedMatchingFiles': matches, 'bytesRecovered': bool(matches)})
    for relative in ('continuation-runner-before.json', 'continuation-runner-after.json', 'next-batch-v1-runner-before.json', 'next-batch-v1-runner-after.json'):
        for pointer, expected in hashes_in(json.loads(blobs[records[relative]['sha256']])):
            matches = [p for p in digest_paths[expected] if Path(p).suffix in ('.py', '.sh', '.json')]
            runner_claims.append({'receipt': relative, 'field': pointer, 'expectedSha256': expected, 'retainedMatchingFiles': matches, 'bytesRecovered': bool(matches)})
    save(output / 'RUNNER-PROVENANCE.json', {'claims': runner_claims, 'missing': [r for r in runner_claims if not r['bytesRecovered']]})

    source_plans = []
    commits = set()
    for name, summary in summaries.items():
        source = summary.get('source') or summary.get('product_source') or summary.get('rename_commit')
        commits.add(source)
        if summary.get('judge_source'):
            commits.add(summary['judge_source'])
        if summary.get('baseline_main'):
            commits.add(summary['baseline_main'])
        manifest_name = name + '/source-before.json'
        if manifest_name not in records:
            expected = summary.get('source_before_sha256')
            matches = [p for p in digest_paths.get(expected, []) if p.endswith('/source-before.json')]
            if not matches:
                raise RuntimeError('Missing original source manifest for ' + name)
            manifest_name = matches[0]
        manifest = json.loads(blobs[records[manifest_name]['sha256']])
        source_plans.append({'receipt': name, 'source': source, 'manifest': manifest_name, 'fileCount': len(manifest),
                             'coverage': 'partial-recorded-subset' if name == 'grid-rename-native-v1' else 'complete-archived-or-clean-checkout-source',
                             'allowCrlfCheckoutVariant': name == 'grid-rename-native-v1',
                             'judgeSource': summary.get('judge_source'), 'judgeOnlyAddedFiles': summary.get('judge_only_added_files', {}),
                             'baselineAdapterSource': summary.get('baseline_main'),
                             'rawSummary': name + '/summary.json'})
    commit_records = {}
    for commit in sorted(commits):
        if not re.fullmatch('[0-9a-f]{40}', commit or ''):
            raise RuntimeError('Invalid source identity')
        raw = subprocess.check_output(['git', '-C', str(args.repo), 'cat-file', 'commit', commit])
        object_id = hashlib.sha1(b'commit ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if object_id != commit:
            raise RuntimeError('Commit object identity mismatch')
        target = output / 'source-commits' / (commit + '.commit')
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(raw)
        tree = raw.splitlines()[0].decode().removeprefix('tree ')
        commit_records[commit] = {'file': target.relative_to(output).as_posix(), 'sha256': sha(raw), 'bytes': len(raw), 'gitCommitObjectId': object_id, 'tree': tree}
    save(output / 'SOURCE-PROVENANCE.json', {'plans': source_plans, 'commits': commit_records, 'note': 'Commit objects prove the named commit identity. Optional Git archive verification checks every recorded source file against those commits without creating a checkout.'})

    archive_path = output / 'raw-evidence.tar.xz'
    with lzma.open(archive_path, 'wb', preset=6) as compressed:
        with tarfile.open(fileobj=compressed, mode='w|') as archive:
            for digest, data in blobs.items():
                info = tarfile.TarInfo('blobs/' + digest)
                info.size = len(data)
                info.mtime = 0
                info.mode = 0o644
                archive.addfile(info, io.BytesIO(data))
    unchanged = all(sha(path.read_bytes()) == records[relative]['sha256'] for relative, path in selected.items())
    if not unchanged:
        raise RuntimeError('Raw evidence changed during publication capture')
    catalog = {'schema': 'geometry-p1-portable-evidence/1', 'capturedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'completedReceipts': RUNS, 'files': records, 'omitted': omitted,
               'rawFiles': len(records), 'rawBytes': raw_bytes, 'uniqueBlobs': len(blobs), 'uniqueBytes': sum(map(len, blobs.values())),
               'archive': {'file': archive_path.name, 'sha256': sha(archive_path.read_bytes()), 'bytes': archive_path.stat().st_size},
               'originalEvidenceUnchanged': unchanged, 'fullAcceptanceClaimed': False, 'binariesIncluded': False,
               'sourceCheckoutsIncluded': False, 'newProductTestsExecutedByPackaging': False,
               'missingRunnerClaimCount': sum(not row['bytesRecovered'] for row in runner_claims)}
    save(output / 'CONTENT-MANIFEST.json', catalog)
    shutil.copyfile(Path(__file__), output / 'prepare_publication.py')
    for name in ('verify_publication.py', 'extract_evidence.py', 'README.md', '.gitattributes'):
        shutil.copyfile(Path(__file__).parent / name, output / name)
    print(json.dumps({key: value for key, value in catalog.items() if key not in ('files', 'omitted', 'completedReceipts')}, indent=2))


if __name__ == '__main__':
    main()
