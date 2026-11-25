"""PF-6 App transport: closed input, exact receipts, server-owned paths.

The native builder remains the only geometry/source evaluator. This adapter
does not expose the CLI's compositional pre/post operations to the App.
"""
import hashlib
import json
from pathlib import Path
import re
import tempfile

MAX_BYTES = 1024 * 1024
UUID = re.compile(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}')


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('JSON 不得重複欄位。')
        value[key] = item
    return value


def _constant(_value):
    raise ValueError('JSON 不接受非有限數值。')


def _strings(value):
    if isinstance(value, str):
        if any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError('資料不得含控制字元。')
    elif isinstance(value, dict):
        for key, item in value.items():
            _strings(key); _strings(item)
    elif isinstance(value, list):
        for item in value:
            _strings(item)


def _u32(value, *, positive=False):
    return type(value) is int and (1 if positive else 0) <= value <= 4294967295


def _u64(value):
    return (type(value) is str and re.fullmatch(r'0|[1-9][0-9]{0,19}', value) is not None
            and int(value) <= 18446744073709551615)


def _uuid(value):
    return type(value) is str and UUID.fullmatch(value) is not None


def _ack(value, request_id, limit):
    if (type(value) is not list or len(value) > limit or any(not _uuid(v) for v in value)
            or len(set(value)) != len(value) or request_id in value):
        raise ValueError('ACK 只接受已處理、互不重複的原請求識別；不得包含本次請求。')
    return value


def receipt_request(headers, body, mode, *, version, session, max_receipts):
    request_id = headers.get('X-Geometry-Request-Id')
    if (headers.get('X-Geometry-Version') != version or headers.get('X-Geometry-Session') != session
            or not _uuid(request_id)):
        raise ValueError('建議角材需要目前版本、服務工作階段及本次請求識別。')
    ack = json.loads(headers.get('X-Geometry-Ack', '[]'), parse_constant=_constant)
    return {'cmd': 'pf6-' + mode + ':' + hashlib.sha256(body).hexdigest(),
            'requestId': request_id, 'session': session, 'ack': _ack(ack, request_id, max_receipts)}


def terminal_request(data, *, version, client_version, session, max_receipts):
    command = data.get('cmd')
    match = re.fullmatch(r'pf6-(confirm|cancel) ([1-9][0-9]{0,9})', command or '')
    if (not match or int(match.group(2)) > 4294967295 or client_version != version
            or not _uuid(data.get('requestId')) or data.get('session') != session
            or not {'cmd', 'requestId', 'session'} <= set(data)
            or set(data) - {'cmd', 'requestId', 'session', 'ack'}):
        raise ValueError('角材確認／取消需要 1…4294967295 的精確候選及原服務的請求回執。')
    _ack(data.get('ack', []), data['requestId'], max_receipts)


def _source(value, field):
    if type(value) is not dict:
        return False
    kind = value.get('kind')
    if kind == 'literal':
        return set(value) == {'kind', 'value'} and type(value['value']) is int and 0 < value['value'] <= 9223372036854775807
    if kind == 'spec':
        return set(value) == {'kind', 'name'} and type(value['name']) is str and bool(value['name'])
    if kind == 'parameter':
        return set(value) == {'kind', 'parameterId', 'fieldId'} and _u32(value['parameterId']) and _u32(value['fieldId'])
    if kind == 'material':
        return (set(value) == {'kind', 'id', 'version', 'field'} and type(value['id']) is str
                and bool(value['id']) and _u32(value['version'], positive=True) and value['field'] == field)
    return False


def request(body, ask_bridge, *, mode):
    try:
        if mode not in ('suggest', 'select') or type(body) is not bytes or not 0 < len(body) <= MAX_BYTES:
            raise ValueError('需 1 MiB 內完整建議／明選 JSON。')
        value = json.loads(body.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
        _strings(value)
        keys = {'schema', 'expectedRevision', 'input', 'pre', 'post'} if mode == 'suggest' else {
            'schema', 'expectedRevision', 'setKey', 'generation', 'selected'}
        if (type(value) is not dict or set(value) != keys
                or value['schema'] != 'panel-fill-builder-' + mode + '/1'
                or not _u64(value['expectedRevision'])):
            raise ValueError('需完整明示欄位及精確 uint64 文字版本。')
        if mode == 'suggest':
            item = value['input']
            if (value['pre'] != [] or value['post'] != [] or type(item) is not dict
                    or set(item) != {'fillId', 'A', 'B', 'roles'} or not _u32(item['fillId'], positive=True)
                    or not _source(item['A'], 'A') or not _source(item['B'], 'B')
                    or item['roles'] not in ({'u': 'primary', 'v': 'secondary'}, {'u': 'secondary', 'v': 'primary'})):
                raise ValueError('請明選正式鋪排、A／B 來源與主副支方向；App 不接受額外 pre／post 操作。')
        elif (type(value['setKey']) is not str or re.fullmatch('[a-f0-9]{64}', value['setKey']) is None
              or not _u64(value['generation']) or type(value['selected']) is not list
              or any(type(key) is not str or not key for key in value['selected'])
              or len(set(value['selected'])) != len(value['selected'])):
            raise ValueError('請保留原提案識別、世代與完整且不重複的明選集合。')
    except (ValueError, UnicodeError, RecursionError, TypeError, KeyError) as error:
        return json.dumps({'ok': False, 'code': 'SCHEMA', 'error': str(error)}, ensure_ascii=False).encode()
    path = None
    try:
        with tempfile.NamedTemporaryFile('wb', suffix='.json', delete=False) as stream:
            stream.write(body); path = Path(stream.name)
        return ask_bridge('pf6-' + mode + ' ' + str(path))
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
