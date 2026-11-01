"""Source-only, reviewed witness migration from an already-recorded observation.
Does not import/execute the oracle, generator, self-test or scan.
"""
from pathlib import Path
import ast, hashlib, json, shutil, subprocess
root=Path('/workspace/geo318-reading-a-work');prep=Path('/workspace/geo318-reading-a-prep')
oracle=root/'geometry-core/framing-template/oracle';evidence=root/'evidence/issue318-reading-a-20261023'
source=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
assert source=='2039b477a9669a9e3fcaad740283605b8de8a8f4',source
observation=json.loads((prep/'observation-small.json').read_text())
assert observation['sha']==source and observation['dirty']==''
rows=observation['rows'];cur,withdrawn=rows[:2]
assert (cur['room'],cur['layout'],cur['policy'])==('FZ120','左上起鋪,板長沿Y','current')
assert cur['verdict']=='core_limited' and not cur['problems'] and not cur['conflicts']
unchanged=['timbers','seams_a','seams_b','p182','conflicts','problems']
assert all(cur[k]==withdrawn[k] for k in unchanged)
assert [(c['code'],c['id'],c['end']) for c in cur['core_limits']]==[('CORE_LIMIT_EXTENSION_END_FREE',1,1000)]
assert [(c['code'],c['id'],c['end']) for c in withdrawn['core_limits']]==[('CORE_LIMIT_BOUNDARY_END_FREE',3,1000),('CORE_LIMIT_EXTENSION_END_FREE',1,1000)]
# This literal is the pre-existing FZ120 hand-computed room, not new observed geometry.
room={'outer':[[0,0],[4100,0],[4100,3672],[1450,3672],[1450,3720],[1000,3720],[1000,3675],[0,3675]]}
byid={t['id']:t for t in cur['timbers']}
assert byid[1]['rect']==[1000,3645,4100,3672] and byid[1]['ext']==[[1000,1450]]
assert byid[3]['rect']==[0,3648,1000,3675]
# Same kind-label projection as the reviewed existing make_golden.layout_record.
def label(t):
 if t['kind']=='rc_parallel' and t.get('core_role')=='custom':return 'rc_parallel:custom'
 result='secondary:'+t['role'] if t['kind']=='secondary' else t['kind']
 if t.get('core_role')=='custom':result+=f":custom{t['priority']}"
 return result
want=['CORE_LIMIT_EXTENSION_END_FREE',1,1000,[1000,3645,4100,3672]]
layout={'layout':{'A':'x','a_start':'min','b_start':'min'},'name':'左上起鋪,板長沿Y','buildable':True,'conflict_codes':[],'core_limits':[want],'seams_a':sorted(cur['seams_a']),'seams_b':sorted(cur['seams_b']),'timbers':sorted([label(t),t['rect']] for t in cur['timbers'])}
assert layout['timbers'][1][1]!=want[3] and layout['timbers'][2][1]==want[3]
golden_path=oracle/'oracle-golden.json';before=golden_path.read_bytes();golden=json.loads(before)
old=golden['core_limit_witness'];step=rows[7]
assert step['room']=='STEP20' and step['verdict']=='buildable' and not step['core_limits']
assert old['layouts'][0]['timbers']==sorted([label(t),t['rect']] for t in step['timbers'])
assert all(old['layouts'][0][k]==step[k] for k in ('seams_a','seams_b'))
golden['core_limit_witness']={'room_name':'例:FZ120(I22 延伸段非空見證)','room':room,'layouts':[layout]}
golden_path.write_text(json.dumps(golden,ensure_ascii=False,indent=1,sort_keys=True)+'\n')
after=golden_path.read_bytes();assert before.split(b'\n "params":',1)[1]==after.split(b'\n "params":',1)[1]
assert len(golden['rooms'])==8 and sum(len(v['layouts']) for v in golden['rooms'].values())==64
p=oracle/'README.md';text=p.read_text();needle='  - 2026-10-20 重產(第 22 輪,核心限制與物理衝突分開):'
assert text.count(needle)==1
text=text.replace(needle,'  - 2026-10-23 閱讀 A：`core_limit_witness` 改用既有 FZ120 左上起鋪板長沿 Y 的 I22 延伸段(建構 id 1、端面 1000、矩形 `[1000,3645,4100,3672]`)。固定段端點例外不解除 I22；保非空、四元組矩形綁定、id 不當排序索引與舊三元組拒絕。原 STEP20 當前可施工,逐支幾何與縫 1831/3639 不變；原 8 房 64 排法全部欄位與 bytes 不改。本次只在人工逐欄核對小型觀察後遷移 witness,尚待正式 generator/selftest 驗證。\n'+needle)
p.write_text(text)
p=root/'geometry-core/domain-decoupling/product-architecture.json';manifest=json.loads(p.read_text());changed={}
for row in manifest['exclusions']:
 if row['path'] in ['geometry-core/framing-template/oracle/'+s for s in ['selftest.py','make_golden.py']]:
  oldhash=row['sha256'];newhash=hashlib.sha256((root/row['path']).read_bytes().replace(b'\r\n',b'\n')).hexdigest();row['sha256']=newhash;changed[row['path']]={'before':oldhash,'after':newhash}
assert len(changed)==2,manifest.keys()
p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
out=evidence/'small-observation-2039b477';out.mkdir()
for name in ('receipt.json','stdout.txt','stderr.txt'):shutil.copyfile(prep/'observation-window'/name,out/name)
shutil.copyfile(prep/'observation-small.json',out/'observation.json')
for name in ('make_golden.py','selftest.py'):ast.parse((oracle/name).read_text())
report={'scope':'Source-only reviewed migration from frozen observation, not formal golden regeneration or acceptance','source_sha':source,'observation_sha256':hashlib.sha256((prep/'observation-small.json').read_bytes()).hexdigest(),'old_witness':old,'new_witness':golden['core_limit_witness'],'fz120_current_withdrawn_equal_fields':unchanged,'fz120_only_removed_limit':['CORE_LIMIT_BOUNDARY_END_FREE',3,1000,[0,3648,1000,3675]],'step20_old_witness_timber_rects_labels_and_seams_unchanged':True,'rooms_params_suffix_bytes_unchanged':True,'rooms_count':8,'layouts_count':64,'new_witness_sorted_index_for_constructor_id1':2,'sorted_index1_rect':layout['timbers'][1][1],'fz114_left_x_retained_trace':rows[6]['p182'],'manifest_exclusion_hashes':changed,'formal_generator_selftest_mutations_unrun':True}
(out/'GOLDEN_MIGRATION_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['source_sha','rooms_params_suffix_bytes_unchanged','rooms_count','layouts_count','new_witness_sorted_index_for_constructor_id1','formal_generator_selftest_mutations_unrun']},ensure_ascii=False,indent=2))
