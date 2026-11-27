"""Produce P2053 expected rows from the unchanged independent framing oracle.

No product module, native reply or previous browser output is an input.
Existing oracle goldens and canvas counts are never written by this tool.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / 'geometry-core/framing-template/oracle/framing_oracle.py'
OUT = ROOT / 'tests/fixtures/framing_template_notch_canvas.json'
BASE = '48d5f3887e8cb8d222307db62dbdea287fda8442'
ROOM = [[0, 0], [3740, 0], [3740, 2000], [2500, 2000], [2500, 3301], [0, 3301]]
PARAMETERS = {'P': 915, 'L': 1830, 'gap': 2, 'w': 27, 'M': 367, 'X': 8, 'min_piece': 27}
LAYOUT = {'A': 'x', 'a_start': 'min', 'b_start': 'min'}


def produce():
    spec = importlib.util.spec_from_file_location('r03b_canvas_independent_oracle', ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    result = oracle.build({'outer': ROOM}, LAYOUT, PARAMETERS)
    assert not oracle.check(result, PARAMETERS), 'R03B_FIXTURE_ORACLE_VALID'
    assert not result['conflicts'] and not result['core_limits'], 'R03B_FIXTURE_ORACLE_SUPPORTED'
    members = []
    for item in result['timbers']:
        kind = item['kind'] + (':' + item['role'] if item['kind'] == 'secondary' else '')
        role = item.get('core_role', 'boundary' if item['kind'] == 'boundary'
                        else 'secondary' if item['kind'] == 'secondary' else 'primary')
        priority = item.get('priority', {'boundary': 1, 'primary': 2, 'secondary': 3}.get(role, 0))
        axis = 1 if item['kind'] in ('main', 'rc_parallel') else 0
        rect = item['rect']
        members.append([kind, rect, rect[axis + 2] - rect[axis], role, priority, 27, 33])
    return {'schema': 'framing-template-notch-canvas-fixture/1', 'base': BASE,
            'oracle': {'path': str(ORACLE.relative_to(ROOT)), 'sha256': hashlib.sha256(ORACLE.read_bytes()).hexdigest()},
            'room': ROOM, 'parameters': PARAMETERS, 'layout': LAYOUT,
            'template': {'id': 'flat-ceiling', 'version': 3,
                         'policyFingerprint': '8d734a5128ac6e9e7ed486dbd7f86fc22997bb9a0f38cefd2ad314ecf14f87fc'},
            'expected': {'members': members, 'seams': {'u': sorted(result['seams_a']), 'v': sorted(result['seams_b'])},
                         'marks': sorted({t['at'] for t in result['timbers'] if t['kind'] == 'secondary' and t.get('role') == 'mark'})}}


if __name__ == '__main__':
    raw = (json.dumps(produce(), ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    OUT.write_bytes(raw)
    print(str(OUT.relative_to(ROOT)), len(raw), hashlib.sha256(raw).hexdigest())
