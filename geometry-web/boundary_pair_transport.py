"""Bounded R17 host transport. Native owns allocation, scope and geometry."""
import json
from pathlib import Path
import re
import tempfile

MAX_BYTES = 1024 * 1024


def _error(message):
    return json.dumps({'ok': False, 'code': 'BOUNDARY_PAIR_INPUT', 'error': message},
                      ensure_ascii=False).encode('utf-8')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('JSON 不得包含重複欄位')
        result[key] = value
    return result


def _constant(_value):
    raise ValueError('JSON 不接受非有限數值')


def _strings(value):
    if isinstance(value, str):
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError('成組資料不得包含控制字元')
    elif isinstance(value, list):
        for item in value:
            _strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            _strings(key)
            _strings(item)


def _u32(value):
    return type(value) is int and 0 <= value <= 4294967295


def _key(value):
    return type(value) is str and re.fullmatch(r'[a-f0-9]{64}', value) is not None


def _ids(value):
    return type(value) is list and len(value) == 2 and all(_u32(i) for i in value) and value[0] != value[1]


def request(body, ask_bridge, *, mode):
    """Only this service creates file paths; token routes also support /api receipts."""
    if not isinstance(body, bytes) or not 0 < len(body) <= MAX_BYTES:
        return _error('成組資料須為完整位元組，且不得超過 1 MiB')
    try:
        data = json.loads(body.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
        _strings(data)
        if type(data) is not dict:
            raise ValueError('成組資料須為物件')
        if mode in {'confirm', 'cancel'}:
            if (set(data) != {'schema', 'token', 'ownerKey'} or data['schema'] != 'boundary-pair-token/1'
                    or not _u32(data['token']) or not _key(data['ownerKey'])):
                raise ValueError('確認／取消需要成組 token 與擁有碼')
            return ask_bridge(f'boundary-pair-{mode} {data["token"]} {data["ownerKey"]}')
        if mode not in {'read', 'preview'}:
            raise ValueError('不支援的成組操作')
        keys = {'schema', 'boundaryId'} if mode == 'read' else {
            'schema', 'boundaryId', 'contextKey', 'expectedRevision', 'operation'}
        if (set(data) != keys or not _u32(data.get('boundaryId')) or data['boundaryId'] == 0
                or data.get('schema') != ('boundary-pair-read/1' if mode == 'read' else 'boundary-pair-transaction/1')):
            raise ValueError('成組資料需要正確版本、邊界識別及明確欄位')
        if mode == 'preview':
            revision = data['expectedRevision']
            if (not _key(data['contextKey']) or type(revision) is not str
                    or not re.fullmatch(r'0|[1-9][0-9]{0,19}', revision)
                    or int(revision) > 18446744073709551615):
                raise ValueError('來源版本須為 uint64 十進位字串，並附原生 contextKey')
            operation = data['operation']
            if type(operation) is not dict or operation.get('op') not in {'create', 'redeclare', 'delete'}:
                raise ValueError('只接受新建、完整重宣告或整組刪除')
            op = operation['op']
            expected = {'op', 'on', 'members'} if op == 'create' else (
                {'op', 'on', 'ids', 'members'} if op == 'redeclare' else {'op', 'ids'})
            if set(operation) != expected or op != 'create' and not _ids(operation['ids']):
                raise ValueError('成組操作含缺少或未支援的欄位')
            if op != 'delete':
                members = operation['members']
                if not _u32(operation['on']) or type(members) is not list or len(members) != 2:
                    raise ValueError('新建／重宣告需要同一承載面與恰兩份成員定義')
                for member in members:
                    if (type(member) is not dict or set(member) != {'A', 'B', 'edge', 'direction', 'side'}
                            or any(type(member[k]) is not int or not 0 < member[k] <= 9223372036854775807 for k in ('A', 'B'))
                            or type(member['edge']) is not str or not re.fullmatch(r'e(0|[1-9][0-9]{0,9})', member['edge'])
                            or int(member['edge'][1:]) > 4294967295
                            or member['direction'] not in ('+u', '-u', '+v', '-v') or member['side'] not in ('+n', '-n')):
                        raise ValueError('須明示兩支 boundary 的字面 A/B、外環邊、方向與深度側')
    except (ValueError, UnicodeError, RecursionError, TypeError) as error:
        return _error(str(error))
    path = None
    try:
        with tempfile.NamedTemporaryFile('wb', suffix='.json', delete=False) as stream:
            stream.write(body)
            path = Path(stream.name)
        return ask_bridge(f'boundary-pair-{mode} {path}')
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
