"""R03 第二片未核對項：App 預覽表逐支 vs geometry-core/framing-template/oracle（同一外環、同一配方偏好）。
改自 evidence/l4-cloud-20261122r03a/scripts/oracle_compare.py；本版不寫死記號，對每個項目各算一次。

用法：python3 -I oracle_compare_r03b.py <repo 根目錄> <輸出目錄>
  讀 <輸出目錄>/walk_r03b.<項目>.phase1.result.json（全部項目），寫 <輸出目錄>/oracle-compare.json。
- App 端只取預覽表（角色、位置矩形、長度、寬×厚）與同列 SVG 的 data-ft-kind。
- 參數與版面換算同 tests/test_framing_template.py::assert_oracle：P915 L1830 gap2 w27 M367 X8 min_piece27；
  lengthAlong v → A='x'，u → A='y'；corner 'a-b' → a_start = starts[0 if v else 1]，b_start = starts[1 if v else 0]。
- 判定：App 支數＝oracle 支數，逐支 (kind, 矩形, 長度) 多重集合相等，寬×厚都是 27 × 33，oracle.check 0 失敗、0 conflicts。
- 另：along-u 項與凍結 golden（oracle-golden.json 的 F4走道，layout 相同者）平移後逐支比較。
任一項不符 exit 1。
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

root, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
oracle_path = root / 'geometry-core/framing-template/oracle/framing_oracle.py'
golden_path = root / 'geometry-core/framing-template/oracle/oracle-golden.json'
spec = importlib.util.spec_from_file_location('r03_oracle', oracle_path)
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)
golden = json.loads(golden_path.read_bytes())
params = {'P': 915, 'L': 1830, 'gap': 2, 'w': 27, 'M': 367, 'X': 8, 'min_piece': 27}

def okind(t):
    return t['kind'] + (':' + t['role'] if t['kind'] == 'secondary' else '')

items, ok_all = {}, True
for f in sorted(out_dir.glob('walk_r03b.*.phase1.result.json')):
    R = json.loads(f.read_bytes())
    item = R['item']
    rec = R['recipeUsed']
    corner, along, d = rec['preference']['corner'], rec['preference']['lengthAlong'], rec['defaults']
    starts = corner.split('-')
    layout = {'A': 'x' if along == 'v' else 'y', 'a_start': starts[0 if along == 'v' else 1], 'b_start': starts[1 if along == 'v' else 0]}
    assert d == {'panelWidth': 915, 'panelLength': 1830, 'gap': 2, 'timberWidth': 27, 'timberDepth': 33, 'maxSecondarySpacing': 367}, d
    room = {'outer': R['outline']}
    o = oracle.build(room, layout, params)
    chk = oracle.check(o, params)
    exp = sorted((okind(t), tuple(t['rect']), max(t['rect'][2] - t['rect'][0], t['rect'][3] - t['rect'][1])) for t in o['timbers'])
    app = sorted((m['kind'], tuple(m['rect']), m['length']) for m in R['preview1'])
    axb = all(m['AxB'] == '27 × 33' for m in R['preview1'])
    res = {'outline': R['outline'], 'preference': rec['preference'], 'layout': layout, 'appMembers': len(app), 'oracleMembers': len(exp),
           'multisetEqual': app == exp, 'allAxB27x33': axb, 'oracleCheckFailures': chk, 'oracleConflicts': o['conflicts'], 'oracleCoreLimits': o['core_limits'],
           'onlyInApp': [list(x) for x in sorted(set(app) - set(exp))][:10], 'onlyInOracle': [list(x) for x in sorted(set(exp) - set(app))][:10],
           'input': {'file': f.name, 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}}
    if item == 'along-u':
        room_g = golden['rooms']['F4走道']
        fx = next((l for l in room_g['layouts'] if l['layout'] == layout), None)
        if fx is None:
            res['frozenGolden'] = {'found': False}
        else:
            gx0 = min(p[0] for p in room_g['room']['outer']); gy0 = min(p[1] for p in room_g['room']['outer'])
            ax0 = min(p[0] for p in R['outline']); ay0 = min(p[1] for p in R['outline'])
            dx, dy = ax0 - gx0, ay0 - gy0
            g = sorted((k, (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy)) for k, r in fx['timbers'])
            a = sorted((m['kind'], tuple(m['rect'])) for m in R['preview1'])
            gdims = [max(p[0] for p in room_g['room']['outer']) - gx0, max(p[1] for p in room_g['room']['outer']) - gy0]
            res['frozenGolden'] = {'found': True, 'room': 'F4走道', 'goldenDims': gdims, 'shift': [dx, dy], 'members': len(g), 'equalAfterShift': a == g}
    ok = res['multisetEqual'] and axb and not chk and not o['conflicts'] and len(app) == R['config']['n'] and (item != 'along-u' or res.get('frozenGolden', {}).get('equalAfterShift') is True)
    res['ok'] = ok
    ok_all = ok_all and ok
    items[item] = res
    print(item, json.dumps({k: res[k] for k in ['appMembers', 'oracleMembers', 'multisetEqual', 'allAxB27x33', 'ok']}, ensure_ascii=False), res.get('frozenGolden', ''))

out = {'schema': 'r03b-l4-oracle-compare/1', 'oracle': {'path': str(oracle_path.relative_to(root)), 'sha256': hashlib.sha256(oracle_path.read_bytes()).hexdigest()},
       'golden': {'path': str(golden_path.relative_to(root)), 'sha256': hashlib.sha256(golden_path.read_bytes()).hexdigest()}, 'params': params, 'items': items, 'ok': ok_all}
(out_dir / 'oracle-compare.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
if len(items) != 6:
    print('FAIL expected 6 items, got', sorted(items)); sys.exit(1)
sys.exit(0 if ok_all else 1)
