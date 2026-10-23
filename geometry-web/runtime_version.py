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


def application_assets(root):
    """Fixed composition assets; no arbitrary template or repository routing."""
    return {
        '/templates/woodworking.js': root / 'geometry-templates/woodworking/frontend.js',
        '/application.js': root / 'geometry-app/application.js',
    }


def static_catalog(root):
    """Existing explicit public documents/examples, never user project files."""
    web = root / 'geometry-web'
    return {
        '/documents/finish': root / 'geometry-guide/docs/finish-surface-dependencies.md',
        '/documents/vision': root / 'geometry-guide/PRODUCT-VISION.md',
        '/documents/guide': web / 'docs/DOCUMENTS.md',
        '/documents/engineering': web / 'docs/ENGINEERING-SPEC-USE.md',
        '/axioms': root / 'geometry-guide/公理層-閱讀器.html',
        **{'/examples/' + name: web / 'examples' / name for name in (
            'engineering-spec-v1.gcanvas', 'assembly-rules-v1.gcanvas',
            'assembly-generation-v1.gcanvas')},
    }


def _tracked_suffix(name):
    # 保留 Path(name).suffix 的已追蹤型別判定，包含 ..py 這類名稱。
    # 每次新鮮度檢查會完整列舉兩次；不必為了排除副檔名另建 Path。
    dot = name.rfind('.')
    return name[dot:] if 0 < dot < len(name) - 1 else ''


def static_files(root):
    """One route allowlist for capture, identity and HTTP serving."""
    web = root / 'geometry-web'
    routes = {'/': web / 'index.html', '/index.html': web / 'index.html'}
    with os.scandir(web) as entries:
        for entry in entries:
            if _tracked_suffix(entry.name) in {'.js', '.css'} and entry.is_file():
                routes['/' + entry.name] = Path(entry.path)

    def vendor(directory, prefix=''):
        try:
            entries = os.scandir(directory)
        except FileNotFoundError:
            return
        with entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    vendor(entry.path, prefix + entry.name + '/')
                elif entry.is_file():
                    routes['/vendor/' + prefix + entry.name] = Path(entry.path)

    # Match the existing vendor routes, including file symlinks, every suffix
    # and LICENSE files. Directory symlinks were not traversed by rglob either.
    vendor(web / 'vendor')
    routes.update(application_assets(root))
    routes.update(static_catalog(root))
    return routes


def source_files(root, routes=None, known_files=None):
    """Enumerate current sources; known_files is the immutable sorted snapshot.

    Reuse its paths and order only after verifying the complete current set.
    File types, contents and the directory listing are never cached here.
    """
    files = [p for p in (root / 'current_geometry.c', root / '公理層.md') if p.is_file()]
    known_paths = {} if known_files is None else {str(path): path for path in known_files}

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
                elif _tracked_suffix(entry.name) in SOURCE_SUFFIXES and entry.is_file():
                    path = known_paths.get(entry.path)
                    files.append(Path(entry.path) if path is None else path)

    for directory in ('geometry-web', 'geometry-core', 'geometry-kernel', 'geometry-app', 'geometry-templates'):
        collect(root / directory)
    found = set(files) | set((static_files(root) if routes is None else routes).values())
    if known_files is not None and found == known_files.keys():
        return list(known_files)
    return sorted(found)


def _identity_content(root, path, content):
    web = root / 'geometry-web'
    # Public bytes are the runtime artifact, even when a file is textual. Only
    # non-served source text may ignore checkout line endings. In particular,
    # archives, fonts, CMaps, images and unknown vendor types are always binary.
    if (path.is_relative_to(web / 'vendor') or path in static_catalog(root).values()
            or path in application_assets(root).values()
            or path.parent == web and path.suffix in {'.html', '.js', '.css'}):
        return content
    if path.suffix in SOURCE_SUFFIXES - {'.wasm'} or path == root / '公理層.md':
        return content.replace(b'\r\n', b'\n')
    return content


def _content_version(root, contents):
    digest = hashlib.sha256()
    for path, content in contents:
        digest.update(path.relative_to(root).as_posix().encode('utf-8') + b'\0')
        digest.update(hashlib.sha256(_identity_content(root, path, content)).digest())
    return digest.hexdigest()


def source_version(root=ROOT):
    return _content_version(root, ((p, p.read_bytes()) for p in source_files(root)))


class RuntimeSnapshot:
    def __init__(self, root=ROOT):
        self.root = root
        self._lock = threading.Lock()
        self._routes = static_files(root)
        paths = source_files(root, self._routes)
        self._files = self._signature(paths)
        self._source_contents = {p: p.read_bytes() for p in paths}
        self.version = _content_version(root, self._source_contents.items())
        web = root / 'geometry-web'
        # Fingerprinted assets must use the exact bytes that produced version,
        # rather than rereading a potentially different revision for serving.
        self.assets = {'/' + p.name: content for p, content in self._source_contents.items()
                       if p.parent == web and p.suffix in {'.html', '.js', '.css'}}
        self.assets.update({route: self._source_contents[path]
                            for route, path in application_assets(root).items()})
        self.static = {route: self._source_contents[path] for route, path in self._routes.items()}
        self.vendor = {route: content for route, content in self.static.items()
                       if route.startswith('/vendor/')}
        for reference in re.findall(rb'(?:src|href)="([^"]+)"', self.assets['/index.html']):
            path = reference.decode('utf-8')
            route = '/' + path.lstrip('/')
            if path.endswith(('.js', '.css')) and route not in self.assets and route not in self.vendor:
                raise RuntimeError('頁面引用的元件不存在：' + path)
        # Fail startup if an edit raced the capture; never publish a mixed snapshot.
        if (static_files(root) != self._routes or source_version(root) != self.version
                or self._files != self._signature()):
            raise RuntimeError('應用程式在啟動期間變更，請重新啟動。')
        self._fresh = True

    def _signature(self, paths=None):
        return [(str(p), p.stat().st_mtime_ns, p.stat().st_size)
                for p in (source_files(self.root) if paths is None else paths)]

    def fresh(self):
        with self._lock:
            try:
                # File systems can give two same-size writes the same timestamp.
                # Read every file on every check; metadata or a TTL cannot safely
                # authorize a mutation. Unchanged bytes need no copies or hashing.
                routes = static_files(self.root)
                if routes != self._routes:
                    return False
                paths = source_files(self.root, routes, self._source_contents)
                if paths != list(self._source_contents):
                    return False
                for path in paths:
                    content = path.read_bytes()
                    original = self._source_contents[path]
                    if content != original and (_identity_content(self.root, path, content)
                            != _identity_content(self.root, path, original)):
                        return False
                # Also reject a source added/deleted while the files were read.
                final_routes = static_files(self.root)
                return final_routes == routes and source_files(self.root, final_routes, self._source_contents) == paths
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
