from pathlib import Path
import datetime, difflib, hashlib, json

L = '7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
E = '537b4d9c647648f8cdc8d45db3fc0bf5b9386911'
O = Path('/workspace/geo337-all-terminal-status-preparation-20261024')
assert not O.exists()
R = Path('/workspace/geometry-axiom/evidence/geo337-train-20261024')
files = {'geo323/receipt-after-profile.json': Path('/workspace/g337323L/receipt.json'),
         'geo323/performance.json': Path('/workspace/g337323L/evidence/performance.json'),
         'geo323/profile-counts.json': Path('/workspace/g337323L/evidence/profile-counts.json'),
         'memo/original-complete-driver-receipt.json': Path('/workspace/g337323memoL/receipt.json')}
for gate in ('geo323-perf','geo323-profile','memo'):
    base = Path('/workspace/train337-L-'+gate+'-original-launch-20261024')
    for name in ('REQUEST.json','RESULT.json','subcommands.json','subcommands/000001/request.json',
                 'subcommands/000001/result.json','subcommands/000001/stdin.bin',
                 'subcommands/000001/stdout.bin','subcommands/000001/stderr.bin'):
        files[gate+'/outer/'+name] = base/name
raw = {}
for name, p in files.items():
    assert p.is_file() and not p.is_symlink() and p.stat().st_size < 3000000, p
    raw[name] = p.read_bytes()
formal = json.loads(raw['geo323/receipt-after-profile.json'])
memo = json.loads(raw['memo/original-complete-driver-receipt.json'])
assert formal['source_sha'] == memo['sha'] == L
assert list(formal['stages']) == ['prepare','build','compare','perf','profile']
assert [s['execution_exit'] for s in formal['stages'].values()] == [0,0,1,0,0]
for stage in formal['stages'].values():
    assert stage['source_before'] == stage['source_after'] == {'head':L,'status':''}
targets = formal['quantitative_targets']
assert targets['N64_fix_main']['actual'] == 1.4282954375137715 and targets['N64_fix_main']['target_met'] is False
assert targets['geo_eval_source_64_32']['actual'] == 4.407618425509266 and targets['geo_eval_source_64_32']['target_met'] is True
assert formal['wrapper_exit'] == 1 and formal['all_measured_original_targets_met'] is False
assert memo['passed'] is True and memo['exit'] == 0 and memo['errors'] == []
assert [(p['phase'],p['actual_exit']) for p in memo['phases']] == [('withdrawn',1),('restored',0),('abc',0)]
assert all(p['result']['execution_complete'] for p in memo['phases'])
assert memo['phases'][0]['result']['actual'] == 6.053833206336931
assert memo['phases'][1]['result']['actual'] == 4.407618425509266
abc = memo['phases'][2]['result']['ABC_result']
assert abc == {'scenes':175,'runs':350,'failures':[],'original_exit':0,'original_audit_tuple_equal':True}
for gate, code in [('geo323-perf',1),('geo323-profile',1),('memo',0)]:
    d=json.loads(raw[gate+'/outer/RESULT.json']); assert d['source_sha']==L and d['actual_exit']==code

original = {n:(R/(n+'.md')).read_text() for n in ('PROGRESS','QUESTIONS')}
draft = dict(original)
old = '| #323 required-eight／PF3／timing／profile／memo反證 | L | required-eight原exit0／PF3原exit0，完整原件包已封；timing／profile／memo UNRUN | 原676／20-19-20／36timings／4profiles與原門檻；不移標舊F結果 |'
assert draft['PROGRESS'].count(old)==1
draft['PROGRESS']=draft['PROGRESS'].replace(old,
 '| #323 required-eight／PF3 | L | 原exit0／0，完整原件包已封 | 原676混合單位／20-19-20，未移標舊F |\n'
 '| #323原timing | L；baseb74／mainadba | stage execution0／outer CLI1；N64目標false | 原36samples；N16/32/48 fix/base 0.998983／0.811880／0.806587皆≤1，N64 fix/main=1.4282954375>1.3。原CLI1含累積compare紅與數值紅 |\n'
 '| #323原profile | L | stage execution0／outer CLI1；calls比門檻綠 | 原四profiles；N32 82668／N64 364369，ratio4.4076184255≤4.5。累積compare／性能紅未解除 |\n'
 '| #323 whole-memo反證 | L及明示withdrawn/restored變體 | driver／outer0；withdrawn1／restored0／隔離ABC0 | 兩phase execution_complete true；calls比撤回6.0538332063>4.5、恢復4.4076184255≤4.5；隔離175/350與原audit tuple相同，不代跨版本compare1或N64性能紅 |',1)
draft['PROGRESS']=draft['PROGRESS'].replace('沒有 READY-TO-MERGE，B1 完整清單及 B2 原跨版本 exact 尚未解除。',
 '同L正式清單的原終態已收齊；P189／#323 exact、N64性能與required CI仍紅，沒有READY-TO-MERGE。',1)
draft['PROGRESS']=draft['PROGRESS'].replace('## #323同L比較終態與小原收據出版','## 歷史快照：E537僅完成#323 compare時的小收據出版',1)
draft['PROGRESS'] += ('\n## 全部L專項終態已收齊：仍有原比較、性能與CI紅燈\n\n'
 '原#323 prepare/build/compare/perf/profile stage execution為0/0/1/0/0；perf與profile的outer CLI皆1，不能與stage execution0或個別數值目標綠混用。N64fix/main=1.4282954375137715>1.3是真性能門檻紅；N16/32/48對原base皆不變慢，source calls64/32=4.407618425509266≤4.5通過。原36timing與四profile未重取樣，分母與門檻未改。\n\n'
 'memo於02:35:07.864974 UTC真完成，原driver/outer0；撤回1的calls比6.053833206336931>4.5，恢復0的比4.407618425509266，兩phase execution_complete true。memo隔離175/350 ABC原0、原audit tuple一致，仍不解除formal跨版本compare1、P189full1或N64載入性能紅。\n\n'
 '本批final-L-all-terminal-status-only保原13KB formal receipt、performance/profile原JSON、三outer完整小流與原2,877,262B memo driver receipt；沒有摘欄冒原件。完整#323/memo原流與P52/P189三完整封包尚未推送，本小收據不代完整封包。下一步先查N64熱點與做受影響修正／撤回恢復，保原比較紅與QUESTIONS的版本裁決界線，繼續其他已授權工作，不放寬門檻。\n')
draft['QUESTIONS'] += ('\n## Q-323-N64：既定性能門檻紅，無新增門檻決策\n\n'
 '同L原36樣本timing的stage execution0，但N64 fix/main=1.4282954375137715>1.3，target_met=false；outer CLI1另包含累積compare1。N16/32/48 fix/base原三門檻皆true，原四profile的source calls64/32=4.407618425509266≤4.5亦true。memo撤回6.053833206336931>4.5真1、恢復4.407618425509266真0，隔離175/350 ABC0，不代表N64載入時間或跨版本診斷exact已綠。\n\n'
 '本項不要求使用者定新數值。原1.3門檻與分母保留，性能病因待依原profile剖析，不逕歸環境、不挑樣本、不改比較器。可自主進行不改公理／鎖定決策的效能修正，須做撤回／恢復並按影響更新驗收。原B2與P189診斷版本界線另保待裁決，不以這次memo因果證據解除。\n')
body=Path('/workspace/PR_BODY-geo337-compact-awaiting-memo.md').read_text()
assert body.count('__MEMO_FINAL_ROW__')==1
body=body.replace('__MEMO_FINAL_ROW__',
 '| #323 whole-memo撤回／恢復 | 原driver／outer0；withdrawn1／restored0／隔離ABC0 | calls比撤回6.0538332063>4.5、恢復4.4076184255≤4.5；三phase execution_complete true，隔離175/350原audit tuple一致。不解除formal compare1或N64載入性能紅 |',1)
body=body.replace('604輸入與HEAD/index前後一致','604輸入與HEAD/index前後一致；Linux manifest／scan／report／receipt四檔按原schema採用',1)
body=body.replace('六個`final-L-browser-*/`','`final-L-browser-canvas/`、`final-L-browser-assembly/`、`final-L-browser-documents/`、`final-L-browser-grid/`、`final-L-browser-space/`、`final-L-browser-timber/`',1)
body=body.replace('`final-L-section7-{cardref,axiom}/`','`final-L-section7-cardref/`與`final-L-section7-axiom/`',1)
body=body.replace('完整archive未公開的限制不因附PACKAGE或peer JSON而解除。',
 '新`final-L-all-terminal-status-only/`另保formal performance／profile原JSON、完整memo driver receipt與三outer；#323/memo完整原流尚未公開，這些小收據也不代完整封包。完整archive未公開的限制不因附PACKAGE或peer JSON而解除。',1)
assert body.count('### 唯一 current-state 矩陣')==1 and body.count('__NEXT_PERFORMANCE_EVIDENCE_HEAD__')==1
assert '__MEMO_FINAL_ROW__' not in body and 'UNRUN' not in body and 'RUNNING' not in body
O.mkdir();(O/'frozen-originals').mkdir();manifest=[]
for name,data in raw.items():
    p=O/'frozen-originals'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    manifest.append({'name':name,'original_path':str(files[name]),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
for name in draft:
    (O/(name+'.original.md')).write_text(original[name]);(O/(name+'.draft.md')).write_text(draft[name])
    (O/(name+'.diff')).write_text(''.join(difflib.unified_diff(original[name].splitlines(True),draft[name].splitlines(True),fromfile=name+'.original.md',tofile=name+'.draft.md')))
(O/'PR_BODY.compact-final.md').write_text(body)
meta={'source_sha':L,'expected_evidence_head':E,'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'files':manifest,'original_bytes':sum(x['bytes'] for x in manifest),'complete_raw_archives_published':False,
      'original_outer_exits':{'geo323_perf':1,'geo323_profile':1,'memo':0},
      'stage_exits':{'prepare':0,'build':0,'compare':1,'perf':0,'profile':0},
      'memo_phase_exits':{'withdrawn':1,'restored':0,'abc':0},'all_L_specials_terminal':True,
      'remaining_red':['P189_full_exact','geo323_cross_version_exact','geo323_N64_fix_main','required_CI']}
(O/'MANIFEST.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'directory':str(O),'raw_files':len(manifest),'raw_bytes':meta['original_bytes'],
                  'pins':{name:hashlib.sha256((O/name).read_bytes()).hexdigest() for name in ['MANIFEST.json','PROGRESS.draft.md','QUESTIONS.draft.md','PR_BODY.compact-final.md']},
                  'body_bytes':len(body.encode())},ensure_ascii=False))
