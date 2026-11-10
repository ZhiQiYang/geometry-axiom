"""H-116-TIMBER/1 bounded transport; native owns recipes and all geometry."""
import json
from pathlib import Path
import re
import tempfile

MAX_BYTES = 1024 * 1024
MAX_OPERATIONS = 64


def _error(message):
    return json.dumps({'ok': False, 'code': 'TIMBER_INPUT', 'error': message},
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
            raise ValueError('角材資料字串不得含控制字元')
    elif isinstance(value, list):
        for item in value:
            _strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            _strings(key)
            _strings(item)


def _uint32(value):
    return type(value) is int and 0 <= value <= 4294967295


def file_request(body, ask_bridge, *, read=False):
    """The service creates/deletes the file; caller-controlled paths are rejected."""
    if not isinstance(body, bytes) or not 0 < len(body) <= MAX_BYTES:
        return _error('角材資料必須是完整位元組，且不得超過 1 MiB')
    try:
        text = body.decode('utf-8')
        data = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
        _strings(data)
        keys = {'schema', 'boundaryId', 'timberIds'} if read else {
            'schema', 'boundaryId', 'expectedRevision', 'operations'}
        if (type(data) is not dict or set(data) != keys or
                not _uint32(data.get('boundaryId')) or
                data.get('schema') != ('timber-edit-read/1' if read else 'timber-edit-transaction/1')):
            raise ValueError('角材資料需要正確版本、面識別及明確欄位')
        if read:
            ids = data['timberIds']
            if (type(ids) is not list or not 1 <= len(ids) <= MAX_OPERATIONS or
                    not all(_uint32(item) for item in ids) or len(set(ids)) != len(ids)):
                raise ValueError('讀取需要 1–64 個不重複的角材識別')
        else:
            revision = data['expectedRevision']
            if (type(revision) is not str or not re.fullmatch(r'0|[1-9][0-9]{0,19}', revision) or
                    int(revision) > 18446744073709551615):
                raise ValueError('來源版本必須是完整 uint64 十進位字串')
            operations = data['operations']
            if type(operations) is not list or not 1 <= len(operations) <= MAX_OPERATIONS:
                raise ValueError('交易需要 1–64 個操作')
            targets = set()
            for operation in operations:
                if type(operation) is not dict:
                    raise ValueError('角材操作必須是物件')
                if operation.get('op') == 'update-timber-fields':
                    if (set(operation) != {'op', 'id', 'fields'} or not _uint32(operation.get('id')) or
                            operation['id'] in targets or type(operation.get('fields')) is not dict or
                            set(operation['fields']) - {'A', 'B', 'role', 'priority', 'direction'}):
                        raise ValueError('批改只接受不重複角材的明選欄位')
                    targets.add(operation['id'])
                elif operation.get('op') == 'create-from-recipe':
                    if (len(operations) != 1 or set(operation) != {'op', 'recipeKey', 'placement'} or
                            type(operation.get('recipeKey')) is not str or
                            not re.fullmatch(r'[a-f0-9]{64}', operation['recipeKey']) or
                            type(operation.get('placement')) is not dict or
                            set(operation['placement']) != {'on', 'anchor', 'selector', 'direction', 'side'} or
                            not _uint32(operation['placement'].get('on'))):
                        raise ValueError('貼上／重複需要一個原生配方及完整明選落點')
                else:
                    raise ValueError('不支援的角材操作')
    except (ValueError, UnicodeError, RecursionError) as error:
        return _error(str(error))
    path = None
    try:
        with tempfile.NamedTemporaryFile('wb', suffix='.json', delete=False) as stream:
            stream.write(body)
            path = Path(stream.name)
        command = 'timber-edit-read' if read else 'timber-edit-preview'
        return ask_bridge(f'{command} {path}')
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
