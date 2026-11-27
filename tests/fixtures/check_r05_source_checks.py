"""以 L467 交付的原生產生器重建，再逐位元組比對；不覆寫版控夾具。"""
import argparse
import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = 'L467/l467-recovered-reproduction/'
BUNDLE_SHA = '0d8b15ca544526b0e3cf3d61483637af5152a0d8476d9a32de73d7326b4afb6c'
FIXTURE_SHA = 'b0aad00d5aa04091f548a469e662b07b702254e16b8d50530ac3d88d21e47bc4'


def signature(data):
    return len(data), hashlib.sha256(data).hexdigest()


def check(bundle):
    raw = bundle.read_bytes()
    if signature(raw) != (429892, BUNDLE_SHA):
        raise ValueError('R05_F4B_EVIDENCE_BUNDLE_PIN')
    with tempfile.TemporaryDirectory(prefix='r05-rebuild-') as directory:
        tmp = Path(directory)
        # 原腳本自建 detached worktree。在臨時的本地 repo 內登記、隨它清除。
        repo = tmp / 'repo.git'
        subprocess.run(['git', 'clone', '--quiet', '--bare', '--shared', str(ROOT), str(repo)], check=True)
        inputs = tmp / 'original-inputs'
        inputs.mkdir()
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:xz') as archive:
            for name in ('reproduce.py', 'consume.js', 'extend_fixture.py'):
                (tmp / name).write_bytes(archive.extractfile(PREFIX + name).read())
            for name in ('native.commands.txt', 'extend-native.commands.txt'):
                (inputs / name).write_bytes(archive.extractfile(PREFIX + name).read())
        # 不解出交付包內的 fixture 或任何 bridge/producer 輸出。
        env = dict(os.environ, TMPDIR=str(tmp))
        for script, log, args in [('reproduce.py', 'native.commands.txt', [repo, tmp]),
                                  ('extend_fixture.py', 'extend-native.commands.txt', [tmp])]:
            subprocess.run([sys.executable, '-B', HERE / 'r05_replay_epochs.py', inputs / log,
                            tmp / script, *args], cwd=tmp, env=env, check=True)
        expected = (HERE / 'r05_source_checks.json').read_bytes()
        actual = (tmp / 'r05_source_checks.json').read_bytes()
        if signature(expected) != (79573, FIXTURE_SHA):
            raise AssertionError('R05_F4B_VERSIONED_FIXTURE_PIN')
        print(f'版控：{signature(expected)}\n重建：{signature(actual)}', flush=True)
        if actual != expected:
            raise AssertionError('R05_F4B_NATIVE_REBUILD_BYTES')
        print('R05_F4B_NATIVE_REBUILD_BYTES：逐位元組相同')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path, help='原始 L467-evidence.tar.xz（見同目錄的 provenance.md）')
    check(parser.parse_args().bundle)
