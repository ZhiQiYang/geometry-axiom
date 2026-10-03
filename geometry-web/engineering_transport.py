"""Bounded, server-owned file transport to the authoritative engineering core."""
import json
from pathlib import Path
import tempfile

MAX_BYTES = 1024 * 1024


def _error(message):
    return json.dumps({'ok': False, 'code': 'ENGINEERING_INPUT', 'error': message},
                      ensure_ascii=False).encode('utf-8')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('JSON 不得包含重複欄位')
        result[key] = value
    return result


def _constant(value):
    raise ValueError('JSON 不接受非有限數值')


def file_request(body, ask_bridge, *, validate_scene=False, assembly=False, generation=False):
    """No caller-provided paths, rewritten dimensions, or catalog authority here."""
    if not isinstance(body, bytes) or len(body) > MAX_BYTES:
        return _error('工程資料必須是完整位元組，且不得超過 1 MiB')
    if not validate_scene and not body:
        return _error('工程交易不得為空')
    try:
        text = body.decode('utf-8')
        if '\0' in text:
            raise ValueError('工程資料不得含 NUL')
        if not validate_scene:
            data = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
            if (not isinstance(data, dict) or set(data) - {'schema', 'operations', 'expectedRevision'}
                    or data.get('schema') != ('assembly-generation-transaction/1' if generation else 'assembly-transaction/1' if assembly else 'engineering-transaction/1')
                    or not isinstance(data.get('operations'), list)
                    or not 1 <= len(data['operations']) <= 256
                    or type(data.get('expectedRevision')) is not int or data['expectedRevision'] < 0):
                raise ValueError('工程交易需要正確版本、1–256 個操作及預覽來源版本')
    except (ValueError, UnicodeError) as error:
        return _error(str(error))
    command = 'engineering-validate' if validate_scene else ('assembly-generation-preview' if generation else 'assembly-preview' if assembly else 'engineering-preview')
    path = None
    try:
        with tempfile.NamedTemporaryFile('wb', suffix='.scene' if validate_scene else '.json', delete=False) as stream:
            stream.write(body)
            path = Path(stream.name)
        return ask_bridge(f'{command} {path}')
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
