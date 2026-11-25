"""Prepare an evidence-only fast-forward candidate in a disposable CI checkout."""
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

REPO = 'ZhiQiYang/geometry-axiom'
BASE_API = 'repos/' + REPO + '/'
PR_BRANCH = 'claude/r16-u123h-apply-20261122'
ME_PATH = '.github/workflows/mutation-evidence.yml'
STORE = '.github/evidence/'
ARCH = STORE + 'architecture/'
SEEDS = {
    'tests/mutants_results.json': '205b18792d436d5fb81613e199f8d9191dfdeece',
    'geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md': 'd67f224bd1c99a5c5eda55809b90e243968e8260',
    'geometry-core/domain-decoupling/product-architecture-receipt.json': '3d069364ed1f7a3d865597f32c1115955d6a57ca',
    'geometry-core/domain-decoupling/product-architecture-scan.json': '902c2bc4a5ce99c996cbb02a792f3159b5800061',
}
REPORT = Path(os.environ['RUNNER_TEMP']) / 'r448-store-receipt'


def require(value, message):
    if not value:
        raise ValueError(message)


def command(*args):
    return subprocess.check_output(args)


def git(*args):
    return command('git', *args).decode().strip()


def api(path):
    return json.loads(command('gh', 'api', BASE_API + path))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    (REPORT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def official_artifact(run_id, source, name, artifacts):
    matches = [row for row in artifacts if row['name'] == name]
    require(len(matches) == 1, 'unique run artifact required: ' + name)
    item = api('actions/artifacts/' + str(matches[0]['id']))
    require(item['name'] == name and item['expired'] is False
            and str(item['workflow_run']['id']) == run_id
            and item['workflow_run']['head_sha'] == source, 'artifact source: ' + name)
    raw = command('gh', 'api', BASE_API + 'actions/artifacts/' + str(item['id']) + '/zip')
    require(item['size_in_bytes'] == len(raw) and item['digest'] == 'sha256:' + sha(raw),
            'artifact bytes: ' + name)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require(archive.testzip() is None, 'ZIP CRC: ' + name)
        members = {}
        for entry in archive.infolist():
            key = PurePosixPath(entry.filename)
            require(not key.is_absolute() and '..' not in key.parts and '\\' not in entry.filename
                    and entry.filename.rstrip('/') == str(key)
                    and not stat.S_ISLNK(entry.external_attr >> 16), 'unsafe ZIP entry: ' + entry.filename)
            if not entry.is_dir():
                require(str(key) not in members, 'duplicate ZIP member: ' + str(key))
                members[str(key)] = archive.read(entry)
    return item, members


def seed_blobs(revision):
    found = {path: git('rev-parse', revision + ':' + path) for path in SEEDS}
    require(found == SEEDS, 'frozen Git seed blob changed at ' + revision)
    for path in SEEDS:
        require(git('hash-object', '--no-filters', path) == found[path], 'worktree seed differs: ' + path)
    return found


def run_check(script, mode, *arguments):
    args = [sys.executable, '-B', '.github/scripts/' + script, mode, '--root', '.', *map(str, arguments)]
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    stem = script.removesuffix('.py') + '-' + mode
    (REPORT / (stem + '.stdout')).write_bytes(result.stdout)
    (REPORT / (stem + '.stderr')).write_bytes(result.stderr)
    if result.returncode:
        print(result.stdout.decode(errors='replace')[-1200:], result.stderr.decode(errors='replace')[-1200:], file=sys.stderr)
    result.check_returncode()
    return json.loads(result.stdout)


def adopt():
    REPORT.mkdir()
    source = os.environ['ME_SOURCE']
    head = os.environ['ADOPT_TARGET']
    run_id = os.environ['ME_RUN_ID']
    require(git('rev-parse', 'HEAD') == head and not git('status', '--porcelain'), 'wrong or dirty target')
    if source != head:
        require(api('compare/' + source + '...' + head)['status'] == 'ahead', 'target does not descend from source')
    seed_before = seed_blobs('HEAD')
    run = api('actions/runs/' + run_id)
    require(run['repository']['full_name'] == REPO and str(run['id']) == run_id
            and run['path'] == ME_PATH and run['status'] == 'completed'
            and run['conclusion'] == 'success' and run['event'] == 'workflow_dispatch'
            and run['head_sha'] == source and run['head_branch'] == PR_BRANCH,
            'run status, branch, workflow or source differs')
    attempt = str(run['run_attempt'])
    jobs = api('actions/runs/' + run_id + '/attempts/' + attempt + '/jobs?per_page=100')
    require(len(jobs['jobs']) == jobs['total_count'] and jobs['total_count'] > 0
            and all(j['status'] == 'completed' and j['conclusion'] == 'success' for j in jobs['jobs']),
            'incomplete mutation jobs or results')
    listing = api('actions/runs/' + run_id + '/artifacts?per_page=100')
    require(listing['total_count'] == len(listing['artifacts']), 'artifact listing is incomplete')
    me, mutations = official_artifact(run_id, source, 'mutation-complete-evidence', listing['artifacts'])
    ae, architecture = official_artifact(run_id, source, 'architecture-repo-evidence', listing['artifacts'])
    save('github-inputs.json', {'run': run, 'jobs': jobs, 'mutations': me, 'architecture': ae})
    require(set(mutations) == {'summary.json', 'mutants_results.json'}, 'unexpected mutation bundle members')
    summary = json.loads(mutations['summary.json'])
    require(summary['head'] == source and summary['binary_bytes_verified'] is True
            and type(summary['full_table_strict_exit']) is int and summary['full_table_strict_exit'] == 0
            and summary['ledger_sha256'] == sha(mutations['mutants_results.json']), 'original supervisor proofs')
    supervisor = sha(Path('.github/scripts/mutation_evidence.py').read_bytes().replace(b'\r\n', b'\n'))
    for shard in summary['shards']:
        require(shard['head'] == source and str(shard['run_id']) == run_id
                and str(shard['run_attempt']) == attempt and shard['supervisor_sha256'] == supervisor,
                'shard origin or supervisor hash differs: ' + shard['shard'])
    with tempfile.TemporaryDirectory(dir=os.environ['RUNNER_TEMP']) as scratch:
        for name, data in mutations.items():
            (Path(scratch) / name).write_bytes(data)
        adoption = run_check('evidence_records.py', 'adopt', '--artifact-dir', scratch)
    require(adoption['origin_head'] == source and adoption['strict_exit'] == 0, 'adoption origin or strict status')
    copied = {}
    parents = {PurePosixPath(key).parent for key in architecture}
    require(len(parents) == 1, 'expected one complete architecture bundle')
    parent = parents.pop()
    require(len(parent.parts) == 2 and all(re.fullmatch('[0-9a-f]{64}', part) for part in parent.parts),
            'architecture directory identities')
    envelope = json.loads(architecture[str(parent / 'bundle.json')])
    require(envelope['inputKey'] == parent.parts[0] and envelope['origin']['sourceHead'] == source
            and str(envelope['origin']['runId']) == run_id and str(envelope['origin']['runAttempt']) == attempt,
            'architecture provenance')
    for key, raw in architecture.items():
        target = Path(ARCH) / key
        copied[str(target)] = sha(raw)
        if target.exists():
            require(not target.is_symlink() and target.is_file() and target.read_bytes() == raw,
                    'existing immutable architecture bytes differ: ' + str(target))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(raw)
    architecture_check = run_check('evidence_architecture.py', 'check')
    require(architecture_check['ok'] and architecture_check['inputKey'] == parent.parts[0]
            and any(o['sourceHead'] == source and str(o['runId']) == run_id
                    and o['receiptSha256'] == parent.parts[1] for o in architecture_check['origins']),
            'current architecture inputs or verified origin differ')
    mutation_check = run_check('evidence_records.py', 'check')
    require(mutation_check['strict_exit'] == 0, 'strict mutation freshness')
    git('add', '--', STORE)
    changed = [str(x, 'utf-8') for x in command('git', 'diff', '--cached', '--name-only', '-z').split(b'\0') if x]
    require(all(p.startswith(STORE) for p in changed) and not git('diff', '--name-only')
            and not git('ls-files', '--others', '--exclude-standard'), 'non-store or unstaged changes')
    require(not git('ls-files', '--others', '--ignored', '--exclude-standard', '--', STORE),
            'ignored evidence file was omitted')
    files = []
    for p in changed:
        data = Path(p).read_bytes()
        line = git('ls-files', '--stage', '--', p).split('\t')[0].split()
        oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        require(line == ['100644', oid, '0'], 'index mode or bytes differ: ' + p)
        files.append({'path': p, 'mode': '100644', 'blob': oid, 'bytes': len(data), 'sha256': sha(data)})
    with zipfile.ZipFile(REPORT / 'changed-files.zip', 'w', compression=zipfile.ZIP_DEFLATED) as changes:
        for item in files:
            changes.write(item['path'], arcname=item['path'])
    tree = git('write-tree')
    candidate = head
    if files:
        branch = 'refs/heads/r448-store-candidate'
        who = ['-c', 'user.name=Codex', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com']
        candidate = git(*who, 'commit-tree', tree, '-p', head, '-m', 'Adopt verified R16 mutation and architecture evidence')
        git('update-ref', branch, candidate)
        bundle = REPORT / 'candidate.bundle'
        git('bundle', 'create', str(bundle), branch, '^' + head)
        git('bundle', 'verify', str(bundle))
        require(git('bundle', 'list-heads', str(bundle)) == candidate + ' ' + branch, 'unexpected bundle ref')
    (REPORT / 'candidate-commit.txt').write_bytes(command('git', 'cat-file', 'commit', candidate))
    require(git('rev-parse', candidate + '^{tree}') == tree, 'candidate tree differs')
    seeds_after = seed_blobs(candidate)
    save('candidate.json', {
        'schema': 'geometry-r448-adoption-candidate/1',
        'source': source, 'target': head, 'candidate': candidate, 'tree': tree,
        'run': run_id, 'attempt': attempt, 'files': files,
        'mutationArtifactId': me['id'], 'mutationArtifactDigest': me['digest'],
        'architectureArtifactId': ae['id'], 'architectureArtifactDigest': ae['digest'],
        'seedBlobsBefore': seed_before, 'seedBlobsAfter': seeds_after,
        'architectureMemberHashes': copied, 'adoption': adoption, 'mutationCheck': mutation_check,
        'architectureCheck': architecture_check,
        'bundleSha256': sha((REPORT / 'candidate.bundle').read_bytes()) if files else None,
    })
    print('候選', candidate, 'tree', tree, '檔數', len(files), '新突變引用', len(adoption['updated']),
          '保留引用', len(adoption['retained']), '架構輸入', architecture_check['inputKey'])


if __name__ == '__main__':
    adopt()
