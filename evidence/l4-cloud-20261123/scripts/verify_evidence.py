#!/usr/bin/env python3
"""核對 evidence/l4-cloud-20261123 輸出目錄裡記錄的 SHA-256 與檔案原始位元組相符。

用法：python3 -I verify_evidence.py <輸出目錄>
規則（全部相符 exit 0，否則 exit 1，不靜默略過）：
1. walk_*.result.json 中任何同時含 `file` 與 `sha256` 的物件：<輸出目錄>/<file> 的原始位元組 SHA-256 必須等於 sha256。
2. `saved` 物件（另存結果，含 sha256／bytes）：對應 walk 的 .gcanvas（walk_d06→d06、walk_d09→d09、walk_pf4a→pf4a）必須相符。
3. pdf/manifest.json 中 h-then-line 的 sha256 必須等於 pdf/h-then-line.pdf。
4. 每個 result.json 的 checks 必須全部 pass，且 passed 欄與實際計數一致。
"""
import hashlib, json, os, sys

def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def walk(o, out):
    if isinstance(o, dict):
        if 'file' in o and 'sha256' in o:
            out.append(o)
        for v in o.values():
            walk(v, out)
    elif isinstance(o, list):
        for v in o:
            walk(v, out)

def main(root):
    fails, ok = [], 0
    saved_map = {'walk_d06.result.json': 'd06.gcanvas', 'walk_d09.result.json': 'd09.gcanvas', 'walk_pf4a.result.json': 'pf4a.gcanvas'}
    results = sorted(f for f in os.listdir(root) if f.startswith('walk_') and f.endswith('.result.json'))
    if len(results) != 6:
        fails.append(f'expected 6 result files, got {results}')
    for name in results:
        r = json.load(open(os.path.join(root, name), encoding='utf-8'))
        refs = []
        walk(r, refs)
        for ref in refs:
            p = os.path.join(root, ref['file'])
            if not os.path.isfile(p) or sha(p) != ref['sha256']:
                fails.append(f'{name}: {ref["file"]} mismatch')
            else:
                ok += 1
        if 'saved' in r:
            p = os.path.join(root, saved_map[name])
            if not os.path.isfile(p) or sha(p) != r['saved']['sha256'] or os.path.getsize(p) != r['saved']['bytes']:
                fails.append(f'{name}: saved {saved_map[name]} mismatch')
            else:
                ok += 1
        checks = r.get('checks', [])
        n = sum(1 for c in checks if c.get('pass'))
        if not checks or n != len(checks) or r.get('passed') != f'{n}/{len(checks)}' or r.get('fatal'):
            fails.append(f'{name}: checks {n}/{len(checks)} passed={r.get("passed")} fatal={bool(r.get("fatal"))}')
        else:
            ok += 1
    m = json.load(open(os.path.join(root, 'pdf', 'manifest.json'), encoding='utf-8'))
    if sha(os.path.join(root, 'pdf', 'h-then-line.pdf')) != m['h-then-line']['sha256']:
        fails.append('pdf manifest mismatch')
    else:
        ok += 1
    for f in fails:
        print('FAIL', f)
    print(json.dumps({'ok': ok, 'fail': len(fails)}))
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
