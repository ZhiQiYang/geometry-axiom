#!/usr/bin/env python3
"""把結果檔整理成 README 用的表（只讀結果檔，不改任何檔）。
用法：python3 -I summarize.py <輸出目錄（含 r16/、r03/）>
"""
import json, os, sys

root = sys.argv[1]
r = json.load(open(os.path.join(root, 'r16', 'walk_r16_height.result.json'), encoding='utf-8'))
print('## R16', r['passed'])
print('| 尺寸 | 工作區 | 狀態 | V | 下限 | 可用高度 | 遮蔽 | 控制數 | 中心未命中 | 邊點未命中 | 需捲動 |')
print('|---|---|---|---:|---:|---:|---:|---:|---|---|---|')
for s in r['sizes']:
    for w in s['workspaces']:
        ctl = {'teaching-open': w.get('controlsTeaching') or [], 'normal': w.get('controls') or []}
        for row in w['rows']:
            c = ctl[row['state']]
            miss = [x['selector'] for x in c if not (x['exists'] and x['visible'] and x['centerHit'])]
            edge = [x['selector'] for x in c if x['exists'] and x['visible'] and x['centerHit'] and not x['allPointsHit']]
            scrolled = [f"{x['selector']}" for x in c if x['wheelSteps']]
            print(f"| {s['requested']['width']}×{s['requested']['height']} | {w['label']} | {row['state']} | {row['viewport']['innerHeight']} | {row['minimum']} | {round(row['usableHeight'], 2)} | {len(row['obstructions'])} | {len(c)} | {', '.join(miss) or '—'} | {', '.join(edge) or '—'} | {len(scrolled)} |")
    print(f"<!-- {s['requested']['width']}: faceEnter={s.get('faceEnter', {}).get('via')} spaceEnter={s.get('spaceEnter', {}).get('via')} gridViaDrawer={s.get('gridEntryViaDrawer')} -->")
print('FAILED:', [c['code'] for c in r['checks'] if not c['pass']])
print()
print('## R03')
for it in ['corner-max-min', 'corner-min-max', 'corner-max-max', 'along-u', 'size-2500x3000', 'recipes']:
    for ph in (1, 2):
        p = os.path.join(root, 'r03', f'walk_r03b.{it}.phase{ph}.result.json')
        if not os.path.isfile(p):
            print(it, ph, 'MISSING'); continue
        x = json.load(open(p, encoding='utf-8'))
        extra = ''
        if ph == 1:
            extra = f"head={x.get('preview1Head')} outline={x.get('outline')} saved={x.get('saved', {}).get('bytes')}B {x.get('saved', {}).get('sha256', '')[:12]} redo3v={x.get('threeViewAfterRedo')} gen={x.get('generatorInvocationsBeforeRestart')} pid={x.get('runtimeAtStart', {}).get('pid')}"
        else:
            extra = f"cold3v={x.get('coldThreeView')} gen={x.get('coldGeneratorInvocations')} pid={x.get('runtime', {}).get('pid')}"
        print(it, ph, x['passed'], [c['code'] for c in x['checks'] if not c['pass']], extra)
