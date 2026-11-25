#!/usr/bin/env python3
"""核對 evidence/l4-cloud-20261123/recheck-main-ea16e3f5 補核輸出（#453 終審後補核）。

用法：python3 -I verify_recheck.py <補核目錄> <原輸出目錄 main-ea16e3f5>
規則（全部相符 exit 0，否則 exit 1）：
1. 三份 result.json（walk_d09_cold390_visible、walk_r11_locate、walk_pf4a_4digit）都在。
2. 其中任何同時含 `file` 與 `sha256` 的物件：<補核目錄>/<file> 原始位元組 SHA-256 必須相符。
3. `input` 物件（補核讀入的 .gcanvas）的 sha256／bytes 必須等於原輸出目錄裡同名檔（d09.gcanvas、pf4a.gcanvas）。
4. checks 全部 pass、passed 欄與實際計數一致、沒有 fatal。
5. runtime-probe.json 與 runtime-probe.after.json 都是 fresh:true 且 version 相同。
"""
import hashlib, json, os, sys

def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def refs(o, out):
    if isinstance(o, dict):
        if 'file' in o and 'sha256' in o:
            out.append(o)
        for v in o.values():
            refs(v, out)
    elif isinstance(o, list):
        for v in o:
            refs(v, out)

def main(root, orig):
    fails, ok = [], 0
    want = {'walk_d09_cold390_visible.result.json': 'd09.gcanvas', 'walk_r11_locate.result.json': None, 'walk_pf4a_4digit.result.json': 'pf4a.gcanvas'}
    for name, gc in want.items():
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            fails.append(f'missing {name}'); continue
        r = json.load(open(p, encoding='utf-8'))
        rs = []; refs(r, rs)
        for ref in rs:
            f = os.path.join(root, ref['file'])
            if os.path.isfile(f) and sha(f) == ref['sha256']: ok += 1
            else: fails.append(f'{name}: {ref["file"]} mismatch')
        if gc:
            g = os.path.join(orig, gc); inp = r.get('input') or {}
            if os.path.isfile(g) and sha(g) == inp.get('sha256') and os.path.getsize(g) == inp.get('bytes'): ok += 1
            else: fails.append(f'{name}: input {gc} mismatch')
        checks = r.get('checks', []); n = sum(1 for c in checks if c.get('pass'))
        if checks and n == len(checks) and r.get('passed') == f'{n}/{len(checks)}' and not r.get('fatal'): ok += 1
        else: fails.append(f'{name}: checks {n}/{len(checks)} passed={r.get("passed")} fatal={bool(r.get("fatal"))}')
    pr = [json.load(open(os.path.join(root, f), encoding='utf-8')) for f in ('runtime-probe.json', 'runtime-probe.after.json')]
    if all(x.get('fresh') is True for x in pr) and pr[0].get('version') == pr[1].get('version'): ok += 1
    else: fails.append('runtime probe not fresh or version differs')
    for f in fails:
        print('FAIL', f)
    print(json.dumps({'ok': ok, 'fail': len(fails)}))
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
