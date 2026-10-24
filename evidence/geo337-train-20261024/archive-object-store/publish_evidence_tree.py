"""Publish pinned evidence leaves by constructing Git trees, without copying archives.

The current checked-out train advances only through a normal fast-forward merge.
Existing tree entries, modes, product leaves and archived bytes remain unchanged.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re

ROOT = Path('/workspace/geometry-axiom')
BRANCH = 'codex/train-337-continue-20261024'
PREFIX = 'evidence/geo337-train-20261024/'
CAPTURE = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAPTURE_PIN = 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--expected-parent', required=True)
    parser.add_argument('--product-source', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--message', required=True)
    args = parser.parse_args()
    require(all(re.fullmatch('[0-9a-f]{40}', x) for x in
                (args.expected_parent, args.product_source)), 'full source and parent OIDs required')
    raw = args.manifest.read_bytes()
    require(sha(raw) == args.manifest_sha256, 'manifest pin changed')
    manifest = json.loads(raw)
    require(sha(CAPTURE.read_bytes()) == CAPTURE_PIN, 'capture changed')
    require(not args.out.exists(), 'fresh output required')
    args.out.mkdir(parents=True)
    env = dict(os.environ)
    for key in list(env):
        if key.startswith('GIT_'):
            env.pop(key)
    env['GIT_OPTIONAL_LOCKS'] = '0'
    spec = importlib.util.spec_from_file_location('original_capture', CAPTURE)
    cap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cap)
    rec = cap.Recorder(args.out, env, args.product_source)
    result = {'schema': 'geo337-evidence-tree-publication/1',
              'product_source': args.product_source, 'previous_head': args.expected_parent,
              'manifest_sha256': args.manifest_sha256, 'published': False,
              'tool_sha256': sha(Path(__file__).read_bytes())}
    def save():
        (args.out / 'RESULT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    def git(*argv, data=None):
        row, stdout, _ = rec.run(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
                                 *argv], cwd=ROOT, data=data, check=False, timeout=None,
                                source_variant='publish immutable original evidence; product unchanged')
        require(row['actual_process_returncode'] == 0, 'Git failure: ' + row['directory'])
        return stdout
    def oid(data):
        value = data.decode().strip()
        require(re.fullmatch('[0-9a-f]{40}', value), 'invalid OID')
        return value
    def remote():
        lines = git('ls-remote', '--heads', 'origin', 'refs/heads/' + BRANCH).splitlines()
        require(len(lines) == 1, 'missing or ambiguous train ref')
        value, ref = lines[0].split(b'\t')
        require(ref.decode() == 'refs/heads/' + BRANCH, 'wrong remote ref')
        return oid(value)
    save()
    try:
        require(oid(git('rev-parse', 'HEAD')) == args.expected_parent, 'root HEAD moved')
        require(git('branch', '--show-current').decode().strip() == BRANCH, 'wrong train branch')
        require(not git('status', '--porcelain=v1'), 'root not clean')
        require(remote() == args.expected_parent, 'remote differs from parent')
        require(not git('diff', '--name-only', args.product_source, args.expected_parent,
                        '--', '.', ':(exclude)evidence'), 'parent differs from product source')
        entries = {}
        for item in manifest['files']:
            destination = item['destination']
            parts = PurePosixPath(destination).parts
            require(destination.startswith(PREFIX) and '..' not in parts and
                    not destination.startswith('/') and '\x00' not in destination,
                    'destination outside evidence scope')
            require(destination not in entries, 'duplicate destination')
            source = Path(item['source_path'])
            require(source.is_file() and not source.is_symlink(), 'missing original file')
            require(source.stat().st_size == item['bytes'], 'original size changed')
            if 'preloaded_blob' in item:
                blob = item['preloaded_blob']
                require(re.fullmatch('[0-9a-f]{40}', blob), 'invalid preloaded OID')
                require(git('cat-file', '-t', blob).strip() == b'blob', 'preloaded object is not blob')
                require(int(git('cat-file', '-s', blob)) == item['bytes'], 'preloaded size differs')
                # The pinned store receipt includes the full SHA256/Git hash/byte validation.
                proof = Path(item['preload_receipt'])
                require(sha(proof.read_bytes()) == item['preload_receipt_sha256'], 'preload receipt changed')
                proof_data = json.loads(proof.read_bytes())
                identity = proof_data['archive_identity']
                require(proof_data['exit_code'] == 0 and proof_data['alternate_connected'] and
                        proof_data['object_oid'] == blob and identity['sha256'] == item['sha256'] and
                        identity['bytes'] == item['bytes'] and
                        source.stat().st_ino == identity['inode'] and
                        source.stat().st_dev == identity['device'] and
                        source.stat().st_mtime_ns == identity['mtime_ns'], 'preload binding missing')
            else:
                require(sha(source.read_bytes()) == item['sha256'], 'original hash changed')
                blob = oid(git('hash-object', '-w', '--no-filters', '--', str(source)))
                require(sha(source.read_bytes()) == item['sha256'], 'source changed while writing blob')
            entries[destination] = blob
        require(entries, 'empty publication')
        def read_tree(tree_oid):
            rows = {}
            for row in git('ls-tree', '-z', tree_oid).split(b'\0'):
                if row:
                    header, name = row.split(b'\t', 1)
                    mode, kind, obj = header.split(b' ')
                    rows[name.decode()] = (mode, kind, obj)
            return rows
        def update_tree(tree_oid, changes, prefix=''):
            rows = read_tree(tree_oid) if tree_oid else {}
            groups = {}
            for path, blob in changes.items():
                name, sep, tail = path.partition('/')
                groups.setdefault(name, {})[tail if sep else ''] = blob
            for name, group in groups.items():
                old = rows.get(name)
                if '' in group:
                    require(len(group) == 1, 'file/tree collision')
                    require(old is None or (prefix + name == PREFIX + 'PROGRESS.md' and
                                           old[:2] == (b'100644', b'blob')),
                            'would overwrite existing archived evidence')
                    rows[name] = (b'100644', b'blob', group[''].encode())
                else:
                    require(old is None or old[:2] == (b'040000', b'tree'), 'parent is not tree')
                    child = update_tree(old[2].decode() if old else None, group, prefix + name + '/')
                    rows[name] = (b'040000', b'tree', child.encode())
            stream = b''.join(mode + b' ' + kind + b' ' + obj + b'\t' + name.encode() + b'\0'
                              for name, (mode, kind, obj) in rows.items())
            tree = oid(git('mktree', '-z', data=stream))
            require(read_tree(tree) == rows, 'tree reconstruction mismatch')
            return tree
        tree = update_tree(oid(git('rev-parse', args.expected_parent + '^{tree}')), entries)
        commit = oid(git('commit-tree', tree, '-p', args.expected_parent,
                         data=(args.message + '\n').encode()))
        changed = git('diff-tree', '--no-commit-id', '--name-only', '-r', '-z',
                      args.expected_parent, commit).decode().strip('\0').split('\0')
        require(set(changed) == set(entries), 'commit scope differs from manifest')
        require(not git('diff', '--name-only', args.product_source, commit,
                        '--', '.', ':(exclude)evidence'), 'product changed')
        visible = git('sparse-checkout', 'check-rules', '-z',
                      data=b''.join(x.encode() + b'\0' for x in entries))
        require(set(visible.decode().strip('\0').split('\0')) <= {PREFIX + 'PROGRESS.md', ''},
                'large archives would materialize in root checkout')
        require(oid(git('rev-parse', 'HEAD')) == args.expected_parent and
                not git('status', '--porcelain=v1') and remote() == args.expected_parent,
                'HEAD, working tree or remote moved before fast-forward')
        git('merge', '--ff-only', commit)
        require(oid(git('rev-parse', 'HEAD')) == commit and not git('status', '--porcelain=v1'),
                'fast-forward did not leave clean expected root')
        git('push', 'origin', 'HEAD:refs/heads/' + BRANCH)
        require(remote() == commit, 'remote did not reach evidence commit')
        result.update(evidence_head=commit, published=True, push_exit=0,
                      files=len(entries), logical_bytes=sum(x['bytes'] for x in manifest['files']),
                      changed_paths=changed, product_unchanged=True)
    except BaseException as exc:
        result['error'] = repr(exc)
        raise
    finally:
        save()
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
