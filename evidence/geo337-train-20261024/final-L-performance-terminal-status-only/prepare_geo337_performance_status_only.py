from pathlib import Path
import datetime, difflib, hashlib, json

L = '7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
E = '58a75f479fd9c65e71a7827b732ae738b667294e'
O = Path('/workspace/geo337-performance-status-only-preparation-20261024')
assert not O.exists()
OLD = Path('/workspace/geo337-P52-P189-docs-preparation-20261024')
R = Path('/workspace/geometry-axiom/evidence/geo337-train-20261024')
files = {}
def add(name, source):
    files[name] = Path(source)
def outer(gate, target):
    root = Path('/workspace/train337-L-' + gate + '-original-launch-20261024')
    for name in ('REQUEST.json', 'RESULT.json', 'subcommands.json', 'subcommands/000001/request.json',
                 'subcommands/000001/result.json', 'subcommands/000001/stdin.bin',
                 'subcommands/000001/stdout.bin', 'subcommands/000001/stderr.bin'):
        add(target + '/outer/' + name, root / name)
outer('p189', 'p189-full'); outer('p189-timing', 'p189-timing'); outer('geo323-compare', 'geo323-compare')
add('p189-full/driver-receipt.json', '/workspace/g337p189L/receipt.json')
for stream in ('stdout', 'stderr'):
    add('p189-full/original-assertion.' + stream + '.bin', '/workspace/g337p189L/subcommands/000006/' + stream + '.bin')
    for side in ('base', 'fix'):
        add('p189-full/first-mismatch-' + side + '.' + stream, '/workspace/g337p189L/measurement/repo-_role_priority_mutant.scene-' + side + '.' + stream)
add('p189-timing/driver-receipt.json', '/workspace/g337p189L-timing/receipt.json')
for name in ('samples.tsv', 'loadfile-samples.json', 'receipt.json', 'TIMING_ONLY_SCOPE.json', 'summary.txt', 'timing.log'):
    add('p189-timing/measurement/' + name, '/workspace/g337p189L-timing/measurement/' + name)
for stream in ('stdout', 'stderr'):
    add('p189-timing/original-timing.' + stream + '.bin', '/workspace/g337p189L-timing/subcommands/000006/' + stream + '.bin')
add('geo323-compare/receipt-after-compare.json', '/workspace/g337323L/receipt.json')
add('geo323-compare/equivalence.json', '/workspace/g337323L/evidence/equivalence.json')
for gate in ('prepare', 'build'):
    add('geo323-compare/' + gate + '-outer-RESULT.json', '/workspace/train337-L-geo323-' + gate + '-original-launch-20261024/RESULT.json')
for name, folder in (('P52', 'p52-v3'), ('P189', 'p189-v2'), ('P189_TIMING', 'p189-timing-v2')):
    add('local-complete-package-metadata/' + name + '-PACKAGE.json', '/workspace/train337-final-performance-collection-preparation/' + folder + '/PACKAGE.json')
    add('local-complete-package-metadata/' + name + '_ACTUAL_PACKAGE_PEER.json', '/workspace/train337-canvas-peer-resume/' + name + '_ACTUAL_PACKAGE_PEER.json')

raw = {}
for name, source in files.items():
    assert source.is_file() and not source.is_symlink(), source
    assert source.stat().st_size < 400000, source
    raw[name] = source.read_bytes()
    assert not name.endswith('.tar.gz')
receipt = json.loads(raw['geo323-compare/receipt-after-compare.json'])
assert receipt['source_sha'] == L and set(receipt['stages']) == {'prepare', 'build', 'compare'}
assert [receipt['stages'][g]['execution_exit'] for g in ('prepare', 'build', 'compare')] == [0, 0, 1]
assert receipt['wrapper_exit'] == 1 and receipt['quantitative_targets'] == {}
for stage in receipt['stages'].values():
    assert stage['source_before'] == stage['source_after'] == {'head': L, 'status': ''}
eq = json.loads(raw['geo323-compare/equivalence.json'])
assert eq['scenes'] == 175 and len(eq['runs']) == 350
assert eq['failures'] == [['_role_priority_mutant.scene', 'stdout'], ['_s1_p8_l_room_primary_through_reflex_extension.scene', 'stdout'], ['_s1_p8b_l_room_primary_through_reflex_extension_hi.scene', 'stdout']]
for folder, code in (('p189-full', 1), ('p189-timing', 0), ('geo323-compare', 1)):
    d = json.loads(raw[folder + '/outer/RESULT.json'])
    assert d['source_sha'] == L and d['actual_exit'] == code
for name in ('P52', 'P189', 'P189_TIMING'):
    d = json.loads(raw['local-complete-package-metadata/' + name + '_ACTUAL_PACKAGE_PEER.json'])
    assert d['exit_code'] == 0 and d['findings'] == [] and d['source_sha'] == L

original = {'PROGRESS': (R/'PROGRESS.md').read_text(), 'QUESTIONS': (R/'QUESTIONS.md').read_text(),
            'PR_BODY': (OLD/'PR_BODY.original.md').read_text()}
draft = {name: (OLD/(name+'.draft.md')).read_text() for name in original}
def once(name, old, new):
    assert draft[name].count(old) == 1, (name, old)
    draft[name] = draft[name].replace(old, new, 1)
once('PROGRESS', '| #323跨版本175／350 exact | F對原b74 | 1，仍阻擋B2 | 三個I22所需診斷差異，L尚未重跑；未改裁判或刪診斷 |',
     '| #323跨版本175／350 exact | L對原b74 | prepare0／build0／compare1；同L已跑仍紅 | 原175 scenes／350 runs，三個具名stdout差；verify_linux.py:156原assert not failures,failures；來源前後L clean。原ABC_result尚未設定，未冒後續audit或性能已通過 |')
old339 = '- #339 F38da31bc／Ee9ee6d08／De1b5b171 已一般推送：真M1f0架構3綠、mutate check1（107stale／13unrun）；11正式項3PASS／1RED／7UNRUN，舊S57的142與3反證不移標新F。'
once('PROGRESS', old339,
     '- #339 歷史快照Ee9ee6d08／De1b5b171：三架構0、mutate check1（107stale／13unrun）；舊S57結果不移標。後續同F38da的142及三組反證已公開於E1d94ab77ab29952d5b73ec5b262dfd239819fe25／D71113ce739f6fe7c327b162e47e6fd7dba349824；正式11項仍3PASS／1RED／7UNRUN。最新各線來源與owner見handoff 2e7963d3的handoff/NEXT.md，不把本歷史段落當current矩陣。')
once('PR_BODY', '| #323 跨版本 175 場景／350 組 exact | L | **UNRUN** | 原 comparator 保留；下列歷史 exit1 仍是 B2，未獲裁決前不能宣稱解除 |',
     '| #323 跨版本175場景／350組exact | L對原base b74f9a2 | **原prepare0／build0／compare1；已跑仍紅** | 原175 scenes／350 runs，三個具名stdout差；verify_linux.py:156原assert，前後同L clean。ABC_result未設定，不冒後續audit或性能通過；完整流待推 |')

for name in ('PROGRESS', 'PR_BODY'):
    draft[name] = draft[name].replace('完整流包待封', '完整原件包已在雲端核對、待推送')
    draft[name] = draft[name].replace('完整流包待', '完整原件包已在雲端核對、待推送')
    draft[name] = draft[name].replace('原流目前雲端待封', '小原收據已公開，完整原件包雲端已核、待推送')
    draft[name] = draft[name].replace('原流雲端待封', '小原收據已公開；完整原件包雲端已核、待推送')
    draft[name] = draft[name].replace('完整原件目前雲端待封', '小原收據已公開；完整原件包雲端已核、待推送')
    draft[name] = draft[name].replace('第一次collector因Chrome SingletonCookie symlink退出1，屬收件工具假設，正在v2處理symlink/socket記錄，完整原raw保留，沒有重跑產品。',
        'collector先因Chrome IPC、再因原ledger附加欄位各退出1，兩次工具失敗均保留；v3已封完整包並核對13496/0，原產品沒有重跑。45個IPC只存metadata，65項原annotation保留，六個ELF只省包內payload；完整包待推送。')
    draft[name] = draft[name].replace('首次完整collector因Chrome SingletonCookie symlink退出1，屬收件工具，v2只處理symlink/socket封存；完整失敗與原raw保留，不能將工具1混成產品紅，也不能把產品0當完整包已公開。',
        'collector因Chrome IPC與原ledger附加欄位先後兩次退出1，原工具失敗與raw保留；v3完整包已核13496/0，45個IPC只存metadata、65項annotation保留，六個ELF只省包內payload。工具1不是產品紅，完整包仍待推送。')

compare_note = ('同L #323原prepare0／build0／compare1已真完成；equivalence.json記175 scenes／350 runs，差異僅列`_role_priority_mutant.scene`、`_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`三個stdout。原`verify_linux.py:156`的`assert not failures,failures`拋出；ABC_result尚未設定、quantitative_targets為空，不能冒完整後續audit四元組或性能已通過。前後來源同L且clean；perf／profile／memo仍UNRUN，原比較器未改，B2未解除。')
draft['PROGRESS'] += '\n## #323同L比較終態與小原收據出版\n\n' + compare_note + '\n\n本批final-L-performance-terminal-status-only只公開P189兩原終態／assertion與首次差異streams、timing原36表／receipt／scope，以及#323比較後receipt／equivalence與outer；三份已完成完整包仍在雲端，沒有壓縮或入Git。P52／P189full／timing的actual核對為13496／14330／1457各0，不當產品測試；產品結果仍為0／1／0。\n'
draft['PR_BODY'] += '\n' + compare_note + '\n\n本次`final-L-performance-terminal-status-only`保存原小收據及assertion輸出；P52／P189full／timing完整原件包均已在雲端封存且獨立13496／14330／1457核對0，但尚未推送，不能把metadata或peer JSON當成完整tar已公開。產品退出碼仍分別為0／1／0，B1／B2／B3未全解除，維持draft。\n'
anchor = '\n## Q-P189-EXACT：同族I22診斷差異，保原正式紅燈'
once('QUESTIONS', anchor, '\n本輪L正式重跑更新：' + compare_note + '\n' + anchor)
assert draft['PR_BODY'].count('### 唯一 current-state 矩陣') == 1
assert draft['PR_BODY'].count('__NEXT_PERFORMANCE_EVIDENCE_HEAD__') == 1
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
O.mkdir(); (O/'frozen-originals').mkdir()
manifest = []
for name, data in raw.items():
    dest = O/'frozen-originals'/name; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
    manifest.append({'name':name,'original_path':str(files[name]),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
for name in original:
    (O/(name+'.original.md')).write_text(original[name]); (O/(name+'.draft.md')).write_text(draft[name])
    (O/(name+'.diff')).write_text(''.join(difflib.unified_diff(original[name].splitlines(True),draft[name].splitlines(True),fromfile=name+'.original.md',tofile=name+'.draft.md')))
meta = {'source_sha':L,'expected_evidence_head':E,'captured_at':now,'files':manifest,
        'small_original_bytes':sum(x['bytes'] for x in manifest),'complete_raw_archives_published':False,
        'original_exits':{'p52':0,'p189_full':1,'p189_timing':0,'geo323_prepare':0,'geo323_build':0,'geo323_compare':1},
        'unrun':['geo323_perf','geo323_profile','memo'],'source_unchanged':True}
(O/'MANIFEST.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'directory':str(O),'file_count':len(manifest),'small_original_bytes':meta['small_original_bytes'],
                  'docs':{n:hashlib.sha256((O/(n+'.draft.md')).read_bytes()).hexdigest() for n in original}},ensure_ascii=False))
