"""Server-owned, bounded, read-only snapshot indexing; no model rebuild."""
from pathlib import Path
import json
import tempfile

MAX_BYTES = 1024 * 1024


def snapshot_request(body, ask_bridge):
    if not isinstance(body, bytes) or len(body) > MAX_BYTES:
        return json.dumps({'ok': False, 'code': 'CAPACITY', 'error': '來源快照上限為 1 MiB。'}).encode()
    try:
        text = body.decode('utf-8')
        if '\0' in text:
            raise ValueError('來源快照不得含 NUL。')
    except (UnicodeError, ValueError):
        return json.dumps({'ok': False, 'code': 'ENCODING', 'error': '來源快照須為完整 UTF-8。'}).encode()
    path = None
    try:
        with tempfile.NamedTemporaryFile('wb', suffix='.scene', delete=False) as stream:
            path = Path(stream.name)
            stream.write(body)
        return ask_bridge('source-inspect-file ' + str(path))
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
