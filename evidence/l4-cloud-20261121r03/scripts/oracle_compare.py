"""R03 L4：把 App 預覽表逐值記下的構件，與 geometry-core/framing-template/oracle 對同一尺寸的輸出逐支比對。

用法：python3 -I oracle_compare.py <repo 根目錄> <walk_r03.phase1.result.json> <輸出 oracle-compare.json>

- App 端只取預覽表（角色、位置矩形、長度、寬×厚）與同列 SVG 的 data-ft-kind；不讀 native 回覆物件。
- oracle 參數與 tests/test_framing_template.py::assert_oracle 相同（P915 L1830 gap2 w27 M367 X8 min_piece27），
  版面由保存的配方偏好換算：lengthAlong v → A='x'；corner 'a-b' → a_start／b_start（同 assert_oracle）。
- 另做三項抽查：主支整支連續、裁切只在對牆（不置中）、RC 邊界四邊都有邊界材。
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

root, result_path, out_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
oracle_path = root / 'geometry-core/framing-template/oracle/framing_oracle.py'
spec = importlib.util.spec_from_file_location('r03_oracle', oracle_path)
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)

R = json.loads(result_path.read_bytes())
outline = R['outline']
recipe = R['recipeSaved']['recipes'][0]
corner, along = recipe['preference']['corner'], recipe['preference']['lengthAlong']
d = recipe['defaults']
starts = corner.split('-')
layout = {'A': 'x' if along == 'v' else 'y', 'a_start': starts[0 if along == 'v' else 1], 'b_start': starts[1 if along == 'v' else 0]}
params = {'P': d['panelWidth'], 'L': d['panelLength'], 'gap': d['gap'], 'w': d['timberWidth'], 'M': d['maxSecondarySpacing'], 'X': 8, 'min_piece': 27}
room = {'outer': outline}
o = oracle.build(room, layout, params)
oracle_check = oracle.check(o, params)

def okind(t):
    return t['kind'] + (':' + t['role'] if t['kind'] == 'secondary' else '')

expected = [{'kind': okind(t), 'rect': list(t['rect']), 'length': max(t['rect'][2] - t['rect'][0], t['rect'][3] - t['rect'][1])} for t in o['timbers']]
app = [{'i': m['i'], 'role': m['role'], 'kind': m['kind'], 'rect': m['rect'], 'length': m['length'], 'AxB': m['AxB']} for m in R['preview1']]
key = lambda m: (m['kind'], tuple(m['rect']), m['length'])
exp_sorted, app_sorted = sorted(map(key, expected)), sorted(map(key, app))
rows = []
# 逐支：App 表的每一列在 oracle 中找同 kind＋同矩形，長度也要相等
pool = list(expected)
for m in app:
    hit = next((e for e in pool if e['kind'] == m['kind'] and e['rect'] == m['rect']), None)
    if hit: pool.remove(hit)
    rows.append({'appRow': m['i'], 'role': m['role'], 'kind': m['kind'], 'appRect': m['rect'], 'appLength': m['length'], 'AxB': m['AxB'],
                 'oracleRect': hit['rect'] if hit else None, 'oracleLength': hit['length'] if hit else None,
                 'match': bool(hit and hit['length'] == m['length'] and m['AxB'] == f"{d['timberWidth']} × {d['timberDepth']}")})
x0, y0 = min(p[0] for p in outline), min(p[1] for p in outline)
x1, y1 = max(p[0] for p in outline), max(p[1] for p in outline)
w = d['timberWidth']
mains = [m for m in app if m['kind'] == 'main']
bnd = [m for m in app if m['kind'] == 'boundary']
rcp = [m for m in app if m['kind'] == 'rc_parallel']
seamsec = [m for m in app if m['kind'] == 'secondary:seam']
# 主支整支連續：每支主支從一側邊界材內緣連到對側邊界材內緣，同一 u 位置只有一支（沒有被切段）
main_cont = {'mains': [m['rect'] for m in mains],
             'eachSpansBoundaryToBoundary': all(m['rect'][1] == y0 + w and m['rect'][3] == y1 - w and m['length'] == (y1 - y0) - 2 * w for m in mains) if along == 'v' else None,
             'oneMemberPerLine': len({m['rect'][0] for m in mains}) == len(mains),
             'oracleMainCount': sum(1 for e in expected if e['kind'] == 'main')}
main_cont['ok'] = bool(main_cont['eachSpansBoundaryToBoundary'] and main_cont['oneMemberPerLine'] and main_cont['oracleMainCount'] == len(mains))
# 封板只在對牆裁切、不置中：由主支中心（u 向板寬縫）與板縫副支中心（v 向板長縫）推回縫位置
useams = sorted((m['rect'][0] + m['rect'][2]) // 2 for m in mains)
vseams = sorted({(m['rect'][1] + m['rect'][3]) // 2 for m in seamsec})
def pieces(lo, hi, seams, gap):
    edges = [lo] + seams + [hi]
    out = []
    for i in range(len(edges) - 1):
        a = edges[i] + (0 if i == 0 else gap // 2 + gap % 2)
        b = edges[i + 1] - (0 if i + 1 == len(edges) - 1 else gap // 2)
        out.append(b - a)
    return out
upieces = pieces(x0, x1, useams, d['gap'])
vpieces = pieces(y0, y1, vseams, d['gap'])
trim = {'uSeamsFromMains': useams, 'uSeamsOracle': sorted(o['seams_a']), 'vSeamsFromSeamSecondaries': vseams, 'vSeamsOracle': sorted(o['seams_b']),
        'uPieces': upieces, 'vPieces': vpieces,
        'note': '起鋪角 min-min：u、v 都從最小座標牆開始；只有最後一片（對牆）可小於整板。置中會讓兩端都是裁片。'}
trim['ok'] = (useams == trim['uSeamsOracle'] and vseams == trim['vSeamsOracle']
              and all(p == d['panelWidth'] for p in upieces[:-1]) and upieces[-1] < d['panelWidth']
              and all(p == d['panelLength'] for p in vpieces[:-1]) and vpieces[-1] < d['panelLength'])
# RC 邊界有邊界材：四邊各一支，貼齊外環
rc = {'boundary': [m['rect'] for m in bnd], 'rcParallel': [m['rect'] for m in rcp]}
rc['ok'] = (sorted(m['rect'] for m in bnd) == sorted([[x0, y0, x1, y0 + w], [x0, y1 - w, x1, y1]]) and
            sorted(m['rect'] for m in rcp) == sorted([[x0, y0 + w, x0 + w, y1 - w], [x1 - w, y0 + w, x1, y1 - w]]))
summary = {'appMembers': len(app), 'oracleMembers': len(expected), 'everyMemberMatches': all(r['match'] for r in rows) and not pool and len(app) == len(expected),
           'multisetEqual': exp_sorted == app_sorted, 'oracleCheckFailures': oracle_check, 'oracleConflicts': o['conflicts'], 'oracleCoreLimits': o['core_limits'],
           'mainContinuous': main_cont['ok'], 'trimOnlyAtOppositeWallNotCentered': trim['ok'], 'rcBoundaryHasBoundaryMembers': rc['ok']}
# 3700 對照：同一 oracle 在 3700×2000 的結果（舊退縫政策可接受），App 應拒絕
o3700 = None
r2 = result_path.parent / 'walk_r03.phase2.result.json'
if r2.exists():
    R2 = json.loads(r2.read_bytes())
    o2 = oracle.build({'outer': R2['outline2']}, layout, params)
    o3700 = {'outline': R2['outline2'], 'oracleMembers': len(o2['timbers']), 'oracleCheckFailures': oracle.check(o2, params), 'oracleSeamsA': sorted(o2['seams_a']), 'oracleSeamsB': sorted(o2['seams_b']),
             'appStatus': R2['reject3700']['status'], 'appConfirmDisabled': R2['reject3700']['confirmDisabled']}
out = {'schema': 'r03-l4-oracle-compare/1',
       'oracle': {'path': str(oracle_path.relative_to(root)), 'repoFileSha256': hashlib.sha256(oracle_path.read_bytes()).hexdigest()},
       'input': {'path': result_path.name, 'sha256': hashlib.sha256(result_path.read_bytes()).hexdigest()},
       'room': room, 'layout': layout, 'params': params, 'recipePreference': recipe['preference'],
       'summary': summary, 'members': rows, 'oracleUnmatched': pool, 'mainContinuity': main_cont, 'trim': trim, 'rcBoundary': rc, 'case3700': o3700}
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False))
sys.exit(0 if all([summary['everyMemberMatches'], summary['multisetEqual'], not oracle_check, summary['mainContinuous'], summary['trimOnlyAtOppositeWallNotCentered'], summary['rcBoundaryHasBoundaryMembers']]) else 1)
