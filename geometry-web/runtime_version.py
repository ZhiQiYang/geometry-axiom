"""Source identity and immutable web assets for one local server lifetime."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import sys
import threading
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
RESTART_MESSAGE = '應用程式檔案已更新，這個服務需要重新啟動。請先保存目前專案，再重啟服務並重新整理頁面。'


def source_files(root):
    files = [root / 'current_geometry.c', root / '公理層.md']
    for directory in ('geometry-web', 'geometry-core'):
        for base, dirs, names in os.walk(root / directory):
            dirs[:] = [d for d in dirs if d not in {'__pycache__', 'docs', 'prototypes', 'node_modules', '.git'}]
            for name in names:
                path = Path(base) / name
                if path.suffix in {'.py', '.js', '.mjs', '.wasm', '.css', '.html', '.c', '.h', '.inc', '.ps1', '.bat'}:
                    files.append(path)
    return sorted(p for p in files if p.is_file())


def source_version(root=ROOT):
    digest = hashlib.sha256()
    for path in source_files(root):
        digest.update(path.relative_to(root).as_posix().encode('utf-8') + b'\0')
        content = path.read_bytes()
        if path.suffix != '.wasm':
            content = content.replace(b'\r\n', b'\n')
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()


class RuntimeSnapshot:
    def __init__(self, root=ROOT):
        self.root = root
        self._lock = threading.Lock()
        self._files = self._signature()
        self.version = source_version(root)
        self.assets = {'/' + p.name: p.read_bytes() for p in (root / 'geometry-web').iterdir()
                       if p.is_file() and p.suffix in {'.html', '.js', '.css'}}
        self.vendor = {'/vendor/' + p.relative_to(root / 'geometry-web/vendor').as_posix(): p.read_bytes()
                       for p in (root / 'geometry-web/vendor').rglob('*') if p.is_file()}
        for reference in re.findall(rb'(?:src|href)="([^"]+)"', self.assets['/index.html']):
            path = reference.decode('utf-8')
            if path.endswith(('.js', '.css')) and '/' + path not in self.assets and '/' + path not in self.vendor:
                raise RuntimeError('頁面引用的元件不存在：' + path)
        # Fail startup if an edit raced the capture; never publish a mixed snapshot.
        if source_version(root) != self.version or self._files != self._signature():
            raise RuntimeError('應用程式在啟動期間變更，請重新啟動。')
        self._fresh = True

    def _signature(self):
        return [(str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in source_files(self.root)]

    def fresh(self):
        with self._lock:
            try:
                # File systems can give two same-size writes the same timestamp.
                # Content, rather than mtime, decides whether the runtime is current.
                return source_version(self.root) == self.version
            except OSError:
                return False

    def index(self):
        marker = f'<meta name="geometry-runtime-version" content="{self.version}">'.encode()
        return self.assets['/index.html'].replace(b'<head>', b'<head>\n' + marker, 1)


def probe(port, root=ROOT):
    """Only reuse a server that proves its source identity and repository."""
    with urlopen(f'http://127.0.0.1:{port}/runtime', timeout=5) as response:
        status = json.load(response)
    if (status.get('schema') != 'geometry-runtime/1' or status.get('fresh') is not True
            or status.get('version') != source_version(root)
            or Path(status.get('root', '')).resolve() != root.resolve()):
        raise RuntimeError('既有服務與目前專案版本不符；請先保存專案，再重新啟動服務。')
    return status


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe', type=int, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(probe(args.probe), ensure_ascii=False))
    except Exception as error:
        print('不能沿用目前服務：' + str(error), file=sys.stderr)
        sys.exit(1)
