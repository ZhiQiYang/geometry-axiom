"""H-116-VIEW/1 bounded read transport; native owns projection and identity."""
import json
from pathlib import Path
import re
import tempfile

MAX_BYTES = 1024 * 1024
# Same closed World capacity advertised by the native workspace_view capability:
# placements + guides + timbers (R04) + columns/beams. Native tests pin this sum.
MAX_HIDDEN_ROOTS = 16 + 16 + 512 + 2 * 32
MAX_COORD = 400000000
ROOT_KINDS = {'boundary', 'placement', 'guide', 'timber', 'column', 'beam'}
FRAMES = {'front', 'side', 'top', 'bottom'}


def _error(message, pick):
    result = {'ok': False, 'schema': 'workspace-view-pick-result/1' if pick else 'workspace-view-result/1',
              'status': 'INVALID', 'revision': None, 'viewKey': None, 'error': message}
    result.update({'target': None, 'hoverOps': []} if pick else {'layout': None, 'ops': []})
    return json.dumps(result, ensure_ascii=False).encode('utf-8')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('視圖 JSON 不得包含重複欄位')
        result[key] = value
    return result


def _constant(_value):
    raise ValueError('視圖 JSON 不接受非有限數值')


def _strings(value):
    if isinstance(value, str):
        if any(ord(char) < 32 or ord(char) == 127 or 0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise ValueError('視圖字串不得含控制字元或不完整 Unicode')
    elif isinstance(value, list):
        for item in value:
            _strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            _strings(key)
            _strings(item)


def _object(value, keys):
    return type(value) is dict and set(value) == set(keys.split(','))


def _uint32(value):
    return type(value) is int and 0 <= value <= 4294967295


def _validate(data, pick):
    keys = 'schema,expectedRevision,viewKey,viewId,point,radius' if pick else 'schema,expectedRevision,scope,presentation,layers,hidden'
    if not _object(data, keys) or data['schema'] != ('workspace-view-pick/1' if pick else 'workspace-view/1'):
        raise ValueError('視圖需要正確版本及封閉欄位')
    revision = data['expectedRevision']
    if (type(revision) is not str or not re.fullmatch(r'0|[1-9][0-9]{0,19}', revision) or
            int(revision) > 18446744073709551615):
        raise ValueError('來源版本必須是完整 uint64 十進位字串')
    if pick:
        if (type(data['viewKey']) is not str or not re.fullmatch(r'[a-f0-9]{64}', data['viewKey']) or
                type(data['viewId']) is not str or data['viewId'] not in FRAMES or
                not _object(data['point'], 'x,y') or
                not all(type(value) is int and -MAX_COORD <= value <= MAX_COORD for value in data['point'].values()) or
                type(data['radius']) is not int or not 0 <= data['radius'] <= MAX_COORD):
            raise ValueError('拾取需要有效視圖鍵、原生視角及有界整數座標與半徑')
        return
    scope, presentation = data['scope'], data['presentation']
    if not ((_object(scope, 'kind') and scope['kind'] == 'project') or
            (_object(scope, 'kind,id') and scope['kind'] == 'space' and _uint32(scope['id']))):
        raise ValueError('視圖範圍必須是專案或明確空間識別')
    if (not _object(presentation, 'mode,focus') or not (
            presentation['mode'] == 'three' and presentation['focus'] is None or
            presentation['mode'] == 'focus' and type(presentation['focus']) is str and presentation['focus'] in FRAMES)):
        raise ValueError('視圖呈現必須是三視圖或明確單一視角')
    layers = data['layers']
    if (type(layers) is not list or len(layers) > 4 or
            not all(type(item) is str and item in {'face', 'guide', 'timber', 'rc'} for item in layers)):
        raise ValueError('視圖圖層不在支援集合內')
    hidden = data['hidden']
    if type(hidden) is not list or len(hidden) > MAX_HIDDEN_ROOTS:
        raise ValueError('隱藏根超過服務宣告的容量')
    for root in hidden:
        if (not _object(root, 'kind,id') or type(root['kind']) is not str or
                root['kind'] not in ROOT_KINDS or not _uint32(root['id'])):
            raise ValueError('隱藏根需要封閉種類及 uint32 識別')


def file_request(body, ask_bridge, *, pick=False):
    """No caller path is accepted; temporary files are removed on all outcomes."""
    if not isinstance(body, bytes) or not 0 < len(body) <= MAX_BYTES:
        return _error('視圖資料必須是完整位元組，且不得超過 1 MiB', pick)
    try:
        data = json.loads(body.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
        _strings(data)
        _validate(data, pick)
    except (ValueError, UnicodeError, RecursionError) as error:
        return _error(str(error), pick)
    path = None
    try:
        with tempfile.NamedTemporaryFile('wb', suffix='.json', delete=False) as stream:
            stream.write(body)
            path = Path(stream.name)
        return ask_bridge(f'{"view-pick" if pick else "view-read"} {path}')
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
