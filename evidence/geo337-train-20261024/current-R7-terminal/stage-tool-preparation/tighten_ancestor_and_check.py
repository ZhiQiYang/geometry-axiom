from pathlib import Path
import ast,difflib,hashlib,json,shutil
D=Path(__file__).resolve().parent
OLD=Path('/workspace/geo323-final-r6-stage-tools-20261024')
H=lambda b:hashlib.sha256(b).hexdigest()
a='81b6c388f8b73e9aaf885b1d948e5f306b77bafd'
b='1449d430d1c4734bb1bc3a9f91f3851c845cc0f3'
original=(D/'FINAL_PINS.json').read_bytes()
assert H(original)=='3a9e0fffdc7673d559ab1c16d45aa655be1554aadad2932d5b9fa98673841a40'
pins=json.loads(original)['files']
for n,p in pins.items():
 raw=(D/n).read_bytes();assert H(raw)==p['sha256'] and len(raw)==p['bytes'],n
hist=D/'history-before-S144-binding';hist.mkdir()
for p in D.iterdir():
 if p.is_file() and p.name!='tighten_ancestor_and_check.py':shutil.copyfile(p,hist/p.name)
for n,count in [('bind_final_request.py',1),('prepare_plan.py',2)]:
 s=(D/n).read_text();assert s.count(a)==count
 (D/n).write_text(s.replace(a,b))
p=json.loads((D/'PLAN.json').read_bytes());assert p['required_ancestor']==a;p['required_ancestor']=b
for row in p['tool_changes']:
 if row['name']=='bind_final_request.py':row['new_sha256']=H((D/row['name']).read_bytes())
(D/'PLAN.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
s=(D/'README.md').read_text();assert s.count(a)==1
s=s.replace(a,b).replace('不能先以S81測完冒成後續來源','必須包含已推送的S144見證修正版，不能先以S81測完冒成後續來源')
(D/'README.md').write_text(s)
for n in ['bind_final_request.py','prepare_plan.py','PLAN.json','README.md']:
 (D/(n+'.S144.diff')).write_text(''.join(difflib.unified_diff((hist/n).read_text().splitlines(True),(D/n).read_text().splitlines(True),fromfile='S81-draft/'+n,tofile='S144-required/'+n)))
(D/'bind_final_request.py.diff').write_text(''.join(difflib.unified_diff((OLD/'bind_final_request.py').read_text().splitlines(True),(D/'bind_final_request.py').read_text().splitlines(True),fromfile='R6/bind_final_request.py',tofile='R7/bind_final_request.py')))
checks=[]
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
r=json.loads((D/'REQUEST.unbound.json').read_bytes());o=json.loads((OLD/'REQUEST.unbound.json').read_bytes())
ck('exact original five stage launcher',(D/'launch_stages.py').read_bytes()==(OLD/'launch_stages.py').read_bytes())
for n in ['base','main','stages','global_locks','original_tools','tool_files','expected_original_samples','expected_original_scenes','expected_profile_points','performance_thresholds_changed','clock_boundaries_changed']:ck('unchanged request '+n,r[n]==o[n])
for n in ['source_checkout','acceptance_out','inner_lock']:ck('new TMP path '+n,Path(r[n]).is_relative_to('/tmp'))
ck('unbound actual final source',r['source_sha'] is None and r['selected_final_source']=='__ROOT_FINAL_R7_SHA__' and (D/'REQUEST.template.json').read_bytes()==(D/'REQUEST.unbound.json').read_bytes())
ck('conservative 138+128 MiB resource sum',r['source_resource_min_free_bytes']==r['full_round_min_free_bytes']==(138+128)*1024*1024 and r['estimated_round_bytes']==138*1024*1024 and r['native_reserve_bytes']==128*1024*1024)
x="fs=os.statvfs('/workspace');report['free_bytes_before']=fs.f_bavail*fs.f_frsize";y="fs=os.statvfs(target.parent);report['free_bytes_before']=fs.f_bavail*fs.f_frsize;report['resource_filesystem']=str(target.parent)"
ck('source prep only real filesystem metadata change',(OLD/'prepare_source.py').read_text().replace(x,y)==(D/'prepare_source.py').read_text())
ck('binder only required ancestor change',(OLD/'bind_final_request.py').read_text().replace('df66452e7a514032453bea93b8b18ab74d7b1457',b)==(D/'bind_final_request.py').read_text())
s=(D/'start_five.py').read_text()
for x in ['os.statvfs(resource_root)','destination.is_relative_to(resource_root)','destination.parent.stat().st_dev==resource_root.stat().st_dev',"free>=request['full_round_min_free_bytes']","'--stage','five'","request['source_sha']==S"]:ck('real outer guard '+x,x in s)
for n,p in r['tool_files'].items():
 raw=(Path(r['original_tools'])/n).read_bytes();ck('unchanged v5 '+n,H(raw)==p['sha256'] and len(raw)==p['bytes'])
for n in ['prepare_plan.py','prepare_source.py','launch_stages.py','bind_final_request.py','start_five.py']:
 ast.parse((D/n).read_text());ck('AST '+n,True)
ck('no binding/materialization/formal run',not any((D/n).exists() for n in ['binding','preparation','outer-five','launch-five']) and not Path(r['source_checkout']).exists() and not Path(r['acceptance_out']).exists())
ck('new required ancestor exact S144',p is not None and json.loads((D/'PLAN.json').read_bytes())['required_ancestor']==b)
ck('original S81 frozen draft preserved',H((hist/'FINAL_PINS.json').read_bytes())=='3a9e0fffdc7673d559ab1c16d45aa655be1554aadad2932d5b9fa98673841a40')
ck('binder delta precisely one S81 to S144',(hist/'bind_final_request.py').read_text().replace(a,b)==(D/'bind_final_request.py').read_text())
ck('prepare generator delta precisely two S81 to S144',(hist/'prepare_plan.py').read_text().replace(a,b)==(D/'prepare_plan.py').read_text())
ck('unbound request retained bytewise',(hist/'REQUEST.unbound.json').read_bytes()==(D/'REQUEST.unbound.json').read_bytes())
report={'checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'C_run':False,'formal_run':False,'scope':'Pure tool-byte/AST/contracts only; S144 publication is owner and independent peer evidence, not reproduced as C execution here.'}
(D/'STATIC_SELF_CHECK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
names=list(pins)+['tighten_ancestor_and_check.py']
new={'files':{n:{'bytes':len((D/n).read_bytes()),'sha256':H((D/n).read_bytes())} for n in names}}
(D/'FINAL_PINS.json').write_text(json.dumps(new,indent=2)+'\n')
print(json.dumps({'checks':report['passed'],'failed':report['failed'],'required_ancestor':b,'FINAL_PINS_sha256':H((D/'FINAL_PINS.json').read_bytes()),'C_run':False,'formal_run':False}))
