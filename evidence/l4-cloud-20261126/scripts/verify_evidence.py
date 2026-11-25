#!/usr/bin/env python3
"""核對 evidence/l4-cloud-20261126 輸出目錄的原件完整性，並列出核對項結果。

用法：python3 -I verify_evidence.py <輸出目錄（含 r16/、r03/）>
結束碼：0＝完整性全部相符且所有核對項 PASS；1＝完整性有任何不符（雜湊、檔案、計數、probe）；2＝完整性相符，但有核對項 FAIL（逐項列出）。
完整性規則（不靜默略過）：
1. 每個 result.json 中同時含 `file` 與 `sha256` 的物件：<結果檔所在目錄>/<file> 原始位元組 SHA-256 必須相符。
2. R03 第一階段 `saved`（sha256／bytes）必須等於 r03/<項目>.gcanvas；第二階段 `fileSha256AtOpen` 也必須等於它。
3. 每個 result.json 的 `passed` 必須等於 checks 的實際計數；不得有 fatal。
4. 所有 runtime-probe*.json 都是 fresh:true，且 version 全部相同。
5. 結果檔數：r16 1 份；r03 每個項目第一、二階段各 1 份（共 12 份）；oracle-compare.json 的 ok 為 true。
"""
import hashlib, json, os, sys

ITEMS = ['corner-max-min', 'corner-min-max', 'corner-max-max', 'along-u', 'size-2500x3000', 'recipes']

def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def refs(o, out):
    if isinstance(o, dict):
        if 'file' in o and 'sha256' in o and isinstance(o['file'], str) and o['file'].startswith('screens/'):
            out.append(o)
        for v in o.values():
            refs(v, out)
    elif isinstance(o, list):
        for v in o:
            refs(v, out)

def main(root):
    bad, ok, failed_checks = [], 0, []
    def load(p):
        return json.load(open(p, encoding='utf-8'))
    results = [os.path.join(root, 'r16', 'walk_r16_height.result.json')]
    results += [os.path.join(root, 'r03', f'walk_r03b.{i}.phase{ph}.result.json') for i in ITEMS for ph in (1, 2)]
    for p in results:
        if not os.path.isfile(p):
            bad.append(f'missing {p}'); continue
        r = load(p); d = os.path.dirname(p); name = os.path.relpath(p, root)
        rs = []; refs(r, rs)
        for ref in rs:
            f = os.path.join(d, ref['file'])
            if os.path.isfile(f) and sha(f) == ref['sha256']:
                ok += 1
            else:
                bad.append(f'{name}: {ref["file"]} mismatch')
        checks = r.get('checks', [])
        n = sum(1 for c in checks if c.get('pass'))
        if not checks or r.get('passed') != f'{n}/{len(checks)}' or r.get('fatal'):
            bad.append(f'{name}: passed={r.get("passed")} actual={n}/{len(checks)} fatal={bool(r.get("fatal"))}')
        else:
            ok += 1
        failed_checks += [f'{name}: {c["code"]}' for c in checks if not c.get('pass')]
        if r.get('phase') == '1':
            g = os.path.join(d, f'{r["item"]}.gcanvas')
            if os.path.isfile(g) and sha(g) == r['saved']['sha256'] and os.path.getsize(g) == r['saved']['bytes']:
                ok += 1
            else:
                bad.append(f'{name}: saved {r["item"]}.gcanvas mismatch')
        if r.get('phase') == '2':
            p1 = load(os.path.join(d, f'walk_r03b.{r["item"]}.phase1.result.json'))
            if r.get('fileSha256AtOpen') == p1['saved']['sha256']:
                ok += 1
            else:
                bad.append(f'{name}: cold-open file sha differs from saved')
    versions = set()
    for sub in ('r16', 'r03'):
        for f in sorted(os.listdir(os.path.join(root, sub))):
            if f.startswith('runtime-probe') and f.endswith('.json'):
                pr = load(os.path.join(root, sub, f))
                versions.add(pr.get('version'))
                if pr.get('fresh') is True:
                    ok += 1
                else:
                    bad.append(f'{sub}/{f}: not fresh')
    if len(versions) != 1:
        bad.append(f'runtime versions differ: {sorted(map(str, versions))}')
    oc = os.path.join(root, 'r03', 'oracle-compare.json')
    if os.path.isfile(oc) and load(oc).get('ok') is True and sorted(load(oc)['items']) == sorted(ITEMS):
        ok += 1
    else:
        bad.append('r03/oracle-compare.json not ok')
    for b in bad:
        print('FAIL', b)
    for c in failed_checks:
        print('CHECK-FAIL', c)
    print(json.dumps({'integrityOk': ok, 'integrityFail': len(bad), 'checkFail': len(failed_checks), 'runtimeVersion': sorted(map(str, versions))}))
    return 1 if bad else (2 if failed_checks else 0)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
