"""T33：用本機 file:// 遠端實測兩段補抓，不占用日常 60 秒契約檢查的時間。"""
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_registry as registry


class FetchDeadline(unittest.TestCase):
    def test_commit_retry_and_unresponsive_blob_share_30_seconds(self):
        def git(repo, *args):
            return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote, client = root / 'remote', root / 'client'
            for repo in (remote, client):
                repo.mkdir()
                git(repo, 'init', '-q')
            (remote / 'sample').write_bytes(b'T33\n')
            git(remote, 'add', 'sample')
            git(remote, '-c', 'user.name=T33', '-c', 'user.email=t33@example.invalid',
                'commit', '-qm', 'T33')
            revision = git(remote, 'rev-parse', 'HEAD')
            git(remote, 'config', 'uploadpack.allowFilter', 'true')
            git(client, 'remote', 'add', 'origin', remote.as_uri())
            git(client, 'config', 'remote.origin.promisor', 'true')
            git(client, 'config', 'remote.origin.partialCloneFilter', 'blob:none')

            # 第一次不回應；第二次只給 commit 與 tree；後續所有 blob 請求都不回應。
            helper = root / 'upload-pack'
            helper.write_text('#!/bin/sh\necho fetch >> "$1/calls"\n'
                              'if [ "$(wc -l < "$1/calls")" -eq 2 ]; then\n'
                              '    exec git-upload-pack "$1"\nfi\nexec sleep 60\n')
            helper.chmod(0o755)
            git(client, 'config', 'remote.origin.uploadpack', shlex.quote(str(helper)))

            start = time.monotonic()
            registry._ensure_git_objects(client, revision)
            commit_time = time.monotonic() - start
            with self.assertRaisesRegex(registry.GitObjectsUnavailable,
                                        r'^R386_NATIVE_BASE_OBJECTS_UNAVAILABLE: 1 blobs .*no answer') as caught:
                registry._ensure_git_objects(client, revision, ['sample'])
            elapsed = time.monotonic() - start
            calls = (remote / 'calls').read_text().splitlines()
            print(f'commit={commit_time:.3f}s; total={elapsed:.3f}s; upload-pack calls={len(calls)}; '
                  f'{caught.exception}', flush=True)
            self.assertGreaterEqual(len(calls), 3)
            self.assertLessEqual(elapsed, 30, 'T33：commit 與 blob 補抓合計超過 30 秒')


if __name__ == '__main__':
    unittest.main()
