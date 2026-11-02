"""Acquire fixed source artifacts and replay the unchanged read-only verifier."""
import argparse
import concurrent.futures
import datetime
import hashlib
import importlib.util
import json
import os
import platform
from pathlib import Path
import stat
import subprocess
import sys
import time
import zipfile

OUT = Path(__file__).resolve().parent
SOURCE = Path('/tmp/geometry-pr345-20261102')
HEAD = 'de3a56cfadecf575f8e7860cbfdafdac2af0a883'
RUN = 41431971663
BASE = 'https://api.github.com/repos/ZhiQiYang/geometry-axiom'
spec = importlib.util.spec_from_file_location('existing_read_only_acquisition',
    '/tmp/geometry-resume-20261102/ci-followup/pr344-E503cfc59/acquire_evidence.py')
network = importlib.util.module_from_spec(spec)
spec.loader.exec_module(network)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
git = lambda *args: subprocess.check_output(['git', *args], cwd=SOURCE, text=True).strip()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def prepare():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder = OUT / 'api' / stamp
    receipts = []
    for name, suffix in [('run', ''), ('jobs', '/jobs?per_page=100'), ('artifacts', '/artifacts?per_page=100')]:
        receipts.append(network.fetch(f'{BASE}/actions/runs/{RUN}{suffix}', folder / (name + '.json')))
    run = json.loads((folder / 'run.json').read_text())
    jobs = json.loads((folder / 'jobs.json').read_text())['jobs']
    artifacts = json.loads((folder / 'artifacts.json').read_text())['artifacts']
    assert run['head_sha'] == HEAD and run['event'] == 'workflow_dispatch' and run['run_attempt'] == 1
    assert run['status'] == 'completed' and run['conclusion'] == 'success'
    assert len(jobs) == 10 and all(j['conclusion'] == 'success' for j in jobs)
    assert len(artifacts) == 9 and all(not a['expired'] and a['workflow_run']['id'] == RUN for a in artifacts)
    assert git('rev-parse', 'HEAD') == HEAD and git('status', '--porcelain=v1') == ''
    plan = {'run': RUN, 'head': HEAD, 'source_tree': git('rev-parse', 'HEAD^{tree}'),
        'api_folder': str(folder), 'acquisitions': receipts,
        'artifact_total_zip_bytes': sum(a['size_in_bytes'] for a in artifacts),
        'artifacts': artifacts, 'jobs': [{'id': j['id'], 'name': j['name']} for j in jobs],
        'mode': 'metadata only; original verifier not yet replayed'}
    write(OUT / 'DOWNLOAD_PLAN.json', plan)
    return plan


def acquire(artifact):
    destination = OUT / 'official-zips' / f"{artifact['id']}.zip"
    if destination.exists():
        assert 'sha256:' + sha(destination) == artifact['digest'], 'Keep changed original file; do not overwrite.'
        receipt = {'file': str(destination), 'sha256': sha(destination), 'reused_verified_bytes': True}
    else:
        receipt = network.fetch(artifact['archive_download_url'], destination)
    assert destination.stat().st_size == artifact['size_in_bytes']
    assert 'sha256:' + sha(destination) == artifact['digest']
    name = artifact['name']
    assert '/' not in name and '..' not in name
    group = 'shards' if name.startswith('mutation-shard-') else 'other'
    folder = OUT / 'extracted' / group / name
    assert not folder.exists(), 'Do not overwrite previous extraction.'
    members = []
    with zipfile.ZipFile(destination) as archive:
        for info in archive.infolist():
            assert not info.filename.startswith('/') and '..' not in Path(info.filename).parts
            assert stat.S_IFMT(info.external_attr >> 16) != stat.S_IFLNK
            if info.is_dir():
                continue
            path = folder / info.filename
            path.parent.mkdir(parents=True, exist_ok=True)
            data = archive.read(info)
            path.write_bytes(data)
            members.append({'path': info.filename, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    return {'id': artifact['id'], 'name': name, 'download': receipt, 'members': members}


def verify(plan):
    assert git('rev-parse', 'HEAD') == HEAD and git('status', '--porcelain=v1') == ''
    output = OUT / 'original-verifier-replay'
    assert not output.exists(), 'Original output must not exist; do not silently repeat a completed replay.'
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        receipts = list(executor.map(acquire, plan['artifacts']))
    write(OUT / 'ARTIFACT_BYTES.json', receipts)
    manifests = list((OUT / 'extracted/shards').glob('*/manifest.json'))
    assert len(manifests) == 7
    probes = []
    for path in manifests:
        manifest = json.loads(path.read_text())
        assert manifest['head'] == HEAD and str(manifest['run_id']) == str(RUN) and str(manifest['run_attempt']) == '1'
        assert manifest['negative_cache_probe']['strict_exit'] == 1
        probes.append({'shard': manifest['shard'], 'probe': manifest['negative_cache_probe']})
    command = [sys.executable, '-B', '.github/scripts/mutation_evidence.py', 'verify',
        '--artifacts', str(OUT / 'extracted/shards'), '--out', str(output)]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    env['PATH'] = '/tmp/geometry-resume-20261102/pr363/node-v24.22.1-linux-x64/bin:' + env['PATH']
    request = {'argv': command, 'cwd': str(SOURCE), 'head': HEAD, 'tree': git('rev-parse', 'HEAD^{tree}'),
        'run': RUN, 'attempt': 1, 'downloaded_binary_execution': False,
        'collector_sha256': sha(Path(__file__)), 'python': sys.version,
        'platform': platform.platform(), 'node': subprocess.check_output(['node', '--version'], env=env, text=True).strip(),
        'environment': {key: env.get(key) for key in ('PATH', 'CC', 'CFLAGS', 'MUTATE_CACHE',
            'MUTATE_RESULTS', 'PYTHONDONTWRITEBYTECODE')},
        'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    write(OUT / 'VERIFY_REQUEST.json', request)
    started = time.monotonic()
    with (OUT / 'verify.stdout').open('wb') as stdout, (OUT / 'verify.stderr').open('wb') as stderr:
        process = subprocess.run(command, cwd=SOURCE, env=env, stdout=stdout, stderr=stderr, check=False)
    result = {'actual_exit': process.returncode, 'elapsed_seconds': time.monotonic() - started,
        'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'stdout_sha256': sha(OUT / 'verify.stdout'),
        'stderr_sha256': sha(OUT / 'verify.stderr'), 'downloaded_elf_executions': 0}
    write(OUT / 'VERIFY_RESULT.json', result)
    assert process.returncode == 0
    official = OUT / 'extracted/other/mutation-complete-evidence'
    for filename in ['mutants_results.json', 'summary.json']:
        assert (output / filename).read_bytes() == (official / filename).read_bytes()
    summary = json.loads((output / 'summary.json').read_text())
    assert summary['head'] == HEAD and summary['table_size'] == 123 and summary['active'] == 120
    assert git('rev-parse', 'HEAD') == HEAD and git('status', '--porcelain=v1') == ''
    write(OUT / 'ACCEPTANCE.json', {'head': HEAD, 'run': RUN, 'attempt': 1, 'source_clean': True,
        'original_verifier_exit': 0, 'summary': summary, 'official_byte_equal': True,
        'zip_count': 9, 'manifest_run_attempt_checked': True, 'negative_probes': probes,
        'native_producer_not_run': True, 'scope': 'Original current-source full-table verifier only; native/browser CI separately bound',
        'downloaded_elf_executions': 0, 'ledger_sha256': sha(output / 'mutants_results.json')})
    print(json.dumps({'head': HEAD, 'run': RUN, 'exit': 0, 'counts': summary['counts'],
        'ledger_sha256': sha(output / 'mutants_results.json'), 'elapsed_seconds': result['elapsed_seconds']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'verify'])
    args = parser.parse_args()
    metadata = prepare()
    if args.mode == 'verify':
        verify(metadata)
    else:
        print(json.dumps({'run': RUN, 'head': HEAD, 'artifact_zip_bytes': metadata['artifact_total_zip_bytes'], 'mode': 'metadata only'}))
