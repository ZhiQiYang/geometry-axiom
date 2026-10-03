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
SOURCE_SUFFIXES = {'.py', '.js', '.mjs', '.wasm', '.css', '.html', '.c', '.h', '.inc', '.ps1', '.bat'}
SOURCE_EXCLUDES = {'__pycache__', 'docs', 'prototypes', 'node_modules', '.git'}


def source_files(root):
    files = [p for p in (root / 'current_geometry.c', root / '公理層.md') if p.is_file()]

    def collect(directory):
        # DirEntry retains the file type from enumeration. Avoid a separate stat
        # for every source path (especially costly on Windows).
        try:
            entries = os.scandir(directory)
        except FileNotFoundError:
            return
        with entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    if entry.name not in SOURCE_EXCLUDES:
                        collect(entry.path)
                elif Path(entry.name).suffix in SOURCE_SUFFIXES and entry.is_file():
                    files.append(Path(entry.path))

    for directory in ('geometry-web', 'geometry-core'):
        collect(root / directory)
    return sorted(files)


def _content_version(root, contents):
    digest = hashlib.sha256()
    for path, content in contents:
        digest.update(path.relative_to(root).as_posix().encode('utf-8') + b'\0')
        if path.suffix != '.wasm':
            content = content.replace(b'\r\n', b'\n')
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()


def source_version(root=ROOT):
    return _content_version(root, ((p, p.read_bytes()) for p in source_files(root)))


class RuntimeSnapshot:
    def __init__(self, root=ROOT):
        self.root = root
        self._lock = threading.Lock()
        self._files = self._signature()
        self._source_contents = {p: p.read_bytes() for p in source_files(root)}
        self.version = _content_version(root, self._source_contents.items())
        web = root / 'geometry-web'
        # Fingerprinted assets must use the exact bytes that produced version,
        # rather than rereading a potentially different revision for serving.
        self.assets = {'/' + p.name: content for p, content in self._source_contents.items()
                       if p.parent == web and p.suffix in {'.html', '.js', '.css'}}
        self.vendor = {'/vendor/' + p.relative_to(web / 'vendor').as_posix():
                       self._source_contents[p] if p in self._source_contents else p.read_bytes()
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
                # Read every file on every check; metadata or a TTL cannot safely
                # authorize a mutation. Unchanged bytes need no copies or hashing.
                paths = source_files(self.root)
                if paths != list(self._source_contents):
                    return False
                for path in paths:
                    content = path.read_bytes()
                    original = self._source_contents[path]
                    if content != original and (path.suffix == '.wasm' or
                            content.replace(b'\r\n', b'\n') != original.replace(b'\r\n', b'\n')):
                        return False
                # Also reject a source added/deleted while the files were read.
                return source_files(self.root) == paths
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
