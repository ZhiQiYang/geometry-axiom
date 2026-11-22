"""R03 bounded transport; native owns generation, source identity and geometry."""
import json
from pathlib import Path
import re
import tempfile

MAX_BYTES = 1024 * 1024


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('JSON 不得重複欄位')
        value[key] = item
    return value


def _constant(_value):
    raise ValueError('JSON 不接受非有限數值')


def _strings(value):
    if isinstance(value, str):
        if any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError('資料不得含控制字元')
    elif isinstance(value, dict):
        for key, item in value.items():
            _strings(key)
            _strings(item)
    elif isinstance(value, list):
        for item in value:
            _strings(item)


def _u32(value):
    return type(value) is int and 0 <= value <= 4294967295


def _key(value):
    return type(value) is str and re.fullmatch('[a-f0-9]{64}', value) is not None


def request(body, ask_bridge, *, mode):
    """The service owns the private path; no client path reaches the bridge."""
    try:
        if mode not in ('read', 'preview') or type(body) is not bytes or not 0 < len(body) <= MAX_BYTES:
            raise ValueError('需 1 MiB 內完整 read／preview JSON')
        value = json.loads(body.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
        _strings(value)
        version_two = mode == 'read' and type(value) is dict and value.get('schema') == 'framing-template-read/2'
        keys = ({'schema', 'boundaryId', 'template'} if version_two else {'schema', 'boundaryId'}) if mode == 'read' else {
            'schema', 'boundaryId', 'on', 'contextKey', 'definitionFingerprint',
            'expectedRevision', 'template', 'parameters', 'layout', 'material', 'sources'}
        if type(value) is not dict or set(value) != keys or not _u32(value['boundaryId']):
            raise ValueError('需完整明示欄位與 uint32 邊界識別')
        schema = ('framing-template-read/2' if version_two else 'framing-template-read/1') if mode == 'read' else 'framing-template-generate/1'
        if value['schema'] != schema:
            raise ValueError('不支援的配方資料版本')
        if version_two:
            template = value['template']
            if (type(template) is not dict or set(template) != {'id', 'version', 'policyFingerprint'}
                    or template['id'] != 'flat-ceiling' or type(template['version']) is not int
                    or template['version'] != 2 or not _key(template['policyFingerprint'])):
                raise ValueError('read/2 需明選完整的 flat-ceiling/2 版本與政策指紋')
        if mode == 'preview':
            revision = value['expectedRevision']
            if (not _u32(value['on']) or not _key(value['contextKey']) or not _key(value['definitionFingerprint'])
                    or type(revision) is not str or re.fullmatch('0|[1-9][0-9]{0,19}', revision) is None
                    or int(revision) > 18446744073709551615):
                raise ValueError('需明選框架、原生工作區、World 指紋及精確 uint64 版本')
            # Deep definitions are checked by the authoritative C parser.
            # The transport rejects non-object substitutions before any file.
            if any(type(value[key]) is not dict for key in ('template', 'parameters', 'layout', 'material', 'sources')):
                raise ValueError('模板、參數、排向、材料與來源必須是完整物件')
    except (ValueError, UnicodeError, RecursionError, TypeError, KeyError) as error:
        return json.dumps({'ok': False, 'code': 'SCHEMA', 'error': str(error)}, ensure_ascii=False).encode()
    path = None
    try:
        with tempfile.NamedTemporaryFile('wb', suffix='.json', delete=False) as stream:
            stream.write(body)
            path = Path(stream.name)
        return ask_bridge(f'framing-template-{mode} {path}')
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
